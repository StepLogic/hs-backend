from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_db

router = APIRouter()


@router.get("/", response_model=list[schemas.EnrollmentResponse])
def read_enrollments(
    student_id: str = Query(...),
    db: Session = Depends(get_db),
) -> list[models.Enrollment]:
    return crud.get_enrollments_by_student(db, student_id)


@router.post("/", response_model=schemas.EnrollmentResponse, status_code=201)
def create_enrollment(
    *, db: Session = Depends(get_db), enrollment_in: schemas.EnrollmentCreate
) -> models.Enrollment:
    return crud.create_enrollment(db, enrollment_in)


@router.put("/{enrollment_id}", response_model=schemas.EnrollmentResponse)
def update_enrollment(
    *, enrollment_id: str, db: Session = Depends(get_db), enrollment_in: schemas.EnrollmentUpdate
) -> models.Enrollment:
    enrollment = crud.update_enrollment(db, enrollment_id, enrollment_in)
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    return enrollment
