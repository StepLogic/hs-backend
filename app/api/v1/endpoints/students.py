from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_db

router = APIRouter()


@router.get("/", response_model=list[schemas.StudentResponse])
def read_students(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> list[models.Student]:
    return crud.get_students(db, skip=skip, limit=limit)


@router.get("/{student_id}", response_model=schemas.StudentResponse)
def read_student(student_id: str, db: Session = Depends(get_db)) -> models.Student:
    student = crud.get_student(db, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.post("/", response_model=schemas.StudentResponse, status_code=201)
def create_student(
    *, db: Session = Depends(get_db), student_in: schemas.StudentCreate
) -> models.Student:
    return crud.create_student(db, student_in)


@router.put("/{student_id}", response_model=schemas.StudentResponse)
def update_student(
    *,
    student_id: str,
    db: Session = Depends(get_db),
    student_in: schemas.StudentUpdate,
) -> models.Student:
    student = crud.update_student(db, student_id, student_in)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.delete("/{student_id}")
def delete_student(
    student_id: str, db: Session = Depends(get_db)
) -> dict[str, bool]:
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
) -> list[models.TestResult]:
    student = crud.get_student(db, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return crud.get_test_results(db, skip=skip, limit=limit, student_id=student_id)
