import os
import sqlite3

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = os.environ.get("DATABASE_URL", "sqlite:///./test_smoke.db")
os.environ["SECRET_KEY"] = "test"

from app.main import app
from app.database import SessionLocal, engine, Base
from app import crud, models

client = TestClient(app)


def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def teardown_module():
    db_path = os.environ["DATABASE_URL"].replace("sqlite:///", "")
    if os.path.exists(db_path):
        os.remove(db_path)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_existing_endpoints():
    # Students
    r = client.post("/api/v1/students/", json={"name": "Alice", "email": "alice@example.com", "grade_level": 3})
    assert r.status_code == 201
    student = r.json()
    assert student["id"]

    r = client.get(f"/api/v1/students/{student['id']}")
    assert r.status_code == 200

    # Courses
    r = client.get("/api/v1/courses/")
    assert r.status_code == 200

    # Questions
    r = client.get("/api/v1/questions/")
    assert r.status_code == 200


def test_lessons_roundtrip():
    db = SessionLocal()
    try:
        # Seed audio + lesson + items
        audio = crud.upsert_audio_asset(db, "spanish", "Hola", "ef_dora", 1.0, "spanish/abc_1.0.wav")
        lesson = crud.create_lesson(db, "spanish", "u1", "Greetings", "Hello", 1)
        crud.create_lesson_item(
            db, lesson.id, 0, "listen", "Hola",
            audio_id=audio.id, translation="Hello",
        )
    finally:
        db.close()

    r = client.get("/api/v1/lessons/?language=spanish")
    assert r.status_code == 200
    lessons = r.json()
    assert len(lessons) >= 1
    lesson_id = lessons[0]["id"]

    r = client.get(f"/api/v1/lessons/{lesson_id}")
    assert r.status_code == 200
    detail = r.json()
    assert detail["unit"] == "u1"
    assert detail["items"][0]["audio_url"] is not None


def test_review_roundtrip():
    db = SessionLocal()
    try:
        audio = crud.upsert_audio_asset(db, "spanish", "Hola poem", "ef_dora", 1.0, "spanish/poem_1.0.wav")
        review = crud.upsert_unit_review(
            db, "spanish", "u1", "Greetings",
            "Hola, ¿cómo estás?",
            [
                {"prompt": "What is the first word?", "options": ["Hola", "Adiós"], "correct_answer": "Hola", "explanation": "It starts with Hola."},
            ],
            poem_audio_id=audio.id,
        )
        review_id = review.id
    finally:
        db.close()

    r = client.get("/api/v1/reviews/u1?language=spanish")
    assert r.status_code == 200
    data = r.json()
    assert data["poem_text"] == "Hola, ¿cómo estás?"
    assert data["poem_audio_url"].endswith("spanish/poem_1.0.wav")
    assert len(data["questions"]) == 1

    # Review progress
    r = client.post("/api/v1/review-progress/", json={
        "student_id": "student-1",
        "review_id": review_id,
        "score": 80,
        "completed": True,
    })
    assert r.status_code == 201
    progress = r.json()
    assert progress["score"] == 80

    r = client.get("/api/v1/review-progress/?student_id=student-1")
    assert r.status_code == 200
    assert len(r.json()) == 1
