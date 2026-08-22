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

    # depth=practice is the same sampler sized to the course: 3 per skill here,
    # inside the 4..50 band and strictly longer than the one-per-skill screen.
    r = client.post(f"/api/v1/courses/{course_id}/assessment/start?depth=practice", headers=headers)
    assert r.status_code == 200
    practice = r.json()["questions"]
    assert 4 <= len(practice) <= 50
    assert len(practice) > len(data["questions"])


def test_submit_assessment_identifies_weak_tags(client: TestClient, admin_token: str):
    """Submitting answers should identify tags with <60% accuracy as weak."""
    # ponytail: stub tables so Better Auth fallback doesn't crash
    from tests.conftest import TestingSessionLocal
    from sqlalchemy import text
    db = TestingSessionLocal()
    db.execute(text("CREATE TABLE IF NOT EXISTS session (token TEXT, \"userId\" TEXT, \"expiresAt\" TIMESTAMP)"))
    db.execute(text("CREATE TABLE IF NOT EXISTS \"user\" (id TEXT PRIMARY KEY, name TEXT, email TEXT)"))
    db.commit()

    from app import models as m
    db.add(m.Student(id="student-001", name="Test Student", grade_level=10, owner_user_id="admin-user-001"))
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


def test_full_assessment_to_personalization_flow(client: TestClient, admin_token: str):
    """End-to-end: assessment → weak tags → personalized course → edit → activate."""
    from tests.conftest import TestingSessionLocal
    from sqlalchemy import text
    from app import models

    # ponytail: stub tables so Better Auth fallback doesn't crash
    db = TestingSessionLocal()
    db.execute(text("CREATE TABLE IF NOT EXISTS session (token TEXT, \"userId\" TEXT, \"expiresAt\" TIMESTAMP)"))
    db.execute(text("CREATE TABLE IF NOT EXISTS \"user\" (id TEXT PRIMARY KEY, name TEXT, email TEXT)"))
    db.commit()
    db.close()

    headers = {"Authorization": f"Bearer {admin_token}"}

    # Seed course with 3 tagged units via API
    r = client.post("/api/v1/courses/", json={
        "subject": "math",
        "course_type": "core",
        "title": "Flow Test Course",
        "short_title": "Flow",
        "description": "Integration flow test",
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
    unit_ids = {}
    for tag in ["algebra", "geometry", "stats"]:
        r = client.post("/api/v1/units/", json={
            "course_id": course_id,
            "title": tag.capitalize(),
            "slug": tag,
            "order_index": 0,
            "description": tag,
        }, headers=headers)
        assert r.status_code == 201
        unit_ids[tag] = r.json()["id"]

    # Create questions with skill matching unit tag
    for tag in ["algebra", "geometry", "stats"]:
        for i in range(3):
            r = client.post("/api/v1/questions/", json={
                "subject": "math",
                "grade_level": 10,
                "question_type": "multiple-choice",
                "prompt": f"{tag} Q{i}?",
                "options": ["A", "B", "C", "D"],
                "correct_answer": ["A"],
                "skill": tag,
                "explanation": "A is correct",
                "difficulty": "medium",
            }, headers=headers)
            assert r.status_code == 201

    # Seed student for FK constraint on personalized_courses
    db = TestingSessionLocal()
    db.add(models.Student(id="student-001", name="Test Student", grade_level=10, owner_user_id="admin-user-001"))
    db.commit()
    db.close()

    # 1. Start assessment
    r = client.post(f"/api/v1/courses/{course_id}/assessment/start", headers=headers)
    assert r.status_code == 200
    questions = r.json()["questions"]
    assert len(questions) >= 3

    # 2. Submit with algebra weak (all wrong), geometry strong (all right), stats strong
    answers = []
    for q in questions:
        is_correct = q["unit_tag"] != "algebra"  # algebra all wrong
        answers.append({
            "question_id": q["id"],
            "answer": ["A"] if is_correct else ["B"],
            "skill": q["skill"],
            "unit_tag": q["unit_tag"],
        })

    r = client.post(
        f"/api/v1/courses/{course_id}/assessment/submit",
        json={"student_id": "student-001", "answers": answers},
        headers=headers,
    )
    assert r.status_code == 200
    result = r.json()
    assert "algebra" in result["weak_tags"]
    assert "stats" not in result["weak_tags"]  # stats should be strong

    # 3. Generate personalized course
    r = client.post(
        f"/api/v1/courses/{course_id}/personalized",
        json={"student_id": "student-001", "weak_tags": result["weak_tags"]},
        headers=headers,
    )
    assert r.status_code == 201
    pc = r.json()
    assert pc["status"] == "draft"
    assert unit_ids["algebra"] in pc["unit_ids"]

    # 4. Edit — add geometry
    r = client.put(
        f"/api/v1/courses/{course_id}/personalized/units?student_id=student-001",
        json={"unit_ids": pc["unit_ids"] + [unit_ids["geometry"]]},
        headers=headers,
    )
    assert r.status_code == 200
    assert unit_ids["geometry"] in r.json()["unit_ids"]

    # 5. Activate
    r = client.post(
        f"/api/v1/courses/{course_id}/personalized/activate?student_id=student-001",
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["status"] == "active"

    # 6. Cannot edit after activation
    r = client.put(
        f"/api/v1/courses/{course_id}/personalized/units?student_id=student-001",
        json={"unit_ids": [unit_ids["algebra"]]},
        headers=headers,
    )
    assert r.status_code == 400
    assert "active" in r.json()["detail"].lower()
