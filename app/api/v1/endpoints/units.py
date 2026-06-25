from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_db

router = APIRouter()


@router.get("/course/{course_id}", response_model=list[schemas.UnitResponse])
def read_units_by_course(course_id: str, db: Session = Depends(get_db)) -> list[models.Unit]:
    return crud.get_units_by_course(db, course_id)


@router.get("/{unit_id}", response_model=schemas.UnitResponse)
def read_unit(unit_id: str, db: Session = Depends(get_db)) -> models.Unit:
    unit = crud.get_unit(db, unit_id)
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    return unit


@router.post("/", response_model=schemas.UnitResponse, status_code=201)
def create_unit(
    *, db: Session = Depends(get_db), unit_in: schemas.UnitCreate
) -> models.Unit:
    return crud.create_unit(db, unit_in)


@router.put("/{unit_id}", response_model=schemas.UnitResponse)
def update_unit(
    *, unit_id: str, db: Session = Depends(get_db), unit_in: schemas.UnitUpdate
) -> models.Unit:
    unit = crud.update_unit(db, unit_id, unit_in)
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    return unit


@router.delete("/{unit_id}")
def delete_unit(unit_id: str, db: Session = Depends(get_db)) -> dict[str, bool]:
    success = crud.delete_unit(db, unit_id)
    if not success:
        raise HTTPException(status_code=404, detail="Unit not found")
    return {"ok": True}
