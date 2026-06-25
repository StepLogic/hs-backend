import requests
from fastapi import APIRouter, HTTPException
from app.config import settings

router = APIRouter()


@router.get("/{key:path}")
def stream_audio(key: str):
    """Proxy private B2 audio through the backend so the frontend never needs B2 credentials."""
    # Authorize with B2 to get a download URL + auth token
    auth_resp = requests.get(
        "https://api.backblazeb2.com/b2api/v2/b2_authorize_account",
        auth=(settings.B2_KEY_ID, settings.B2_APP_KEY),
        timeout=10,
    )
    if auth_resp.status_code != 200:
        raise HTTPException(status_code=500, detail="B2 authorization failed")

    auth_data = auth_resp.json()
    download_url = auth_data["downloadUrl"]
    auth_token = auth_data["authorizationToken"]

    # Build the file download URL
    file_url = f"{download_url}/file/{settings.B2_BUCKET}/{key}"

    # Stream the file back to the client
    file_resp = requests.get(
        file_url,
        headers={"Authorization": auth_token},
        stream=True,
        timeout=30,
    )
    if file_resp.status_code == 404:
        raise HTTPException(status_code=404, detail="Audio not found")
    if file_resp.status_code != 200:
        raise HTTPException(status_code=500, detail="B2 download failed")

    from fastapi.responses import StreamingResponse

    return StreamingResponse(
        file_resp.iter_content(chunk_size=8192),
        media_type=file_resp.headers.get("Content-Type", "audio/wav"),
        headers={
            "Content-Length": file_resp.headers.get("Content-Length", ""),
            "Accept-Ranges": "bytes",
        },
    )
