from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_db, require_roles

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
    difficulty: Optional[models.Difficulty] = None,
    source_test_id: Optional[str] = None,
    is_full_test: Optional[bool] = None,
    unattached: bool = False,
    # Practice asks for a fresh draw each round; admin lists keep a stable order.
    shuffle: bool = False,
) -> list[models.Question]:
    query = db.query(models.Question)
    if difficulty is not None:
        query = query.filter(models.Question.difficulty == difficulty)
    if source_test_id is not None:
        # A mock is played in order, module by module.
        query = query.filter(models.Question.source_test_id == source_test_id).order_by(
            models.Question.mock_module, models.Question.mock_position, models.Question.id
        )
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
    # A question belongs to a unit or course by its own columns OR by being attached to
    # one of its lessons: the SAT Math import attached reused bank questions through
    # lesson_questions only, so matching the columns alone missed them.
    if unit_id is not None:
        unit_lessons = select(models.Lesson.id).where(models.Lesson.unit_id == unit_id)
        query = query.filter(or_(
            models.Question.unit_id == unit_id,
            models.Question.lesson_id.in_(unit_lessons),
            models.Question.id.in_(select(models.lesson_questions.c.question_id)
                                   .where(models.lesson_questions.c.lesson_id.in_(unit_lessons))),
        ))
    if course_id is not None:
        course_units = select(models.Unit.id).where(models.Unit.course_id == course_id)
        course_lessons = select(models.Lesson.id).where(models.Lesson.unit_id.in_(course_units))
        query = query.filter(or_(
            models.Question.course_id == course_id,
            models.Question.unit_id.in_(course_units),
            models.Question.lesson_id.in_(course_lessons),
            models.Question.id.in_(select(models.lesson_questions.c.question_id)
                                   .where(models.lesson_questions.c.lesson_id.in_(course_lessons))),
        ))
    if is_full_test is not None:
        query = query.filter(models.Question.is_full_test == is_full_test)
    if unattached:
        query = query.filter(models.Question.lesson_id.is_(None))
    if shuffle:
        # ponytail: ORDER BY random() scans the filtered set; fine at bank sizes in the
        # low thousands, switch to TABLESAMPLE if it grows past that.
        query = query.order_by(func.random())
    return query.offset(skip).limit(limit).all()


@router.get("/detailed")
def read_questions_detailed(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    # High enough for the whole bank (~6,400): the admin page lists every question.
    limit: int = Query(100, ge=1, le=20000),
    _staff: models.User = Depends(require_roles("admin", "teacher")),
) -> list[dict]:
    """Return questions with their associated course/unit/lesson names."""
    questions = db.query(models.Question).order_by(models.Question.id).offset(skip).limit(limit).all()

    # Build lookup tables
    courses = {c.id: c for c in db.query(models.Course).all()}
    units = {u.id: u for u in db.query(models.Unit).all()}
    lessons = {l.id: l for l in db.query(models.Lesson).all()}
    # Every question's lesson links in one query. Reading q.lessons per question ran one
    # query each: ~5,000 round trips, 45 s for the admin page.
    links: dict[str, list[models.Lesson]] = {}
    for question_id, lesson_id in db.execute(
        select(models.lesson_questions.c.question_id, models.lesson_questions.c.lesson_id)
    ):
        if lesson_id in lessons:
            links.setdefault(question_id, []).append(lessons[lesson_id])

    result = []
    for q in questions:
        # Resolve via many-to-many lessons, falling back to direct lesson_id
        q_lessons = links.get(q.id, [])
        if not q_lessons and q.lesson_id and q.lesson_id in lessons:
            q_lessons = [lessons[q.lesson_id]]

        unit_via_lesson = units.get(q_lessons[0].unit_id) if q_lessons else None
        course_via_lesson = courses.get(unit_via_lesson.course_id) if unit_via_lesson else None

        course_id = q.course_id or (unit_via_lesson.course_id if unit_via_lesson else None)
        unit_id = q.unit_id or (q_lessons[0].unit_id if q_lessons else None)

        course_title = courses.get(q.course_id).title if q.course_id and q.course_id in courses else (course_via_lesson.title if course_via_lesson else None)
        unit_title = units.get(q.unit_id).title if q.unit_id and q.unit_id in units else (unit_via_lesson.title if unit_via_lesson else None)
        lesson_title = q_lessons[0].title if q_lessons else None

        result.append({
            "id": q.id,
            "subject": q.subject.value if q.subject else None,
            "grade_level": q.grade_level,
            "question_type": q.question_type.value if q.question_type else None,
            "prompt": q.prompt,
            "context": q.context,
            "options": q.options,
            "pairs": q.pairs,
            "items": q.items,
            "correct_answer": q.correct_answer,
            "skill": q.skill,
            "explanation": q.explanation,
            "hint": q.hint,
            "review_status": q.review_status.value if q.review_status else None,
            "difficulty": q.difficulty.value if q.difficulty else None,
            "source_test_id": q.source_test_id,
            "mock_module": q.mock_module,
            "mock_position": q.mock_position,
            "lesson_id": q.lesson_id,
            "unit_id": unit_id,
            "course_id": course_id,
            "is_full_test": q.is_full_test,
            "course_title": course_title,
            "unit_title": unit_title,
            "lesson_title": lesson_title,
            "lessons": [{"id": l.id, "title": l.title} for l in q_lessons],
        })
    return result

@router.get("/source-tests")
def read_source_tests(db: Session = Depends(get_db)) -> list[dict]:
    """Return distinct source_test_id values with question counts."""
    from sqlalchemy import func
    rows = db.query(
        models.Question.source_test_id,
        func.count(models.Question.id).label("count")
    ).filter(
        models.Question.source_test_id.isnot(None)
    ).group_by(models.Question.source_test_id).order_by(models.Question.source_test_id).all()
    return [{"source_test_id": row[0], "count": row[1]} for row in rows]



@router.get("/{question_id}", response_model=schemas.QuestionResponse)
def read_question(question_id: str, db: Session = Depends(get_db)) -> models.Question:
    question = crud.get_question(db, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return question


@router.post("/", response_model=schemas.QuestionResponse, status_code=201)
def create_question(
    *, db: Session = Depends(get_db),
    _staff: models.User = Depends(require_roles("admin", "teacher")), question_in: schemas.QuestionCreate
) -> models.Question:
    return crud.create_question(db, question_in)


@router.put("/{question_id}", response_model=schemas.QuestionResponse)
def update_question(
    *,
    question_id: str,
    db: Session = Depends(get_db),
    _staff: models.User = Depends(require_roles("admin", "teacher")),
    question_in: schemas.QuestionUpdate,
) -> models.Question:
    question = crud.update_question(db, question_id, question_in)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return question


@router.delete("/{question_id}")
def delete_question(
    question_id: str, db: Session = Depends(get_db),
    _staff: models.User = Depends(require_roles("admin", "teacher"))
) -> dict[str, bool]:
    success = crud.delete_question(db, question_id)
    if not success:
        raise HTTPException(status_code=404, detail="Question not found")
    return {"ok": True}
