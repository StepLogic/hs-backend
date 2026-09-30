from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_db, require_roles

router = APIRouter()


@router.get("/course/{course_id}", response_model=list[schemas.UnitResponse])
def read_units_by_course(course_id: str, db: Session = Depends(get_db)) -> list[models.Unit]:
    return crud.get_units_by_course(db, course_id)


@router.get("/course/{course_id}/outline", response_model=list[schemas.UnitWithLessons])
def read_course_outline(course_id: str, db: Session = Depends(get_db)) -> list[dict]:
    """Every unit with its lessons, in two queries. Pages used to fetch the unit list
    and then each unit's lessons separately: 21 requests for SAT Math, and the SAT
    pages made them one after another."""
    units = crud.get_units_by_course(db, course_id)
    by_unit: dict[str, list[models.Lesson]] = {u.id: [] for u in units}
    for lesson in (
        db.query(models.Lesson)
        .filter(models.Lesson.unit_id.in_(list(by_unit)))
        .order_by(models.Lesson.order_index)
        .all()
    ):
        by_unit[lesson.unit_id].append(lesson)
    return [
        {**schemas.UnitResponse.model_validate(u).model_dump(), "lessons": by_unit[u.id]}
        for u in units
    ]


@router.get("/{unit_id}", response_model=schemas.UnitResponse)
def read_unit(unit_id: str, db: Session = Depends(get_db)) -> models.Unit:
    unit = crud.get_unit(db, unit_id)
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    return unit


@router.post("/", response_model=schemas.UnitResponse, status_code=201)
def create_unit(
    *, db: Session = Depends(get_db),
    _staff: models.User = Depends(require_roles("admin", "teacher")), unit_in: schemas.UnitCreate
) -> models.Unit:
    return crud.create_unit(db, unit_in)


@router.put("/{unit_id}", response_model=schemas.UnitResponse)
def update_unit(
    *, unit_id: str, db: Session = Depends(get_db),
    _staff: models.User = Depends(require_roles("admin", "teacher")), unit_in: schemas.UnitUpdate
) -> models.Unit:
    unit = crud.update_unit(db, unit_id, unit_in)
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    return unit


@router.delete("/{unit_id}")
def delete_unit(unit_id: str, db: Session = Depends(get_db),
    _staff: models.User = Depends(require_roles("admin", "teacher"))) -> dict[str, bool]:
    success = crud.delete_unit(db, unit_id)
    if not success:
        raise HTTPException(status_code=404, detail="Unit not found")
    return {"ok": True}
