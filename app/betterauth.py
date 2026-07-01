"""Better Auth session validation for cross-service authentication.

hs-platform runs Better Auth (Node.js) and stores sessions in the shared
PostgreSQL database. This module lets hs-backend validate those sessions
directly so protected endpoints can authenticate users without maintaining a
parallel JWT system.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app import models


def get_user_by_betterauth_session(db: Session, token: str) -> Optional[dict]:
    """Validate a raw Better Auth session token and return the user.

    The token is the opaque string stored in Better Auth's ``session.token``
    column (not the signed cookie value).
    """
    if not token:
        return None

    row = db.execute(
        text(
            """
            SELECT s."userId", s."expiresAt",
                   u.id AS user_id, u.name, u.email
            FROM session s
            JOIN "user" u ON s."userId" = u.id
            WHERE s.token = :token
            LIMIT 1
            """
        ),
        {"token": token},
    ).mappings().fetchone()

    if not row:
        return None

    expires_at = row["expiresAt"]
    if expires_at and expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        return None

    return {
        "id": row["userId"],
        "name": row["name"],
        "email": row["email"],
    }


def get_or_create_backend_user(db: Session, betterauth_user: dict) -> models.User:
    """Map a Better Auth user to the backend ``users`` table.

    Looks up by e-mail. If the user does not exist, a new ``STUDENT`` row is
    created with an empty password hash (auth is handled by Better Auth).
    """
    user = (
        db.query(models.User)
        .filter(models.User.email == betterauth_user["email"])
        .first()
    )
    if user:
        return user

    user = models.User(
        email=betterauth_user["email"],
        password_hash="",
        role=models.Role.STUDENT,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
