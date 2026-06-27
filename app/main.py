import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.initial_data import init_db

app = FastAPI(
    title="HS Backend",
    description="Administration backend for hs-platform",
    version="0.1.0",
)

@app.on_event("startup")
def on_startup() -> None:
    init_db()
    # Run safe migrations to add missing columns on production
    from app.migrations import run_safe_migrations
    try:
        run_safe_migrations()
    except Exception as e:
        print(f"Migration warning: {e}")
_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:4173,https://hs-platform.vercel.app,https://hs-admin-two.vercel.app,https://hs-admin.vercel.app")
allow_origins = [o.strip() for o in _origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.post("/admin/reset-db")
def reset_db():
    """Drop and recreate all tables. Use with caution — loses all data."""
    from app.database import Base, engine
    from app import models  # noqa
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    init_db()
    return {"ok": True, "message": "Database recreated with latest schema"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

app.include_router(api_router, prefix="/api/v1")
