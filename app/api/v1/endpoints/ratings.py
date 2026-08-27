from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, schemas
from app.api.deps import get_db

router = APIRouter()


def _summary(db: Session, target_type: str, target_id: str, student_id: Optional[str]) -> dict:
    average, count = (
        db.query(func.avg(models.Rating.stars), func.count(models.Rating.id))
        .filter(
            models.Rating.target_type == target_type,
            models.Rating.target_id == target_id,
        )
        .one()
    )
    mine = None
    if student_id:
        row = (
            db.query(models.Rating.stars)
            .filter(
                models.Rating.student_id == student_id,
                models.Rating.target_type == target_type,
                models.Rating.target_id == target_id,
            )
            .first()
        )
        mine = row[0] if row else None
    return {
        "target_type": target_type,
        "target_id": target_id,
        "average": round(float(average), 2) if average is not None else None,
        "count": count,
        "my_stars": mine,
    }


@router.get("/", response_model=schemas.RatingSummary)
def read_rating(
    target_type: str = Query(..., pattern="^(course|lesson)$"),
    target_id: str = Query(...),
    student_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> dict:
    return _summary(db, target_type, target_id, student_id)


@router.post("/", response_model=schemas.RatingSummary)
def upsert_rating(
    *,
    db: Session = Depends(get_db),
    rating_in: schemas.RatingCreate,
) -> dict:
    """One rating per student per target — rating again replaces the old score."""
    if db.query(models.Student).filter(models.Student.id == rating_in.student_id).first() is None:
        raise HTTPException(status_code=404, detail="Student not found")

    target = models.Course if rating_in.target_type == "course" else models.Lesson
    if db.query(target).filter(target.id == rating_in.target_id).first() is None:
        raise HTTPException(status_code=404, detail=f"{rating_in.target_type.title()} not found")

    existing = (
        db.query(models.Rating)
        .filter(
            models.Rating.student_id == rating_in.student_id,
            models.Rating.target_type == rating_in.target_type,
            models.Rating.target_id == rating_in.target_id,
        )
        .first()
    )
    if existing:
        existing.stars = rating_in.stars
    else:
        db.add(models.Rating(**rating_in.model_dump()))
    db.commit()
    return _summary(db, rating_in.target_type, rating_in.target_id, rating_in.student_id)
