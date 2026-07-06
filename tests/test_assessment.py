from fastapi.testclient import TestClient


def test_start_assessment_returns_questions_per_tag(client: TestClient, admin_token: str):
    """Assessment should return at least 1 question per unit tag in the course."""
    # ponytail: create Better Auth session table so get_current_user's
    # Better Auth fallback doesn't crash on the missing table
    from tests.conftest import TestingSessionLocal
    from sqlalchemy import text
    db = TestingSessionLocal()
    db.execute(text("CREATE TABLE IF NOT EXISTS session (token TEXT, \"userId\" TEXT, \"expiresAt\" TIMESTAMP)"))
    db.execute(text("CREATE TABLE IF NOT EXISTS \"user\" (id TEXT PRIMARY KEY, name TEXT, email TEXT)"))
    db.commit()
    db.close()

    headers = {"Authorization": f"Bearer {admin_token}"}

    # Create course via API
    r = client.post("/api/v1/courses/", json={
        "subject": "math",
        "course_type": "core",
        "title": "Test Course",
        "short_title": "Test",
        "description": "A test course",
        "icon": "📚",
        "color": "#000",
        "price": 0,
        "skills": [],
        "grade_range": "9-12",
        "features": [],
        "image_emoji": "📚",
    }, headers=headers)
    assert r.status_code == 201
    course_id = r.json()["id"]

    # Create units with description as tag
    r1 = client.post("/api/v1/units/", json={
        "course_id": course_id,
        "title": "Algebra",
        "slug": "algebra",
        "order_index": 0,
        "description": "algebra",
    }, headers=headers)
    assert r1.status_code == 201

    r2 = client.post("/api/v1/units/", json={
        "course_id": course_id,
        "title": "Geometry",
        "slug": "geometry",
        "order_index": 1,
        "description": "geometry",
    }, headers=headers)
    assert r2.status_code == 201

    # Create questions with skill matching unit tag
    for i in range(3):
        client.post("/api/v1/questions/", json={
            "subject": "math",
            "grade_level": 10,
            "question_type": "multiple-choice",
            "prompt": f"Algebra question {i}?",
            "options": ["A", "B", "C", "D"],
            "correct_answer": ["A"],
            "skill": "algebra",
            "explanation": "Because A",
            "difficulty": "medium",
        }, headers=headers)
        client.post("/api/v1/questions/", json={
            "subject": "math",
            "grade_level": 10,
            "question_type": "multiple-choice",
            "prompt": f"Geometry question {i}?",
            "options": ["A", "B", "C", "D"],
            "correct_answer": ["A"],
            "skill": "geometry",
            "explanation": "Because A",
            "difficulty": "medium",
        }, headers=headers)

    # Call assessment start endpoint
    r = client.post(f"/api/v1/courses/{course_id}/assessment/start", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert "questions" in data
    assert len(data["questions"]) >= 2  # at least one per tag
    tags = {q["unit_tag"] for q in data["questions"]}
    assert "algebra" in tags
    assert "geometry" in tags


def test_submit_assessment_identifies_weak_tags(client: TestClient, admin_token: str):
    """Submitting answers should identify tags with <60% accuracy as weak."""
    # ponytail: stub tables so Better Auth fallback doesn't crash
    from tests.conftest import TestingSessionLocal
    from sqlalchemy import text
    db = TestingSessionLocal()
    db.execute(text("CREATE TABLE IF NOT EXISTS session (token TEXT, \"userId\" TEXT, \"expiresAt\" TIMESTAMP)"))
    db.execute(text("CREATE TABLE IF NOT EXISTS \"user\" (id TEXT PRIMARY KEY, name TEXT, email TEXT)"))
    db.commit()
    db.close()

    headers = {"Authorization": f"Bearer {admin_token}"}

    # Create course via API
    r = client.post("/api/v1/courses/", json={
        "subject": "math",
        "course_type": "core",
        "title": "Test Course",
        "short_title": "Test",
        "description": "A test course",
        "icon": "📚",
        "color": "#000",
        "price": 0,
        "skills": [],
        "grade_range": "9-12",
        "features": [],
        "image_emoji": "📚",
    }, headers=headers)
    assert r.status_code == 201
    course_id = r.json()["id"]

    # Create units
    client.post("/api/v1/units/", json={
        "course_id": course_id,
        "title": "Algebra",
        "slug": "algebra",
        "order_index": 0,
        "description": "algebra",
    }, headers=headers)
    client.post("/api/v1/units/", json={
        "course_id": course_id,
        "title": "Geometry",
        "slug": "geometry",
        "order_index": 1,
        "description": "geometry",
    }, headers=headers)

    # Create questions and collect their IDs
    algebra_ids = []
    geometry_ids = []
    for i in range(3):
        r = client.post("/api/v1/questions/", json={
            "subject": "math",
            "grade_level": 10,
            "question_type": "multiple-choice",
            "prompt": f"Algebra question {i}?",
            "options": ["A", "B", "C", "D"],
            "correct_answer": ["A"],
            "skill": "algebra",
            "explanation": "Because A",
            "difficulty": "medium",
        }, headers=headers)
        assert r.status_code == 201
        algebra_ids.append(r.json()["id"])

        r = client.post("/api/v1/questions/", json={
            "subject": "math",
            "grade_level": 10,
            "question_type": "multiple-choice",
            "prompt": f"Geometry question {i}?",
            "options": ["A", "B", "C", "D"],
            "correct_answer": ["A"],
            "skill": "geometry",
            "explanation": "Because A",
            "difficulty": "medium",
        }, headers=headers)
        assert r.status_code == 201
        geometry_ids.append(r.json()["id"])

    # Submit: algebra answers are all wrong (B, C, D vs correct A) → weak
    # geometry answers are all correct (A) → strong
    payload = {
        "student_id": "student-001",
        "answers": [
            {"question_id": algebra_ids[0], "answer": ["B"], "skill": "algebra", "unit_tag": "algebra"},
            {"question_id": algebra_ids[1], "answer": ["C"], "skill": "algebra", "unit_tag": "algebra"},
            {"question_id": algebra_ids[2], "answer": ["D"], "skill": "algebra", "unit_tag": "algebra"},
            {"question_id": geometry_ids[0], "answer": ["A"], "skill": "geometry", "unit_tag": "geometry"},
            {"question_id": geometry_ids[1], "answer": ["A"], "skill": "geometry", "unit_tag": "geometry"},
            {"question_id": geometry_ids[2], "answer": ["A"], "skill": "geometry", "unit_tag": "geometry"},
        ],
    }
    r = client.post(
        f"/api/v1/courses/{course_id}/assessment/submit",
        json=payload,
        headers=headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert "weak_tags" in data
    assert "strong_tags" in data
    assert "tag_results" in data
    # algebra: 0/3 correct (all wrong answers) → weak
    assert "algebra" in data["weak_tags"]
    # geometry: 3/3 correct → strong
    assert "geometry" in data["strong_tags"]
