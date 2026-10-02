import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api.v1.api import api_router
from app.config import settings
from app.initial_data import init_db

app = FastAPI(
    title="HS Backend",
    description="Administration backend for hs-platform",
    version="0.1.0",
)
# print(settings)
@app.on_event("startup")
def on_startup() -> None:
    init_db()
    # Run safe migrations to add missing columns on production
    from app.migrations import run_safe_migrations
    try:
        run_safe_migrations()
    except Exception as e:
        print(f"Migration warning: {e}")


# JSON compresses ~5-8x; the admin question list alone is ~10 MB uncompressed.
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    # A wildcard origin and credentials cannot be combined — the browser rejects the
    # response and never stores the cookie, which is what broke the Google OAuth state.
    allow_origins=[
        o.strip()
        for o in (
            settings.ALLOWED_ORIGINS.split(",")
            if getattr(settings, "ALLOWED_ORIGINS", "")
            else [settings.FRONTEND_URL, "http://localhost:5173", "http://localhost:4173"]
        )
        if o and o.strip()
    ],
    allow_origin_regex=getattr(settings, "ALLOWED_ORIGIN_REGEX", None) or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/health")
def health_check():
    return {"status": "ok"}

app.include_router(api_router, prefix="/api/v1")
