from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_db, get_current_user

router = APIRouter()

# `name` and `email` live on `users`, everything else on `user_profiles`. The account
# screen saves once, so both endpoints compose the two rows rather than making the
# client orchestrate two calls.
USER_FIELDS = ("name", "email")


def _compose(profile: models.UserProfile, user: models.User) -> schemas.UserProfileResponse:
    out = schemas.UserProfileResponse.model_validate(profile)
    out.name = user.name
    out.email = user.email
    return out


@router.get("/me", response_model=schemas.UserProfileResponse)
def get_profile(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.UserProfileResponse:
    profile = crud.get_user_profile(db, str(current_user.id))
    if not profile:
        profile = crud.create_user_profile(
            db, schemas.UserProfileCreate(user_id=str(current_user.id))
        )
    return _compose(profile, current_user)


@router.put("/me", response_model=schemas.UserProfileResponse)
def update_profile(
    update: schemas.UserProfileUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.UserProfileResponse:
    changes = update.model_dump(exclude_unset=True)
    user_changes = {k: changes.pop(k) for k in USER_FIELDS if k in changes}

    new_email = user_changes.get("email")
    if new_email and new_email != current_user.email:
        if crud.get_user_by_email(db, new_email):
            raise HTTPException(status_code=409, detail="Email already registered")

    profile = crud.update_user_profile(
        db, str(current_user.id), schemas.UserProfileUpdate(**changes)
    )
    if not profile:
        profile = crud.create_user_profile(
            db, schemas.UserProfileCreate(user_id=str(current_user.id), **changes)
        )

    if user_changes:
        for key, value in user_changes.items():
            setattr(current_user, key, value)
        db.commit()
        db.refresh(current_user)

    return _compose(profile, current_user)


@router.get("/leaderboard", response_model=list[schemas.LeaderboardEntry])
def get_leaderboard(
    subject: str | None = None,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> list[dict]:
    return crud.get_leaderboard(db, subject=subject, limit=limit)
