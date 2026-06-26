from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_db

router = APIRouter()


@router.post("/", response_model=schemas.ProgressResponse, status_code=201)
def create_progress(
    *, db: Session = Depends(get_db), progress_in: schemas.ProgressCreate
) -> models.LessonProgress:
    return crud.upsert_lesson_progress(
        db,
        student_id=progress_in.student_id,
        lesson_id=progress_in.lesson_id,
        score=progress_in.score,
        completed=progress_in.completed,
    )


@router.get("/", response_model=list[schemas.ProgressResponse])
def read_progress(
    db: Session = Depends(get_db),
    student_id: str = Query(...),
) -> list[models.LessonProgress]:
    return crud.get_lesson_progress(db, student_id=student_id)