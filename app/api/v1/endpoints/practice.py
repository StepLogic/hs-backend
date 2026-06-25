from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_db, get_current_user, get_current_user_optional
from app.srs import score_to_quality, update_mastery

router = APIRouter()


def _difficulty_for_score(score: int) -> models.Difficulty:
    if score < 40:
        return models.Difficulty.EASY
    elif score < 75:
        return models.Difficulty.MEDIUM
    return models.Difficulty.HARD


@router.get("/next", response_model=list[schemas.QuestionResponse])
def next_practice(
    student_id: str = Query(...),
    subject: str = Query(...),
    grade_level: int = Query(...),
    lesson_id: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> list[models.Question]:
    # Build skill filter
    target_skills = None
    if lesson_id:
        lesson = crud.get_lesson(db, lesson_id)
        if lesson:
            target_skills = lesson.skills

    # Ensure skill mastery rows exist for the subject
    existing_skills = {
        sm.skill for sm in crud.get_skill_masteries_by_student(db, student_id, subject)
    }
    taxonomy = crud.get_skill_taxonomies(db, subject=subject)
    for skill_row in taxonomy:
        if skill_row.skill not in existing_skills:
            crud.create_or_update_skill_mastery(
                db,
                schemas.SkillMasteryCreate(
                    student_id=student_id,
                    subject=models.Subject(subject),
                    skill=skill_row.skill,
                    due_date=date.today(),
                ),
            )
        existing_skills.add(skill_row.skill)

    # Select skills to practice
    mastery_rows = crud.get_skill_masteries_by_student(db, student_id, subject)
    if target_skills:
        mastery_rows = [sm for sm in mastery_rows if sm.skill in target_skills]

    # Rank: overdue or weak skills first
    today = date.today()
    ranked = []
    for sm in mastery_rows:
        overdue_days = max(0, (today - sm.due_date).days)
        rank = (100 - sm.mastery_score) + (overdue_days * 5)
        if sm.repetitions == 0:
            rank += 200  # Prioritize never-practiced
        ranked.append((rank, sm))

    ranked.sort(key=lambda x: -x[0])
    chosen_skills = [sm.skill for _, sm in ranked[:limit]]

    # Fetch questions
    result = []
    answered_recently = set()
    recent_answers = (
        db.query(models.UserAnswer)
        .filter(models.UserAnswer.test_result_id.in_(
            db.query(models.TestResult.id).filter(models.TestResult.student_id == student_id)
        ))
        .order_by(models.UserAnswer.id.desc())
        .limit(50)
        .all()
    )
    for ua in recent_answers:
        answered_recently.add(ua.question_id)

    for skill in chosen_skills:
        sm = next((sm for sm in mastery_rows if sm.skill == skill), None)
        difficulty = _difficulty_for_score(sm.mastery_score) if sm else models.Difficulty.MEDIUM
        q = db.query(models.Question).filter(
            models.Question.subject == subject,
            models.Question.skill == skill,
            models.Question.grade_level.between(grade_level - 1, grade_level + 1),
            models.Question.difficulty == difficulty,
            models.Question.review_status == models.ReviewStatus.PUBLISHED,
        )
        if answered_recently:
            q = q.filter(~models.Question.id.in_(list(answered_recently)))
        q = q.first()
        if q and q not in result:
            result.append(q)
        if len(result) >= limit:
            break

    return result


@router.post("/submit", response_model=schemas.PracticeSubmitResponse)
def submit_practice(
    *, db: Session = Depends(get_db), payload: schemas.PracticeSubmit
) -> dict:
    # Write user answers and compute scores
    correct_count = sum(1 for a in payload.answers if a.is_correct)
    total = len(payload.answers)
    score = int((correct_count / total) * 100) if total else 0

    # Determine mastery level from score
    if score >= 90:
        mastery_level = models.MasteryLevel.ADVANCED
    elif score >= 70:
        mastery_level = models.MasteryLevel.PROFICIENT
    elif score >= 50:
        mastery_level = models.MasteryLevel.DEVELOPING
    else:
        mastery_level = models.MasteryLevel.BEGINNER

    # Create TestResult
    test_result_in = schemas.TestResultCreate(
        student_id=payload.student_id,
        subject=payload.subject,
        score=score,
        grade_equivalent=0,  # ponytail: simplified for adaptive practice
        percentile=0,
        correct_count=correct_count,
        total_questions=total,
        skill_breakdown={},
        mastery_level=mastery_level,
    )
    test_result = crud.create_test_result(db, test_result_in)

    # Write UserAnswers and update SkillMastery
    skill_masteries = []
    subject_val = payload.subject.value if hasattr(payload.subject, "value") else payload.subject
    for ans in payload.answers:
        ua = schemas.UserAnswerCreate(
            test_result_id=test_result.id,
            question_id=ans.question_id,
            answer=ans.answer,
            is_correct=ans.is_correct,
            time_spent=ans.time_spent,
        )
        crud.create_user_answer(db, ua)

        q = crud.get_question(db, ans.question_id)
        if not q:
            continue
        sm = crud.get_skill_mastery_by_student_skill(
            db, payload.student_id, subject_val, q.skill
        )
        if not sm:
            sm = crud.create_or_update_skill_mastery(
                db,
                schemas.SkillMasteryCreate(
                    student_id=payload.student_id,
                    subject=payload.subject,
                    skill=q.skill,
                    due_date=date.today(),
                ),
            )
        quality = score_to_quality(ans.is_correct, ans.time_spent, q.difficulty.value if hasattr(q.difficulty, "value") else q.difficulty)
        update_mastery(sm, quality)
        db.commit()
        db.refresh(sm)
        skill_masteries.append(sm)

    # Update lesson progress if lesson_id provided
    lesson_progress = None
    if payload.lesson_id and skill_masteries:
        avg_mastery = int(sum(sm.mastery_score for sm in skill_masteries) / len(skill_masteries))
        progress_status = (
            models.LessonProgressStatus.COMPLETED
            if avg_mastery >= 70
            else models.LessonProgressStatus.IN_PROGRESS
        )
        lesson_progress = crud.create_or_update_lesson_progress(
            db,
            schemas.LessonProgressCreate(
                student_id=payload.student_id,
                lesson_id=payload.lesson_id,
                status=progress_status,
                mastery_score=avg_mastery,
            ),
        )

    return {
        "test_result": test_result,
        "skill_mastery": skill_masteries,
        "lesson_progress": lesson_progress,
    }
