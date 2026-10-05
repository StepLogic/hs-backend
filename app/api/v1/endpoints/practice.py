import logging
import json
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import ai_service, crud, models, schemas
from app.api.deps import get_db, get_current_user, get_current_user_optional, owned_student as _owned_student
from app.api.v1.endpoints.assessment import answers_match
from app.srs import score_to_quality, update_mastery

logger = logging.getLogger(__name__)
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
    current_user: models.User = Depends(get_current_user),
) -> list[models.Question]:
    _owned_student(db, student_id, current_user)
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


@router.get("/history")
def practice_history(
    student_id: str = Query(...),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> dict:
    """A student's answered questions, newest first. The dashboard and the practice
    history page both call this; it did not exist, so both were empty."""
    _owned_student(db, student_id, current_user)
    base = (
        db.query(models.UserAnswer, models.TestResult.created_at)
        .join(models.TestResult, models.UserAnswer.test_result_id == models.TestResult.id)
        .filter(models.TestResult.student_id == student_id)
    )
    total = base.count()
    rows = (
        base.order_by(models.TestResult.created_at.desc(), models.UserAnswer.id)
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    prompts = dict(
        db.query(models.Question.id, models.Question.prompt)
        .filter(models.Question.id.in_({ua.question_id for ua, _ in rows}))
        .all()
    )
    items = [
        {
            "id": ua.id,
            "question_id": ua.question_id,
            "student_id": student_id,
            "answer": ua.answer if isinstance(ua.answer, str) else json.dumps(ua.answer),
            "is_correct": ua.is_correct,
            "time_spent": ua.time_spent,
            "created_at": created_at.isoformat(),
            "question": {"id": ua.question_id, "prompt": prompts[ua.question_id]}
            if ua.question_id in prompts
            else None,
        }
        for ua, created_at in rows
    ]
    return {"items": items, "total": total, "page": page, "pages": -(-total // size)}


@router.post("/submit", response_model=schemas.PracticeSubmitResponse)
def submit_practice(
    *,
    db: Session = Depends(get_db),
    payload: schemas.PracticeSubmit,
    current_user: models.User = Depends(get_current_user),
) -> dict:
    _owned_student(db, payload.student_id, current_user)
    # Grade against the bank rather than trusting the client's is_correct: the client
    # compared option text to a letter key and marked nearly every right answer wrong.
    for ans in payload.answers:
        q = crud.get_question(db, ans.question_id)
        if q is not None:
            ans.is_correct = answers_match(ans.answer, q.correct_answer)

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
            used_hint=ans.used_hint,
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


@router.post("/ai-next", response_model=schemas.AiNextResponse)
async def ai_next(
    req: schemas.AiNextRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> schemas.AiNextResponse:
    """The AI coach's pick from a shortlist the browser already made. Any failure is a
    502 and the browser keeps its own rule-based pick."""
    _owned_student(db, req.student_id, current_user)
    ids = {t.question_id for t in req.history} | set(req.candidate_ids)
    rows = {q.id: q for q in db.query(models.Question).filter(models.Question.id.in_(ids))}

    def info(qid: str) -> dict:
        q = rows.get(qid)
        diff = q.difficulty.value if q and hasattr(q.difficulty, "value") else "medium"
        return {"id": qid, "skill": q.skill if q else "unknown", "difficulty": diff}

    candidates = [info(c) for c in req.candidate_ids if c in rows]
    if not candidates:
        raise HTTPException(status_code=422, detail="No known candidates")
    history = [{**info(t.question_id), "correct": t.correct} for t in req.history]
    db.close()  # release the pooled connection before the slow AI call
    try:
        pick = await ai_service.choose_next(history, candidates)
    except Exception as e:
        logger.warning("ai-next failed: %s", type(e).__name__)
        raise HTTPException(status_code=502, detail="AI coach unavailable")
    if pick["question_id"] not in {c["id"] for c in candidates}:
        raise HTTPException(status_code=502, detail="AI coach picked outside the shortlist")
    return schemas.AiNextResponse(**pick)
