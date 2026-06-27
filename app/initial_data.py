import os

from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.database import SessionLocal
from app.security import hash_password


def init_db() -> None:
    # Ensure all tables exist (safe — create_all is idempotent, won't alter existing)
    from app.database import Base, engine
    from app import models  # noqa: F401 — registers all models with Base
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        admin_email = os.getenv("ADMIN_EMAIL")
        admin_password = os.getenv("ADMIN_PASSWORD")
        if not admin_email or not admin_password:
            return
        existing = crud.get_user_by_email(db, admin_email)
        if existing:
            return
        db_user = models.User(
            email=admin_email,
            password_hash=hash_password(admin_password),
            role=models.Role.ADMIN,
        )
        db.add(db_user)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
