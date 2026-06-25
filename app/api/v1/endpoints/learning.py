from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_db

router = APIRouter()


@router.get("/path", response_model=list[dict])
def learning_path(
    student_id: str,
    course_id: str,
    db: Session = Depends(get_db),
) -> list[dict]:
    units = crud.get_units_by_course(db, course_id)
    result = []
    for unit in units:
        lessons = crud.get_lessons_by_unit(db, unit.id)
        lesson_data = []
        for lesson in lessons:
            progress = crud.get_lesson_progress_by_student_lesson(db, student_id, lesson.id)
            locked = False
            if lesson.prerequisite_lesson_id:
                prereq_progress = crud.get_lesson_progress_by_student_lesson(
                    db, student_id, lesson.prerequisite_lesson_id
                )
                if not prereq_progress or prereq_progress.status != models.LessonProgressStatus.COMPLETED:
                    locked = True
            lesson_data.append({
                "id": lesson.id,
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
            "title": unit.title,
            "slug": unit.slug,
            "order_index": unit.order_index,
            "description": unit.description,
            "lessons": lesson_data,
        })
    return result


@router.post("/progress", response_model=schemas.LessonProgressResponse, status_code=201)
def upsert_progress(
    *, db: Session = Depends(get_db), progress_in: schemas.LessonProgressCreate
) -> models.LessonProgress:
    return crud.create_or_update_lesson_progress(db, progress_in)
