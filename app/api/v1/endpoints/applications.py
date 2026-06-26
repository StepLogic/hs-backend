from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_db, get_current_user

router = APIRouter()


@router.get("/student/{student_id}", response_model=list[schemas.CollegeApplicationResponse])
def read_applications_by_student(
    student_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> list[models.CollegeApplication]:
    return crud.get_applications_by_student(db, student_id)


@router.post("/", response_model=schemas.CollegeApplicationResponse, status_code=201)
def create_application(
    application_in: schemas.CollegeApplicationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.CollegeApplication:
    return crud.create_application(db, application_in)


@router.put("/{application_id}", response_model=schemas.CollegeApplicationResponse)
def update_application(
    application_id: str,
    application_in: schemas.CollegeApplicationUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.CollegeApplication:
    app = crud.update_application(db, application_id, application_in)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app


@router.put("/{application_id}/status", response_model=schemas.CollegeApplicationResponse)
def update_application_status(
    application_id: str,
    status_in: schemas.CollegeApplicationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.CollegeApplication:
    app = crud.update_application_status(db, application_id, status_in.status)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app


@router.delete("/{application_id}")
def delete_application(
    application_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> dict[str, bool]:
    app = crud.delete_application(db, application_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return {"ok": True}
