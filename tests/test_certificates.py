from fastapi.testclient import TestClient


def _setup_for_certificate(client: TestClient, admin_token: str):
    """Setup: course with cert enabled, unit, lesson, final exam question, student, complete lesson, pass final."""
    from tests.conftest import TestingSessionLocal
    from sqlalchemy import text
    from app import models as m, crud, schemas

    db = TestingSessionLocal()
    db.execute(text("CREATE TABLE IF NOT EXISTS session (token TEXT, \"userId\" TEXT, \"expiresAt\" TIMESTAMP)"))
    db.execute(text("CREATE TABLE IF NOT EXISTS \"user\" (id TEXT PRIMARY KEY, name TEXT, email TEXT)"))
    db.add(m.Student(id="student-cert-002", name="Cert Student 2", grade_level=10, owner_user_id="admin-user-001"))
    db.commit()
    db.close()

    headers = {"Authorization": f"Bearer {admin_token}"}

    r = client.post("/api/v1/courses/", json={
        "subject": "math",
        "course_type": "core",
        "title": "Cert Course 2",
        "short_title": "Cert2",
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

    r = client.post("/api/v1/units/", json={
        "course_id": course_id,
        "title": "Unit 1",
        "slug": "unit-1",
        "order_index": 0,
    }, headers=headers)
    assert r.status_code == 201
    unit_id = r.json()["id"]

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

    # Mark lesson as completed
    db = TestingSessionLocal()
    crud.create_or_update_lesson_progress(
        db,
        progress=schemas.LessonProgressCreate(
            student_id="student-cert-002",
            lesson_id=lesson_id,
            status=m.LessonProgressStatus.COMPLETED,
            mastery_score=100,
            attempts=1,
        )
    )
    db.close()

    # Pass final exam
    client.post(
        f"/api/v1/courses/{course_id}/final/submit",
        json={"student_id": "student-cert-002", "answers": [{"question_id": q.id, "answer": ["4"]}]},
        headers=headers,
    )

    return course_id, lesson_id, q.id


def test_eligibility_not_eligible_when_lessons_incomplete(client: TestClient, admin_token: str):
    course_id, _, _ = _setup_for_certificate(client, admin_token)
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Create a new student with no progress
    from tests.conftest import TestingSessionLocal
    from sqlalchemy import text
    from app import models as m
    db = TestingSessionLocal()
    db.execute(text("CREATE TABLE IF NOT EXISTS session (token TEXT, \"userId\" TEXT, \"expiresAt\" TIMESTAMP)"))
    db.execute(text("CREATE TABLE IF NOT EXISTS \"user\" (id TEXT PRIMARY KEY, name TEXT, email TEXT)"))
    db.add(m.Student(id="student-cert-003", name="No Progress", grade_level=10, owner_user_id="admin-user-001"))
    db.commit()
    db.close()

    r = client.get(
        f"/api/v1/courses/{course_id}/certificate/eligibility?student_id=student-cert-003",
        headers=headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["eligible"] is False
    assert data["all_lessons_done"] is False


def test_eligibility_eligible_when_all_done_and_passed(client: TestClient, admin_token: str):
    course_id, _, _ = _setup_for_certificate(client, admin_token)
    headers = {"Authorization": f"Bearer {admin_token}"}

    r = client.get(
        f"/api/v1/courses/{course_id}/certificate/eligibility?student_id=student-cert-002",
        headers=headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["eligible"] is True
    assert data["all_lessons_done"] is True
    assert data["final_passed"] is True
    assert data["final_score"] == 100


def test_claim_certificate_succeeds_when_eligible(client: TestClient, admin_token: str):
    course_id, _, _ = _setup_for_certificate(client, admin_token)
    headers = {"Authorization": f"Bearer {admin_token}"}

    r = client.post(
        f"/api/v1/courses/{course_id}/certificate/claim?student_id=student-cert-002",
        headers=headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["student_name"] == "Cert Student 2"
    assert data["course_title"] == "Cert Course 2"
    assert data["final_score"] == 100
    assert len(data["certificate_hash"]) == 12


def test_claim_certificate_fails_when_already_claimed(client: TestClient, admin_token: str):
    course_id, _, _ = _setup_for_certificate(client, admin_token)
    headers = {"Authorization": f"Bearer {admin_token}"}

    # First claim
    client.post(f"/api/v1/courses/{course_id}/certificate/claim?student_id=student-cert-002", headers=headers)

    # Second claim should fail
    r = client.post(f"/api/v1/courses/{course_id}/certificate/claim?student_id=student-cert-002", headers=headers)
    assert r.status_code == 409
    assert "already claimed" in r.json()["detail"].lower()


def test_list_certificates_returns_earned_certs(client: TestClient, admin_token: str):
    course_id, _, _ = _setup_for_certificate(client, admin_token)
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Claim first
    client.post(f"/api/v1/courses/{course_id}/certificate/claim?student_id=student-cert-002", headers=headers)

    r = client.get("/api/v1/certificates/", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 1
    assert any(c["course_id"] == course_id for c in data)
