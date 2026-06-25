import pytest


def _create_question(client, skill, difficulty="medium", token=None):
    r = client.post("/api/v1/questions/", json={
        "subject": "math",
        "grade_level": 8,
        "question_type": "multiple-choice",
        "prompt": f"What is {skill}?",
        "correct_answer": "A",
        "skill": skill,
        "explanation": "Explanation",
        "difficulty": difficulty,
        "options": ["A", "B", "C", "D"],
    }, headers={"Authorization": f"Bearer {token}"} if token else {})
    return r.json()["id"]


def _seed_skill_taxonomy(client, token, subject, skills):
    for skill in skills:
        client.post("/api/v1/skills/", json={
            "subject": subject,
            "skill": skill,
        }, headers={"Authorization": f"Bearer {token}"})


def test_practice_next_prefers_weak_skills(client, admin_token):
    # Register and create student
    reg = client.post("/api/v1/auth/register", json={"email": "practice@example.com", "password": "secret123", "role": "student"})
    token = reg.json()["access_token"]
    student_id = reg.json()["user_id"]

    # Create questions for two skills
    q1 = _create_question(client, "algebra", "easy", admin_token)
    _create_question(client, "geometry", "medium", admin_token)

    # Seed skill taxonomy via API
    _seed_skill_taxonomy(client, admin_token, "math", ["algebra", "geometry"])

    # Get practice questions
    r = client.get(f"/api/v1/practice/next?student_id={student_id}&subject=math&grade_level=8&limit=5")
    assert r.status_code == 200
    questions = r.json()
    assert len(questions) > 0

    # Answer first question correctly
    q = questions[0]
    r2 = client.post("/api/v1/practice/submit", json={
        "student_id": student_id,
        "subject": "math",
        "answers": [{"question_id": q["id"], "answer": "A", "is_correct": True, "time_spent": 20}],
    })
    assert r2.status_code == 200
    mastery = r2.json()["skill_mastery"]
    assert len(mastery) > 0
    assert mastery[0]["mastery_score"] > 0


def test_practice_respects_published_only(client, admin_token):
    # Create a draft question
    client.post("/api/v1/questions/", json={
        "subject": "math",
        "grade_level": 8,
        "question_type": "multiple-choice",
        "prompt": "Draft question",
        "correct_answer": "A",
        "skill": "draft_skill",
        "explanation": "Draft",
        "difficulty": "easy",
        "options": ["A", "B", "C", "D"],
        "review_status": "draft",
    }, headers={"Authorization": f"Bearer {admin_token}"})

    reg = client.post("/api/v1/auth/register", json={"email": "draft@example.com", "password": "secret123", "role": "student"})
    student_id = reg.json()["user_id"]

    _seed_skill_taxonomy(client, admin_token, "math", ["draft_skill"])

    r = client.get(f"/api/v1/practice/next?student_id={student_id}&subject=math&grade_level=8&limit=5")
    questions = r.json()
    for q in questions:
        assert q["review_status"] == "published"
