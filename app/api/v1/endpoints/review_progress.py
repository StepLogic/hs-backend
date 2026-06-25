from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_db

router = APIRouter()


@router.post("/", response_model=schemas.ReviewProgressResponse, status_code=201)
def create_review_progress(
    *, db: Session = Depends(get_db), progress_in: schemas.ReviewProgressCreate
) -> models.ReviewProgress:
    return crud.upsert_review_progress(
        db,
        student_id=progress_in.student_id,
        review_id=progress_in.review_id,
        score=progress_in.score,
        completed=progress_in.completed,
    )


@router.get("/", response_model=list[schemas.ReviewProgressResponse])
def read_review_progress(
    db: Session = Depends(get_db),
    student_id: str = Query(...),
) -> list[models.ReviewProgress]:
    return crud.get_review_progress(db, student_id=student_id)
