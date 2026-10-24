import logging
import json
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app import ai_service, crud, models, schemas
from app.api.deps import get_db, get_current_user, get_current_user_optional, owned_student as _owned_student
from app.recording import record_answers

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
        .filter(
            models.TestResult.student_id == student_id,
            or_(models.TestResult.source.is_(None), models.TestResult.source != "assessment"),
        )
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


@router.get("/review", response_model=schemas.ReviewResponse)
def practice_review(
    student_id: str = Query(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> dict:
    """Questions whose latest answer (lesson/drill/review) was wrong at least 2 days ago,
    oldest miss first, capped at 10. `due` is the uncapped count."""
    _owned_student(db, student_id, current_user)
    rows = (
        db.query(models.UserAnswer, models.TestResult.created_at)
        .join(models.TestResult, models.UserAnswer.test_result_id == models.TestResult.id)
        .filter(
            models.TestResult.student_id == student_id,
            models.TestResult.source.in_(("lesson", "drill", "review")),
        )
        .order_by(models.TestResult.created_at, models.UserAnswer.id)
        .all()
    )
    latest = {ua.question_id: (ua, at) for ua, at in rows}  # later rows overwrite earlier
    cutoff = datetime.utcnow() - timedelta(days=2)
    missed = sorted(
        ((at, qid) for qid, (ua, at) in latest.items() if not ua.is_correct and at <= cutoff)
    )
    by_id = {
        q.id: q
        for q in db.query(models.Question).filter(
            models.Question.id.in_([qid for _, qid in missed]),
            models.Question.review_status == models.ReviewStatus.PUBLISHED,
            models.Question.question_type.in_((models.QuestionType.MULTIPLE_CHOICE, models.QuestionType.FILL_IN)),
        ).all()
    }
    due = [by_id[qid] for _, qid in missed if qid in by_id]
    return {"questions": due[:10], "due": len(due)}


@router.post("/submit", response_model=schemas.PracticeSubmitResponse)
def submit_practice(
    *,
    db: Session = Depends(get_db),
    payload: schemas.PracticeSubmit,
    current_user: models.User = Depends(get_current_user),
) -> dict:
    _owned_student(db, payload.student_id, current_user)
    return record_answers(
        db, payload.student_id, payload.subject, payload.answers,
        payload.source, payload.lesson_id,
    )


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
