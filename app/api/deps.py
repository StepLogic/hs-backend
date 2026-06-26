from typing import Optional

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from app import models
from app.database import get_db as _get_db
from app.security import decode_access_token

get_db = _get_db

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)


def _extract_token(auth_header: Optional[str]) -> Optional[str]:
    if not auth_header:
        return None
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:]
    return auth_header


def get_current_user(
    auth_header: Optional[str] = Security(api_key_header),
    db: Session = Depends(get_db),
) -> models.User:
    token = _extract_token(auth_header)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_access_token(token)
    if not payload or not payload.get("sub"):
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(models.User).filter(models.User.id == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def get_current_user_optional(
    auth_header: Optional[str] = Security(api_key_header),
    db: Session = Depends(get_db),
) -> Optional[models.User]:
    token = _extract_token(auth_header)
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload or not payload.get("sub"):
        return None
    return db.query(models.User).filter(models.User.id == payload["sub"]).first()


def require_roles(*roles: str):
    def checker(current_user: models.User = Depends(get_current_user)) -> models.User:
        if current_user.role.value not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return checker
