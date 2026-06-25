from fastapi import APIRouter, Depends, HTTPException

from app.storage import generate_upload_url, generate_download_url
from app.api.deps import get_current_user
from app import models

router = APIRouter()


@router.post("/presign")
def presign_upload(
    filename: str,
    content_type: str,
    current_user: models.User = Depends(get_current_user),
):
    if "/" in filename or ".." in filename:
        raise HTTPException(400, "Invalid filename")
    key = f"uploads/{current_user.id}/{filename}"
    return {
        "upload_url": generate_upload_url(key, content_type),
        "public_url": generate_download_url(key, expiry=86400 * 7),
    }
