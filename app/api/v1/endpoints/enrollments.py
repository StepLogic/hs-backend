from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_current_user, get_db

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


@router.delete("/courses/{course_id}/enrollment")
def unenroll_from_course(
    course_id: str,
    student_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> dict:
    """Unenroll student from course. Deletes personalized course and enrollment."""
    # Verify student exists and belongs to current user
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if str(student.owner_user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to access this student")

    enrollment = (
        db.query(models.Enrollment)
        .filter(
            models.Enrollment.student_id == student_id,
            models.Enrollment.course_id == course_id,
        )
        .first()
    )
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    # Delete personalized course if exists
    pc = (
        db.query(models.PersonalizedCourse)
        .filter(
            models.PersonalizedCourse.student_id == student_id,
            models.PersonalizedCourse.base_course_id == course_id,
        )
        .first()
    )
    if pc:
        db.delete(pc)

    db.delete(enrollment)
    db.commit()
    return {"ok": True}
