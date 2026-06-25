from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_db, get_current_user

router = APIRouter()


@router.get("/me", response_model=schemas.UserProfileResponse)
def get_profile(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> models.UserProfile:
    profile = crud.get_user_profile(db, str(current_user.id))
    if not profile:
        profile = crud.create_user_profile(
            db, schemas.UserProfileCreate(user_id=str(current_user.id))
        )
    return profile


@router.put("/me", response_model=schemas.UserProfileResponse)
def update_profile(
    update: schemas.UserProfileUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> models.UserProfile:
    profile = crud.update_user_profile(db, str(current_user.id), update)
    if not profile:
        profile = crud.create_user_profile(
            db, schemas.UserProfileCreate(user_id=str(current_user.id), **update.model_dump(exclude_unset=True))
        )
    return profile
