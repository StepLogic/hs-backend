from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_db, get_current_user

router = APIRouter()


@router.post("/courses/{course_id}/personalized", response_model=schemas.PersonalizedCourseResponse, status_code=201)
def generate_personalized_course(
    course_id: str,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.PersonalizedCourse:
    """Generate a personalized course containing only units matching weak tags."""
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    weak_tags = set(payload.get("weak_tags", []))
    if not weak_tags:
        raise HTTPException(status_code=400, detail="weak_tags is required")

    # Find units whose description (tag) matches weak tags
    units = db.query(models.Unit).filter(models.Unit.course_id == course_id).all()
    matching_unit_ids = [u.id for u in units if u.description in weak_tags]

    if not matching_unit_ids:
        raise HTTPException(status_code=400, detail="No units match the provided weak tags")

    # Check for existing personalized course
    existing = crud.get_personalized_course(db, payload["student_id"], course_id)
    if existing:
        # Update existing draft
        updated = crud.update_personalized_course_units(db, existing.id, matching_unit_ids)
        return updated

    return crud.create_personalized_course(
        db, payload["student_id"], course_id, matching_unit_ids
    )
