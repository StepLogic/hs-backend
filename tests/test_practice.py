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


# ── Grading against the bank's letter keys ─────────────────────────────

def test_answers_match_reads_the_option_letter():
    from app.api.v1.endpoints.assessment import answers_match
    # the bank stores "C" while the student picks "C. $x = 45$"
    assert answers_match("C. $x = 45$", "C")
    assert not answers_match("B. $x = 40$", "C")
    assert answers_match("c) 45", "C")
    # plain and grid-in answers still work
    assert answers_match("4", "4") and answers_match("0.5", "1/2")
    assert not answers_match("A student", "A.")  # prose that merely starts with a letter


def _lettered(client, token, difficulty):
    r = client.post("/api/v1/questions/", json={
        "subject": "math", "grade_level": 8, "question_type": "multiple-choice",
        "prompt": "Solve", "correct_answer": "C", "skill": "algebra",
        "explanation": "Because.", "difficulty": difficulty,
        "options": ["A. $x = 35$", "B. $x = 40$", "C. $x = 45$", "D. $x = 135$"],
    }, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def test_questions_filter_by_difficulty(client, admin_token):
    _lettered(client, admin_token, "easy")
    hard = _lettered(client, admin_token, "hard")
    r = client.get("/api/v1/questions/", params={"difficulty": "hard", "shuffle": "true"})
    assert r.status_code == 200
    assert [q["id"] for q in r.json()] == [hard]


def test_practice_submit_grades_on_the_server(client, admin_token):
    qid = _lettered(client, admin_token, "medium")
    reg = client.post("/api/v1/auth/register", json={"email": "grade@example.com", "password": "secret123"})
    student_id = reg.json()["user_id"]
    r = client.post("/api/v1/practice/submit", json={
        "student_id": student_id, "subject": "math",
        # the client's own verdicts are the wrong way round on purpose
        "answers": [
            {"question_id": qid, "answer": "C. $x = 45$", "is_correct": False, "time_spent": 20},
            {"question_id": qid, "answer": "A. $x = 35$", "is_correct": True, "time_spent": 20},
        ],
    })
    assert r.status_code == 200, r.text
    assert r.json()["test_result"]["correct_count"] == 1
