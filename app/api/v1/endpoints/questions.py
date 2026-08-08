from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_db

router = APIRouter()


@router.get("/", response_model=list[schemas.QuestionResponse])
def read_questions(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    subject: Optional[str] = None,
    grade_level: Optional[int] = None,
    skill: Optional[str] = None,
    status: Optional[str] = Query(None),
    lesson_id: Optional[str] = None,
    unit_id: Optional[str] = None,
    course_id: Optional[str] = None,
    is_full_test: Optional[bool] = None,
    unattached: bool = False,
) -> list[models.Question]:
    query = db.query(models.Question)
    if subject is not None:
        query = query.filter(models.Question.subject == subject)
    if grade_level is not None:
        query = query.filter(models.Question.grade_level == grade_level)
    if skill is not None:
        query = query.filter(models.Question.skill == skill)
    if status is not None:
        query = query.filter(models.Question.review_status == status)
    else:
        query = query.filter(models.Question.review_status == models.ReviewStatus.PUBLISHED)
    if lesson_id is not None:
        query = query.filter(models.Question.lesson_id == lesson_id)
    if unit_id is not None:
        query = query.filter(models.Question.unit_id == unit_id)
    if course_id is not None:
        query = query.filter(models.Question.course_id == course_id)
    if is_full_test is not None:
        query = query.filter(models.Question.is_full_test == is_full_test)
    if unattached:
        query = query.filter(models.Question.lesson_id.is_(None))
    return query.offset(skip).limit(limit).all()


@router.get("/detailed")
def read_questions_detailed(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=5000),
) -> list[dict]:
    """Return questions with their associated course/unit/lesson names."""
    questions = db.query(models.Question).offset(skip).limit(limit).all()

    # Build lookup tables
    courses = {c.id: c for c in db.query(models.Course).all()}
    units = {u.id: u for u in db.query(models.Unit).all()}
    lessons = {l.id: l for l in db.query(models.Lesson).all()}

    result = []
    for q in questions:
        result.append({
            "id": q.id,
            "subject": q.subject.value if q.subject else None,
            "grade_level": q.grade_level,
            "question_type": q.question_type.value if q.question_type else None,
            "prompt": q.prompt,
            "context": q.context,
            "options": q.options,
            "correct_answer": q.correct_answer,
            "skill": q.skill,
            "explanation": q.explanation,
            "hint": q.hint,
            "review_status": q.review_status.value if q.review_status else None,
            "difficulty": q.difficulty.value if q.difficulty else None,
            "source_test_id": q.source_test_id,
            "lesson_id": q.lesson_id,
            "unit_id": q.unit_id,
            "course_id": q.course_id,
            "is_full_test": q.is_full_test,
            "course_title": courses.get(q.course_id).title if q.course_id and q.course_id in courses else None,
            "unit_title": units.get(q.unit_id).title if q.unit_id and q.unit_id in units else None,
            "lesson_title": lessons.get(q.lesson_id).title if q.lesson_id and q.lesson_id in lessons else None,
        })
    return result
@router.get("/source-tests")
def read_source_tests(db: Session = Depends(get_db)) -> list[str]:
    """Return distinct non-null source_test_id values from questions."""
    rows = db.query(models.Question.source_test_id).filter(
        models.Question.source_test_id.isnot(None)
    ).distinct().order_by(models.Question.source_test_id).all()
    return [row[0] for row in rows]



@router.get("/{question_id}", response_model=schemas.QuestionResponse)
def read_question(question_id: str, db: Session = Depends(get_db)) -> models.Question:
    question = crud.get_question(db, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return question


@router.post("/", response_model=schemas.QuestionResponse, status_code=201)
def create_question(
    *, db: Session = Depends(get_db), question_in: schemas.QuestionCreate
) -> models.Question:
    return crud.create_question(db, question_in)


@router.put("/{question_id}", response_model=schemas.QuestionResponse)
def update_question(
    *,
    question_id: str,
    db: Session = Depends(get_db),
    question_in: schemas.QuestionUpdate,
) -> models.Question:
    question = crud.update_question(db, question_id, question_in)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return question


@router.delete("/{question_id}")
def delete_question(
    question_id: str, db: Session = Depends(get_db)
) -> dict[str, bool]:
    success = crud.delete_question(db, question_id)
    if not success:
        raise HTTPException(status_code=404, detail="Question not found")
    return {"ok": True}
