from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, defer

from app import crud, models, schemas
from app.api.deps import get_db, get_current_user, owned_student

router = APIRouter()


@router.get("/path", response_model=list[dict])
def learning_path(
    student_id: str,
    course_id: str,
    db: Session = Depends(get_db),
) -> list[dict]:
    from app.cache import get as cache_get, set as cache_set
    cache_key = f"learning:path:{student_id}:{course_id}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    # Three queries for the whole course. This used to run one lessons query per unit and
    # one or two progress queries per lesson: ~400 round trips for SAT Math's 206 lessons,
    # 8-9 s per call, which practice and the course page both wait on.
    units = crud.get_units_by_course(db, course_id)
    lessons_by_unit: dict[str, list[models.Lesson]] = {u.id: [] for u in units}
    for lesson in (
        db.query(models.Lesson)
        .options(defer(models.Lesson.rating), defer(models.Lesson.review_count))  # unused here
        .filter(models.Lesson.unit_id.in_(list(lessons_by_unit)))
        .order_by(models.Lesson.order_index)
        .all()
    ):
        lessons_by_unit[lesson.unit_id].append(lesson)
    progress_by_lesson = {
        p.lesson_id: p
        for p in db.query(models.LessonProgress).filter(models.LessonProgress.student_id == student_id)
    }
    result = []
    for unit in units:
        lesson_data = []
        for lesson in lessons_by_unit[unit.id]:
            progress = progress_by_lesson.get(lesson.id)
            locked = False
            if lesson.prerequisite_lesson_id:
                prereq_progress = progress_by_lesson.get(lesson.prerequisite_lesson_id)
                if not prereq_progress or prereq_progress.status != models.LessonProgressStatus.COMPLETED:
                    locked = True
            lesson_data.append({
                "id": lesson.id,
                "unit_id": unit.id,
                "title": lesson.title,
                "slug": lesson.slug,
                "order_index": lesson.order_index,
                "duration_min": lesson.duration_min,
                "skills": lesson.skills,
                "prerequisite_lesson_id": lesson.prerequisite_lesson_id,
                "locked": locked,
                "progress": {
                    "status": progress.status.value if progress else "not_started",
                    "mastery_score": progress.mastery_score if progress else 0,
                    "attempts": progress.attempts if progress else 0,
                },
            })
        result.append({
            "id": unit.id,
            "course_id": unit.course_id,
            "title": unit.title,
            "slug": unit.slug,
            "order_index": unit.order_index,
            "description": unit.description,
            "lessons": lesson_data,
        })
    cache_set(cache_key, result, ttl=300)
    return result
@router.post("/progress", response_model=schemas.LessonProgressResponse, status_code=201)
def upsert_progress(
    *, db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user), progress_in: schemas.LessonProgressCreate
) -> models.LessonProgress:
    owned_student(db, progress_in.student_id, current_user)
    from app.cache import delete as cache_delete
    # Invalidate learning path cache for this student
    cache_delete(f"learning:path:{progress_in.student_id}:*")
    return crud.create_or_update_lesson_progress(db, progress_in)

