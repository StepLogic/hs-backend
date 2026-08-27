from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models, schemas
from app.api.deps import get_db, get_current_user_optional, require_roles

router = APIRouter()

STAFF = ("admin", "teacher")


def _is_staff(user: Optional[models.User]) -> bool:
    return user is not None and user.role.value in STAFF


@router.get("/", response_model=list[schemas.TestimonialResponse])
def read_testimonials(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    current_user: Optional[models.User] = Depends(get_current_user_optional),
) -> list[models.Testimonial]:
    """Published quotes for anyone; staff also see unpublished submissions to moderate."""
    query = db.query(models.Testimonial)
    if not _is_staff(current_user):
        query = query.filter(models.Testimonial.published.is_(True))
    return query.order_by(models.Testimonial.created_at.desc()).limit(limit).all()


@router.post("/", response_model=schemas.TestimonialResponse, status_code=201)
def create_testimonial(
    *,
    db: Session = Depends(get_db),
    testimonial_in: schemas.TestimonialCreate,
    current_user: Optional[models.User] = Depends(get_current_user_optional),
) -> models.Testimonial:
    """Open submission. Only staff may publish straight away; everyone else queues."""
    payload = testimonial_in.model_dump()
    payload["name"] = payload["name"].strip() or "Anonymous"
    payload["role"] = payload["role"].strip() or "Parent"
    payload["quote"] = payload["quote"].strip()
    if not _is_staff(current_user):
        payload["published"] = False
    row = models.Testimonial(**payload)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.put("/{testimonial_id}", response_model=schemas.TestimonialResponse)
def update_testimonial(
    *,
    testimonial_id: str,
    db: Session = Depends(get_db),
    testimonial_in: schemas.TestimonialUpdate,
    _staff: models.User = Depends(require_roles(*STAFF)),
) -> models.Testimonial:
    row = db.query(models.Testimonial).filter(models.Testimonial.id == testimonial_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Testimonial not found")
    for field, value in testimonial_in.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{testimonial_id}")
def delete_testimonial(
    testimonial_id: str,
    db: Session = Depends(get_db),
    _staff: models.User = Depends(require_roles(*STAFF)),
) -> dict[str, bool]:
    row = db.query(models.Testimonial).filter(models.Testimonial.id == testimonial_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Testimonial not found")
    db.delete(row)
    db.commit()
    return {"ok": True}
