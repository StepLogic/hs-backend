from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_db, require_roles

router = APIRouter()


@router.get("/search", response_model=list[schemas.CollegeResponse])
def search_colleges(
    db: Session = Depends(get_db),
    q: Optional[str] = None,
    sat_min: Optional[int] = Query(None, ge=400, le=1600),
    sat_max: Optional[int] = Query(None, ge=400, le=1600),
    major: Optional[str] = None,
    tags: Optional[list[str]] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> list[models.College]:
    return crud.search_colleges(
        db, q=q, sat_min=sat_min, sat_max=sat_max, major=major, tags=tags,
        skip=skip, limit=limit,
    )


@router.get("/{college_id}", response_model=schemas.CollegeResponse)
def read_college(college_id: str, db: Session = Depends(get_db)) -> models.College:
    college = crud.get_college(db, college_id)
    if college is None:
        raise HTTPException(status_code=404, detail="College not found")
    return college


@router.post("/", response_model=schemas.CollegeResponse, status_code=201)
def create_college(
    *,
    db: Session = Depends(get_db),
    college_in: schemas.CollegeCreate,
    _admin = Depends(require_roles("admin", "parent")),
) -> models.College:
    return crud.create_college(db, college_in)
