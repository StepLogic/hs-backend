from fastapi import APIRouter, File, Form, UploadFile

from app.b2 import get_bucket, PUBLIC_BASE

router = APIRouter()


@router.post("/")
async def upload_audio(file: UploadFile = File(...), key: str = Form(...)):
    bucket = get_bucket()
    data = await file.read()
    bucket.upload_bytes(data, key)
    return {"url": f"{PUBLIC_BASE}/{key}"}