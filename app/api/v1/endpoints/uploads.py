import os
import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.storage import generate_upload_url
from app.b2 import PUBLIC_BASE
from app.api.deps import get_current_user
from app import models

router = APIRouter()


@router.post("/presign")
def presign_upload(
    filename: str,
    content_type: str,
    current_user: models.User = Depends(get_current_user),
):
    # ponytail: image-only guard at the trust boundary
    if not content_type.startswith("image/"):
        raise HTTPException(400, "Only image uploads are allowed")
    # uuid-based key: avoids filename sanitization/collision concerns entirely
    ext = os.path.splitext(filename)[1]
    key = f"uploads/{current_user.id}/{uuid.uuid4().hex}{ext}"
    return {
        "upload_url": generate_upload_url(key, content_type),
        "public_url": f"{PUBLIC_BASE}/{key}",
    }