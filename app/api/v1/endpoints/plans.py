from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_db, get_current_user, owned_student

router = APIRouter()


@router.post("", response_model=schemas.StudyPlanResponse, status_code=201)
def create_plan(
    *, db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user), plan_in: schemas.StudyPlanCreate
) -> models.StudyPlan:
    owned_student(db, plan_in.student_id, current_user)
    return crud.create_study_plan(db, plan_in)


@router.get("/student/{student_id}", response_model=list[schemas.StudyPlanResponse])
def read_plans_by_student(
    student_id: str, db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> list[models.StudyPlan]:
    owned_student(db, student_id, current_user)
    return crud.get_study_plans_by_student(db, student_id)


@router.get("/{plan_id}", response_model=schemas.StudyPlanResponse)
def read_plan(
    plan_id: str, db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.StudyPlan:
    plan = crud.get_study_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    owned_student(db, plan.student_id, current_user)
    return plan


@router.put("/{plan_id}/items/{item_id}", response_model=schemas.StudyPlanItemResponse)
def update_plan_item(
    plan_id: str,
    item_id: str,
    item_update: schemas.StudyPlanItemUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.StudyPlanItem:
    plan = db.query(models.StudyPlan).filter(models.StudyPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    owned_student(db, plan.student_id, current_user)
    item = crud.update_study_plan_item(db, plan_id, item_id, item_update)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.post("/generate", response_model=schemas.StudyPlanResponse, status_code=201)
def generate_plan(
    *, db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user), req: schemas.PlanGenerateRequest
) -> models.StudyPlan:
    owned_student(db, req.student_id, current_user)
    plan = crud.generate_study_plan(
        db, req.student_id, req.target_exam, req.target_exam_date
    )
    if not plan:
        raise HTTPException(status_code=400, detail="Could not generate plan")
    return plan
