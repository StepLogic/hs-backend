from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_db, get_current_user

router = APIRouter()


def _scope_students_query(
    db: Session, current_user: models.User
):
    query = db.query(models.Student)
    if current_user.role == models.Role.STUDENT:
        query = query.filter(models.Student.owner_user_id == current_user.id)
    elif current_user.role == models.Role.PARENT:
        query = query.filter(models.Student.owner_user_id == current_user.id)
    # teacher/admin see all
    return query


@router.get("/", response_model=list[schemas.StudentResponse])
def read_students(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: models.User = Depends(get_current_user),
) -> list[models.Student]:
    return _scope_students_query(db, current_user).offset(skip).limit(limit).all()


@router.get("/{student_id}", response_model=schemas.StudentResponse)
def read_student(
    student_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.Student:
    student = crud.get_student(db, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    if current_user.role in (models.Role.STUDENT, models.Role.PARENT):
        if str(student.owner_user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized")
    return student


@router.post("/", response_model=schemas.StudentResponse, status_code=201)
def create_student(
    *,
    db: Session = Depends(get_db),
    student_in: schemas.StudentCreate,
    current_user: models.User = Depends(get_current_user),
) -> models.Student:
    # Auto-set owner to current user if not provided
    payload = student_in.model_dump()
    payload["owner_user_id"] = str(current_user.id)
    db_student = models.Student(**payload)
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student


@router.put("/{student_id}", response_model=schemas.StudentResponse)
def update_student(
    *,
    student_id: str,
    db: Session = Depends(get_db),
    student_in: schemas.StudentUpdate,
    current_user: models.User = Depends(get_current_user),
) -> models.Student:
    student = crud.get_student(db, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    if current_user.role in (models.Role.STUDENT, models.Role.PARENT):
        if str(student.owner_user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized")
    updated = crud.update_student(db, student_id, student_in)
    if updated is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return updated


@router.delete("/{student_id}")
def delete_student(
    student_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> dict[str, bool]:
    student = crud.get_student(db, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    if current_user.role == models.Role.PARENT:
        if str(student.owner_user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized")
    success = crud.delete_student(db, student_id)
    if not success:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"ok": True}


@router.get("/{student_id}/results", response_model=list[schemas.TestResultResponse])
def read_student_results(
    student_id: str,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: models.User = Depends(get_current_user),
) -> list[models.TestResult]:
    student = crud.get_student(db, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    if current_user.role in (models.Role.STUDENT, models.Role.PARENT):
        if str(student.owner_user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized")
    return crud.get_test_results(db, skip=skip, limit=limit, student_id=student_id)
