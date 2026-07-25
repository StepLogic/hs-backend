import secrets
import urllib.parse
from typing import Optional

import requests
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
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


@router.post("/create-user", response_model=schemas.UserResponse, status_code=201)
def create_user_admin(
    *,
    db: Session = Depends(get_db),
    user_in: schemas.UserCreate,
) -> models.User:
    existing = crud.get_user_by_email(db, user_in.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    password_hash = hash_password(user_in.password)
    user = crud.create_user(db, user_in, password_hash)
    if user.role == models.Role.STUDENT:
        student = models.Student(
            name=user.name or user.email.split("@")[0],
            grade_level=1,
            owner_user_id=user.id,
        )
        db.add(student)
        db.commit()
    return user


@router.post("/login", response_model=schemas.Token)
def login(
    *, db: Session = Depends(get_db), credentials: schemas.UserLogin
) -> dict:
    user = crud.get_user_by_email(db, credentials.email)

    # 1. Try backend users table first
    if user and user.password_hash and verify_password(credentials.password, user.password_hash):
        token = create_access_token(str(user.id), user.role.value)
        return {
            "access_token": token,
            "token_type": "bearer",
            "role": user.role,
            "user_id": user.id,
        }

    # 2. Fall back to legacy Better Auth tables (for users created before backend auth)
    from sqlalchemy import text as sa_text
    from sqlalchemy.exc import ProgrammingError
    try:
        ba_user = db.execute(
            sa_text('SELECT id, email FROM "user" WHERE email = :email LIMIT 1'),
            {"email": credentials.email},
        ).mappings().fetchone()

        if ba_user:
            ba_account = db.execute(
                sa_text('SELECT password FROM account WHERE "userId" = :user_id AND "providerId" = \'credential\' LIMIT 1'),
                {"user_id": ba_user["id"]},
            ).mappings().fetchone()

            if ba_account and ba_account["password"] and verify_password(credentials.password, ba_account["password"]):
                # Sync to backend users table if missing or empty
                if not user:
                    user = models.User(
                        email=ba_user["email"],
                        name=ba_user["email"].split("@")[0],
                        password_hash=hash_password(credentials.password),
                        role=models.Role.STUDENT,
                    )
                    db.add(user)
                    db.commit()
                    db.refresh(user)
                    student = models.Student(
                        name=ba_user["email"].split("@")[0],
                        grade_level=1,
                        owner_user_id=user.id,
                    )
                    db.add(student)
                    db.commit()
                elif not user.password_hash:
                    user.password_hash = hash_password(credentials.password)
                    db.commit()

                token = create_access_token(str(user.id), user.role.value)
                return {
                    "access_token": token,
                    "token_type": "bearer",
                    "role": user.role,
                    "user_id": user.id,
                }
    except ProgrammingError:
        pass  # Legacy tables don't exist; fall through to invalid credentials

    raise HTTPException(status_code=401, detail="Invalid credentials")


@router.get("/me", response_model=schemas.UserResponse)
def me(current_user: models.User = Depends(get_current_user)) -> models.User:
    return current_user


# ── Google OAuth ───────────────────────────────────────────────────────

@router.get("/google")
def google_auth() -> dict:
    """Initiate Google OAuth sign-in."""
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=503, detail="Google OAuth not configured")

    state = secrets.token_urlsafe(32)
    redirect_uri = f"{settings.FRONTEND_URL.rstrip('/')}/api/v1/auth/google/callback"

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
    return {"url": url}


@router.get("/google/callback")
def google_callback(
    request: Request,
    code: str,
    state: Optional[str] = None,
    db: Session = Depends(get_db),
) -> dict:
    """Handle Google OAuth callback and return JWT token."""
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=503, detail="Google OAuth not configured")

    # Exchange code for tokens
    redirect_uri = f"{settings.FRONTEND_URL.rstrip('/')}/api/v1/auth/google/callback"
    token_resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        },
        timeout=30,
    )
    if not token_resp.ok:
        raise HTTPException(status_code=400, detail="Failed to exchange Google code")

    tokens = token_resp.json()
    id_token = tokens.get("id_token")
    if not id_token:
        raise HTTPException(status_code=400, detail="No ID token from Google")

    # Validate ID token with Google
    google_user_resp = requests.get(
        "https://oauth2.googleapis.com/tokeninfo",
        params={"id_token": id_token},
        timeout=30,
    )
    if not google_user_resp.ok:
        raise HTTPException(status_code=400, detail="Invalid Google token")

    google_user = google_user_resp.json()
    email = google_user.get("email")
    name = google_user.get("name") or email.split("@")[0]
    if not email:
        raise HTTPException(status_code=400, detail="No email from Google")

    # Find or create user
    user = crud.get_user_by_email(db, email)
    if not user:
        user = models.User(
            email=email,
            password_hash="",
            role=models.Role.STUDENT,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        # Auto-create student profile
        student = models.Student(
            name=name,
            grade_level=1,
            owner_user_id=user.id,
        )
        db.add(student)
        db.commit()

    token = create_access_token(str(user.id), user.role.value)
    # Redirect to frontend with token in URL hash for client-side extraction
    redirect_url = f"{settings.FRONTEND_URL.rstrip('/')}/login#token={token}"
    return RedirectResponse(url=redirect_url)
