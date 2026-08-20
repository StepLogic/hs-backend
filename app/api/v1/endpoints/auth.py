import hashlib
import logging
import secrets
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
import requests
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_db, get_current_user
from app.config import settings
from app.security import create_access_token, hash_password, verify_password
from app.notifications import send_password_reset

logger = logging.getLogger(__name__)

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
    from sqlalchemy.exc import OperationalError, ProgrammingError
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
    except (ProgrammingError, OperationalError):
        # Legacy tables don't exist; fall through to invalid credentials. Postgres
        # raises ProgrammingError for a missing relation, SQLite OperationalError —
        # catching only the first turned every failed login into a 500 under SQLite.
        db.rollback()  # the failed statement poisons the session on Postgres

    raise HTTPException(status_code=401, detail="Invalid credentials")


@router.get("/me", response_model=schemas.UserResponse)
def me(current_user: models.User = Depends(get_current_user)) -> models.User:
    return current_user


# ── Password reset ─────────────────────────────────────────────────────

_RESET_TTL_SECONDS = 1800


def _password_fingerprint(password_hash: str) -> str:
    """A non-reversible marker of the *current* password.

    Carried in the reset token and re-checked on confirm, so a token stops working
    the moment the password changes — that makes it single-use without a table."""
    return hashlib.sha256(password_hash.encode()).hexdigest()[:16]


def _issue_reset_token(user: models.User) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": str(user.id),
            "iat": now,
            "exp": now + timedelta(seconds=_RESET_TTL_SECONDS),
            "purpose": "password-reset",
            "pwh": _password_fingerprint(user.password_hash or ""),
        },
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


@router.post("/password-reset/request", status_code=204)
def request_password_reset(
    body: schemas.PasswordResetRequest, db: Session = Depends(get_db)
) -> None:
    # Always 204, whether or not the address exists — a different answer for a
    # registered address turns this into an account-enumeration oracle.
    user = crud.get_user_by_email(db, body.email)
    if user and user.password_hash:
        token = _issue_reset_token(user)
        url = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?token={urllib.parse.quote(token)}"
        result = send_password_reset(user.email, url)
        if not result.get("sent"):
            # Without RESEND_API_KEY nothing is delivered and the flow is untestable.
            # Log the link so local development can follow it; never in production.
            logger.warning("Password reset email not sent (%s)", result.get("reason"))
            if settings.DEBUG:
                logger.warning("Password reset link for %s: %s", user.email, url)


@router.post("/password-reset/confirm", status_code=204)
def confirm_password_reset(
    body: schemas.PasswordResetConfirm, db: Session = Depends(get_db)
) -> None:
    invalid = HTTPException(status_code=400, detail="Reset link is invalid or has expired")
    try:
        claims = jwt.decode(
            body.token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
    except jwt.PyJWTError:
        raise invalid
    if claims.get("purpose") != "password-reset":
        raise invalid

    user = crud.get_user(db, str(claims.get("sub")))
    if not user or not user.password_hash:
        raise invalid
    # Already used, or the password changed by another route since it was issued.
    if not secrets.compare_digest(
        str(claims.get("pwh", "")), _password_fingerprint(user.password_hash)
    ):
        raise invalid

    user.password_hash = hash_password(body.new_password)
    db.commit()

@router.post("/change-password", status_code=204)
def change_password(
    body: schemas.PasswordChange,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    # Google-created accounts get password_hash="" and can never have a password
    # verified against them — bcrypt raises on an empty hash, so answer plainly.
    if not current_user.password_hash:
        raise HTTPException(
            status_code=400, detail="This account signs in with Google and has no password"
        )
    if not verify_password(body.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if body.new_password == body.current_password:
        raise HTTPException(status_code=400, detail="New password must be different")
    current_user.password_hash = hash_password(body.new_password)
    db.commit()


# ── Google OAuth ───────────────────────────────────────────────────────

# The redirect URI must be identical in the authorize request and the token exchange,
# and must point at *this* API — the callback route below lives here, not on the frontend.
def _google_redirect_uri() -> str:
    return f"{settings.BACKEND_URL.rstrip('/')}/api/v1/auth/google/callback"


_STATE_COOKIE = "hs-oauth-state"
_STATE_TTL_SECONDS = 600


def _issue_state() -> str:
    """A short-lived signed token binding the callback to the request that started it."""
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "nonce": secrets.token_urlsafe(16),
            "iat": now,
            "exp": now + timedelta(seconds=_STATE_TTL_SECONDS),
            "purpose": "google-oauth-state",
        },
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def _verify_state(state: Optional[str], cookie_state: Optional[str]) -> None:
    """Reject a callback we did not initiate. This is the CSRF defence in OAuth."""
    if not state or not cookie_state or not secrets.compare_digest(state, cookie_state):
        raise HTTPException(status_code=400, detail="Invalid OAuth state")
    try:
        claims = jwt.decode(state, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")
    if claims.get("purpose") != "google-oauth-state":
        raise HTTPException(status_code=400, detail="Invalid OAuth state")


@router.get("/google")
def google_auth() -> JSONResponse:
    """Initiate Google OAuth sign-in."""
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=503, detail="Google OAuth not configured")

    state = _issue_state()
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": _google_redirect_uri(),
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)

    # The same state goes back in a cookie so the callback can prove it started here.
    response = JSONResponse({"url": url})
    response.set_cookie(
        _STATE_COOKIE,
        state,
        max_age=_STATE_TTL_SECONDS,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        path="/",
    )
    return response


@router.get("/google/callback")
def google_callback(
    request: Request,
    code: str,
    state: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Handle the Google OAuth callback and hand a JWT back to the frontend."""
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=503, detail="Google OAuth not configured")

    _verify_state(state, request.cookies.get(_STATE_COOKIE))

    token_resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": _google_redirect_uri(),
            "grant_type": "authorization_code",
        },
        timeout=30,
    )
    if not token_resp.ok:
        raise HTTPException(status_code=400, detail="Failed to exchange Google code")

    id_token = token_resp.json().get("id_token")
    if not id_token:
        raise HTTPException(status_code=400, detail="No ID token from Google")

    google_user_resp = requests.get(
        "https://oauth2.googleapis.com/tokeninfo",
        params={"id_token": id_token},
        timeout=30,
    )
    if not google_user_resp.ok:
        raise HTTPException(status_code=400, detail="Invalid Google token")

    google_user = google_user_resp.json()

    # tokeninfo says the token is well-formed; it does not say it was minted for *us*.
    # Without this check a token issued to any other Google app would be accepted.
    if google_user.get("aud") != settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=400, detail="Google token was not issued for this app")

    email = google_user.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="No email from Google")

    # An unverified address must never match an existing account — that is account takeover.
    if str(google_user.get("email_verified", "")).lower() not in ("true", "1"):
        raise HTTPException(status_code=400, detail="Google email is not verified")

    name = google_user.get("name") or email.split("@")[0]

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
        db.add(
            models.Student(
                name=name,
                grade_level=1,
                owner_user_id=user.id,
            )
        )
        db.commit()

    token = create_access_token(str(user.id), user.role.value)
    # The fragment is never sent to a server, so the token does not leak via Referer or logs.
    redirect_url = f"{settings.FRONTEND_URL.rstrip('/')}/login#token={token}"
    response = RedirectResponse(url=redirect_url)
    response.delete_cookie(_STATE_COOKIE, path="/")
    return response
