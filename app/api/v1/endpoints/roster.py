from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_db, get_current_user, require_roles

router = APIRouter()


class RosterAssignmentCreate(BaseModel):
    student_id: str
    teacher_id: str
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_db, get_current_user, require_roles

router = APIRouter()




@router.post("/assign", status_code=201)
def assign_student(
    *,
    db: Session = Depends(get_db),
    _admin: models.User = require_roles("admin"),
    payload: RosterAssignmentCreate,
) -> dict:
    # Simple v1: store teacher_id on student.owner_user_id if not already owned
    student = crud.get_student(db, payload.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    student.owner_user_id = payload.teacher_id
    db.commit()
    return {"ok": True}
@router.get("/teacher", response_model=list[schemas.StudentResponse])
def get_teacher_roster(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> list[models.Student]:
    if current_user.role not in (models.Role.TEACHER, models.Role.ADMIN):
        raise HTTPException(status_code=403, detail="Teacher access only")
    return db.query(models.Student).filter(models.Student.owner_user_id == current_user.id).all()
