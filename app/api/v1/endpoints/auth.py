from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_db, get_current_user
from app.config import settings
from app.security import create_access_token, hash_password, verify_password

router = APIRouter()


@router.post("/register", response_model=schemas.Token, status_code=201)
def register(
    *, db: Session = Depends(get_db), user_in: schemas.UserCreate
) -> dict:
    if user_in.role.value in ("teacher", "admin"):
        raise HTTPException(status_code=403, detail="Self-registration not allowed for this role")
    existing = crud.get_user_by_email(db, user_in.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    password_hash = hash_password(user_in.password)
    user = crud.create_user(db, user_in, password_hash)
    # Auto-create student profile for student-role registrations
    if user.role == models.Role.STUDENT:
        student = models.Student(
            name=user.email.split("@")[0],
            grade_level=1,
            owner_user_id=user.id,
        )
        db.add(student)
        db.commit()
    token = create_access_token(str(user.id), user.role.value)
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "user_id": user.id,
    }


@router.post("/login", response_model=schemas.Token)
def login(
    *, db: Session = Depends(get_db), credentials: schemas.UserLogin
) -> dict:
    user = crud.get_user_by_email(db, credentials.email)
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(str(user.id), user.role.value)
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "user_id": user.id,
    }


@router.get("/me", response_model=schemas.UserResponse)
def me(current_user: models.User = Depends(get_current_user)) -> models.User:
    return current_user


@router.get("/session-token")
def get_session_token(
    session_id: str,
    x_internal_secret: Optional[str] = Header(None, alias="X-Internal-Secret"),
    db: Session = Depends(get_db),
) -> dict:
    """Internal endpoint for hs-platform server hooks to resolve a session ID
    to its raw token without querying the DB directly.

    Protected by a shared secret (BETTER_AUTH_SECRET) known only to the
    SvelteKit server and the backend.
    """
    if x_internal_secret != settings.BETTER_AUTH_SECRET or not settings.BETTER_AUTH_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")

    row = db.execute(
        text('SELECT token FROM session WHERE id = :id AND "expiresAt" > NOW()'),
        {"id": session_id},
    ).mappings().fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"token": row["token"]}
