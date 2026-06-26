from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import models
from app.api.deps import get_db, get_current_user, require_roles
from app.notifications import send_parent_digest

router = APIRouter()


class DigestPayload(BaseModel):
    parent_email: str
    student_data: list[dict]


@router.post("/digest")
def send_digest(
    payload: DigestPayload,
    current_user = Depends(require_roles("parent", "admin")),
) -> dict:
    result = send_parent_digest(payload.parent_email, payload.student_data)
    return result
