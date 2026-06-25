from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_db, require_roles

router = APIRouter()


@router.get("/", response_model=list[schemas.SkillTaxonomyResponse])
def read_skills(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    subject: Optional[str] = None,
) -> list[models.SkillTaxonomy]:
    return crud.get_skill_taxonomies(db, skip=skip, limit=limit, subject=subject)


@router.post("/", response_model=schemas.SkillTaxonomyResponse, status_code=201)
def create_skill(
    *, db: Session = Depends(get_db), skill_in: schemas.SkillTaxonomyCreate
) -> models.SkillTaxonomy:
    return crud.create_skill_taxonomy(db, skill_in)


@router.delete("/{skill_id}")
def delete_skill(
    skill_id: str, db: Session = Depends(get_db)
) -> dict[str, bool]:
    success = crud.delete_skill_taxonomy(db, skill_id)
    if not success:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"ok": True}
