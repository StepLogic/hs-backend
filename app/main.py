import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.api import api_router
from app.config import settings

app = FastAPI(
    title="HS Backend",
    description="Administration backend for hs-platform + language learning",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

audio_dir = os.path.join(os.path.dirname(__file__), "..", "audio")
if os.path.isdir(audio_dir):
    app.mount("/audio", StaticFiles(directory=audio_dir), name="audio")

app.include_router(api_router, prefix="/api/v1")
