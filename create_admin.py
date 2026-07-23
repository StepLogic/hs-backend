#!/usr/bin/env python3
import os, uuid, bcrypt
from datetime import datetime, timezone
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL env var is not set")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
if "sslmode=" not in DATABASE_URL:
    sep = "&" if "?" in DATABASE_URL else "?"
    DATABASE_URL = f"{DATABASE_URL}{sep}sslmode=require"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def create_admin_user(email, password, name="Admin"):
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT id FROM users WHERE email = :email"), {"email": email})
        existing = result.fetchone()
        if existing:
            print(f"User {email} already exists (id={existing.id}).")
            return
        user_id = str(uuid.uuid4())
        hashed = hash_password(password)
        now = datetime.now(timezone.utc)
        db.execute(text("""
            INSERT INTO users (id, email, hashed_password, name, role, is_active, created_at, updated_at)
            VALUES (:id, :email, :hashed_password, :name, :role, :is_active, :created_at, :updated_at)
        """), {
            "id": user_id, "email": email, "hashed_password": hashed,
            "name": name, "role": "admin", "is_active": True,
            "created_at": now, "updated_at": now,
        })
        db.commit()
        print(f"Created admin user: {email} (id={user_id})")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user("demo.admin@homeschool.com", "demo123", "Demo Admin")
