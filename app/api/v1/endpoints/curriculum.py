import json
from io import BytesIO

from b2sdk.v2.exception import FileNotPresent
from fastapi import APIRouter, HTTPException, Request

from app.b2 import get_bucket, PUBLIC_BASE

router = APIRouter()


@router.get("/{language}")
def get_curriculum(language: str):
    file_name = f"courses/{language}.json"
    # Try B2 first, fall back to local file
    try:
        bucket = get_bucket()
        try:
            download = bucket.download_file_by_name(file_name)
        except FileNotPresent:
            raise HTTPException(status_code=404, detail="Curriculum not found")
        buf = BytesIO()
        download.save(buf)
        return json.loads(buf.getvalue().decode("utf-8"))
    except HTTPException:
        raise
    except Exception:
        # B2 unavailable — try local file
        import os
        local = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "curriculum", f"{language}.json")
        if os.path.exists(local):
            with open(local, "r", encoding="utf-8") as f:
                return json.load(f)
        raise HTTPException(status_code=404, detail="Curriculum not found")


@router.put("/{language}")
async def put_curriculum(language: str, request: Request):
    body = await request.body()
    file_name = f"courses/{language}.json"
    bucket = get_bucket()
    bucket.upload_bytes(body, file_name)
    return {"url": f"{PUBLIC_BASE}/{file_name}"}