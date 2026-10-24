from datetime import datetime, timedelta

from app import models
from tests.conftest import TestingSessionLocal


def _setup(client, admin_token, n=1):
    hdr_admin = {"Authorization": f"Bearer {admin_token}"}
    ids = []
    for i in range(n):
        r = client.post("/api/v1/questions/", json={
            "subject": "math", "grade_level": 10, "question_type": "multiple-choice",
            "prompt": f"Q{i}", "options": ["A. 1", "B. 2"], "correct_answer": "A",
            "skill": "slope", "explanation": "x", "difficulty": "easy"}, headers=hdr_admin)
        ids.append(r.json()["id"])
    reg = client.post("/api/v1/auth/register", json={"email": "rv@example.com", "password": "secret123", "role": "student"})
    hdr = {"Authorization": f"Bearer {reg.json()['access_token']}"}
    sid = client.get("/api/v1/students/", headers=hdr).json()[0]["id"]
    return hdr, sid, ids


def _miss(sid, qid, source, days_ago, correct=False):
    db = TestingSessionLocal()
    tr = models.TestResult(
        student_id=sid, subject=models.Subject.MATH, score=0, grade_equivalent=1, percentile=1,
        correct_count=int(correct), total_questions=1, skill_breakdown={},
        mastery_level=models.MasteryLevel.BEGINNER, source=source,
        created_at=datetime.utcnow() - timedelta(days=days_ago))
    db.add(tr)
    db.flush()
    db.add(models.UserAnswer(test_result_id=tr.id, question_id=qid, answer="B", is_correct=correct, time_spent=1))
    db.commit()
    db.close()


def _review(client, hdr, sid):
    r = client.get(f"/api/v1/practice/review?student_id={sid}", headers=hdr)
    assert r.status_code == 200
    return r.json()


def test_review_due_after_two_days(client, admin_token):
    hdr, sid, [qid] = _setup(client, admin_token)
    _miss(sid, qid, "lesson", 3)
    body = _review(client, hdr, sid)
    assert body["due"] == 1 and body["questions"][0]["id"] == qid


def test_review_not_due_yet(client, admin_token):
    hdr, sid, [qid] = _setup(client, admin_token)
    _miss(sid, qid, "drill", 1)
    assert _review(client, hdr, sid) == {"questions": [], "due": 0}


def test_review_cleared_by_correct(client, admin_token):
    hdr, sid, [qid] = _setup(client, admin_token)
    _miss(sid, qid, "lesson", 5)
    _miss(sid, qid, "review", 3, correct=True)
    assert _review(client, hdr, sid)["due"] == 0


def test_review_ignores_mock_and_assessment(client, admin_token):
    hdr, sid, ids = _setup(client, admin_token, 3)
    for qid, src in zip(ids, ("mock", "assessment", None)):
        _miss(sid, qid, src, 5)
    assert _review(client, hdr, sid)["due"] == 0


def test_review_caps_at_ten_oldest_first(client, admin_token):
    hdr, sid, ids = _setup(client, admin_token, 12)
    for i, qid in enumerate(ids):
        _miss(sid, qid, "drill", 3 + i)
    body = _review(client, hdr, sid)
    assert body["due"] == 12 and len(body["questions"]) == 10
    assert body["questions"][0]["id"] == ids[11]


def test_review_skips_deleted_question(client, admin_token):
    hdr, sid, _ = _setup(client, admin_token)
    _miss(sid, "gone", "lesson", 5)
    assert _review(client, hdr, sid) == {"questions": [], "due": 0}


def test_review_other_student_403(client, admin_token):
    _, sid, _ = _setup(client, admin_token)
    other = client.post("/api/v1/auth/register", json={"email": "x@example.com", "password": "secret123", "role": "student"})
    hdr = {"Authorization": f"Bearer {other.json()['access_token']}"}
    assert client.get(f"/api/v1/practice/review?student_id={sid}", headers=hdr).status_code == 403


def test_review_skips_unpublished_and_unplayable(client, admin_token):
    hdr, sid, ids = _setup(client, admin_token, 3)
    db = TestingSessionLocal()
    db.get(models.Question, ids[0]).review_status = models.ReviewStatus.DRAFT
    db.get(models.Question, ids[1]).question_type = models.QuestionType.ORDERING
    db.commit()
    db.close()
    for qid in ids:
        _miss(sid, qid, "lesson", 5)
    body = _review(client, hdr, sid)
    assert body["due"] == 1 and body["questions"][0]["id"] == ids[2]
