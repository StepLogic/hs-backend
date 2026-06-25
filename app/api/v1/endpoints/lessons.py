from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_db

router = APIRouter()


@router.get("/unit/{unit_id}", response_model=list[schemas.LessonResponse])
def read_lessons_by_unit(unit_id: str, db: Session = Depends(get_db)) -> list[models.Lesson]:
    return (
        db.query(models.Lesson)
        .filter(models.Lesson.unit_id == unit_id)
        .filter(models.Lesson.review_status == models.ReviewStatus.PUBLISHED)
        .order_by(models.Lesson.order_index)
        .all()
    )


@router.get("/{lesson_id}", response_model=schemas.LessonResponse)
def read_lesson(lesson_id: str, db: Session = Depends(get_db)) -> models.Lesson:
    lesson = crud.get_lesson(db, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson


@router.post("/", response_model=schemas.LessonResponse, status_code=201)
def create_lesson(
    *, db: Session = Depends(get_db), lesson_in: schemas.LessonCreate
) -> models.Lesson:
    return crud.create_lesson(db, lesson_in)


@router.put("/{lesson_id}", response_model=schemas.LessonResponse)
def update_lesson(
    *, lesson_id: str, db: Session = Depends(get_db), lesson_in: schemas.LessonUpdate
) -> models.Lesson:
    lesson = crud.update_lesson(db, lesson_id, lesson_in)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson


@router.delete("/{lesson_id}")
def delete_lesson(lesson_id: str, db: Session = Depends(get_db)) -> dict[str, bool]:
    success = crud.delete_lesson(db, lesson_id)
    if not success:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return {"ok": True}
