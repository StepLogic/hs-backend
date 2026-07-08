from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_db, get_current_user

router = APIRouter()


@router.get("/{course_id}/certificate/eligibility", response_model=schemas.EligibilityResponse)
def certificate_eligibility(
    course_id: str,
    student_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> schemas.EligibilityResponse:
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if str(student.owner_user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        result = crud.get_certificate_eligibility(db, student_id, course_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return schemas.EligibilityResponse(**result)


@router.post("/{course_id}/certificate/claim", response_model=schemas.ClaimResponse)
def claim_certificate(
    course_id: str,
    student_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> schemas.ClaimResponse:
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if str(student.owner_user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        cert = crud.claim_certificate(db, student_id, course_id)
    except ValueError as e:
        msg = str(e).lower()
        if "already claimed" in msg:
            raise HTTPException(status_code=409, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))

    course = crud.get_course(db, course_id)
    assert course is not None

    return schemas.ClaimResponse(
        certificate_id=cert.id,
        student_name=student.name,
        course_title=course.title,
        earned_at=cert.earned_at,
        final_score=cert.final_score,
        certificate_hash=cert.certificate_hash,
    )


list_router = APIRouter()


@list_router.get("/", response_model=list[schemas.CertificateResponse])
def list_my_certificates(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> list[models.Certificate]:
    # Find all students owned by current user
    students = db.query(models.Student).filter(models.Student.owner_user_id == str(current_user.id)).all()
    if not students:
        return []

    all_certs: list[models.Certificate] = []
    for student in students:
        all_certs.extend(crud.get_certificates_by_student(db, student.id))
    return all_certs


@list_router.get("/{certificate_id}", response_model=schemas.CertificateResponse)
def get_certificate(
    certificate_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.Certificate:
    cert = crud.get_certificate_by_id(db, certificate_id)
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")

    student = db.query(models.Student).filter(models.Student.id == cert.student_id).first()
    if not student or str(student.owner_user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")

    return cert
