from fastapi.testclient import TestClient


def _setup_student_and_course(client: TestClient, admin_token: str):
    """Create a student, a course with certificate_enabled, a unit, a lesson, and a final exam question."""
    from tests.conftest import TestingSessionLocal
    from sqlalchemy import text
    from app import models as m

    db = TestingSessionLocal()
    db.execute(text("CREATE TABLE IF NOT EXISTS session (token TEXT, \"userId\" TEXT, \"expiresAt\" TIMESTAMP)"))
    db.execute(text("CREATE TABLE IF NOT EXISTS \"user\" (id TEXT PRIMARY KEY, name TEXT, email TEXT)"))
    db.add(m.Student(id="student-cert-001", name="Cert Student", grade_level=10, owner_user_id="admin-user-001"))
    db.commit()
    db.close()

    headers = {"Authorization": f"Bearer {admin_token}"}

    # Create course with certificate enabled
    r = client.post("/api/v1/courses/", json={
        "subject": "math",
        "course_type": "core",
        "title": "Cert Course",
        "short_title": "Cert",
        "description": "A cert course",
        "icon": "📚",
        "color": "#000",
        "price": 0,
        "skills": [],
        "grade_range": "9-12",
        "features": [],
        "image_emoji": "📚",
        "certificate_enabled": True,
        "certificate_passing_score": 70,
    }, headers=headers)
    assert r.status_code == 201
    course_id = r.json()["id"]

    # Create unit
    r = client.post("/api/v1/units/", json={
        "course_id": course_id,
        "title": "Unit 1",
        "slug": "unit-1",
        "order_index": 0,
        "description": "unit1",
    }, headers=headers)
    assert r.status_code == 201
    unit_id = r.json()["id"]

    # Create lesson
    r = client.post("/api/v1/lessons/", json={
        "unit_id": unit_id,
        "title": "Lesson 1",
        "slug": "lesson-1",
        "order_index": 0,
        "content": "content",
        "content_blocks": [],
        "resources": [],
        "objectives": [],
        "homework": [],
        "duration_min": 10,
        "skills": [],
    }, headers=headers)
    assert r.status_code == 201
    lesson_id = r.json()["id"]

    # Create final exam question via raw CRUD (no public API yet for creating questions)
    from tests.conftest import TestingSessionLocal
    from app import crud
    db = TestingSessionLocal()
    q = crud.create_final_exam_question(
        db, course_id=course_id,
        prompt="What is 2+2?",
        question_type=m.QuestionType.MULTIPLE_CHOICE,
        options=["3", "4", "5"],
        correct_answer=["4"],
        skill="arithmetic",
        difficulty=m.Difficulty.EASY,
        order_index=0,
    )
    db.close()

    return course_id, lesson_id, q.id


def test_start_final_exam_returns_questions(client: TestClient, admin_token: str):
    course_id, _, _ = _setup_student_and_course(client, admin_token)
    headers = {"Authorization": f"Bearer {admin_token}"}

    r = client.post(f"/api/v1/courses/{course_id}/final/start", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["course_id"] == course_id
    assert len(data["questions"]) == 1
    assert data["questions"][0]["prompt"] == "What is 2+2?"


def test_submit_final_exam_scores_and_passes(client: TestClient, admin_token: str):
    course_id, _, q_id = _setup_student_and_course(client, admin_token)
    headers = {"Authorization": f"Bearer {admin_token}"}

    payload = {
        "student_id": "student-cert-001",
        "answers": [{"question_id": q_id, "answer": ["4"]}],
    }
    r = client.post(f"/api/v1/courses/{course_id}/final/submit", json=payload, headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["total_correct"] == 1
    assert data["total_questions"] == 1
    assert data["score"] == 100
    assert data["passed"] is True
    assert data["passing_score"] == 70


def test_submit_final_exam_fails_when_wrong(client: TestClient, admin_token: str):
    course_id, _, q_id = _setup_student_and_course(client, admin_token)
    headers = {"Authorization": f"Bearer {admin_token}"}

    payload = {
        "student_id": "student-cert-001",
        "answers": [{"question_id": q_id, "answer": ["3"]}],
    }
    r = client.post(f"/api/v1/courses/{course_id}/final/submit", json=payload, headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["total_correct"] == 0
    assert data["score"] == 0
    assert data["passed"] is False
