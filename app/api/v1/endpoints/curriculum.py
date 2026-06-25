import json
from io import BytesIO

from b2sdk.v2.exception import FileNotPresent
from fastapi import APIRouter, HTTPException, Request

from app.b2 import get_bucket, PUBLIC_BASE

router = APIRouter()


@router.get("/{language}")
def get_curriculum(language: str):
    bucket = get_bucket()
    file_name = f"courses/{language}.json"
    try:
        download = bucket.download_file_by_name(file_name)
    except FileNotPresent:
        raise HTTPException(status_code=404, detail="Curriculum not found")
    buf = BytesIO()
    download.save(buf)
    return json.loads(buf.getvalue().decode("utf-8"))


@router.put("/{language}")
async def put_curriculum(language: str, request: Request):
    body = await request.body()
    file_name = f"courses/{language}.json"
    bucket = get_bucket()
    bucket.upload_bytes(body, file_name)
    return {"url": f"{PUBLIC_BASE}/{file_name}"}