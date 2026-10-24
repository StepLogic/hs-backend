from app import ai_service


def _setup(client, admin_token, email="tip@example.com", name=None):
    hdr_admin = {"Authorization": f"Bearer {admin_token}"}
    qid = client.post("/api/v1/questions/", json={
        "subject": "math", "grade_level": 10, "question_type": "multiple-choice",
        "prompt": "Q", "options": ["A. 1", "B. 2"], "correct_answer": "A",
        "skill": "slope", "explanation": "x", "difficulty": "medium"}, headers=hdr_admin).json()["id"]
    body = {"email": email, "password": "secret123", "role": "student"}
    if name:
        body["name"] = name
    reg = client.post("/api/v1/auth/register", json=body)
    hdr = {"Authorization": f"Bearer {reg.json()['access_token']}"}
    sid = client.get("/api/v1/students/", headers=hdr).json()[0]["id"]
    return hdr, sid, qid


def _drill(client, hdr, sid, qid, right=True, source="drill"):
    r = client.post("/api/v1/practice/submit", headers=hdr, json={
        "student_id": sid, "subject": "math", "source": source,
        "answers": [{"question_id": qid, "answer": "A" if right else "B", "is_correct": right, "time_spent": 5}]})
    assert r.status_code == 200, r.text


def _tip(client, hdr, sid):
    return client.get(f"/api/v1/students/{sid}/study-tip", headers=hdr)


def _fake(monkeypatch, summaries, tips=None):
    async def fake(summary):
        summaries.append(summary)
        return f"tip {len(summaries)}"
    monkeypatch.setattr(ai_service, "generate_study_tip", fake)


def test_tip_none_without_activity(client, admin_token, monkeypatch):
    seen = []
    _fake(monkeypatch, seen)
    hdr, sid, _ = _setup(client, admin_token)
    r = _tip(client, hdr, sid)
    assert r.status_code == 200 and r.json() == {"tip": None}
    assert seen == []


def test_tip_generated_then_cached(client, admin_token, monkeypatch):
    seen = []
    _fake(monkeypatch, seen)
    hdr, sid, qid = _setup(client, admin_token)
    _drill(client, hdr, sid, qid)
    a, b = _tip(client, hdr, sid), _tip(client, hdr, sid)
    assert a.json() == b.json() == {"tip": "tip 1"}
    assert len(seen) == 1


def test_tip_regenerates_after_new_activity(client, admin_token, monkeypatch):
    seen = []
    _fake(monkeypatch, seen)
    hdr, sid, qid = _setup(client, admin_token)
    _drill(client, hdr, sid, qid)
    _tip(client, hdr, sid)
    _drill(client, hdr, sid, qid, right=False)
    assert _tip(client, hdr, sid).json() == {"tip": "tip 2"}
    assert len(seen) == 2
    assert seen[1]["recent"] == {"right": 1, "wrong": 1}


def test_tip_summary_has_no_personal_data(client, admin_token, monkeypatch):
    seen = []
    _fake(monkeypatch, seen)
    hdr, sid, qid = _setup(client, admin_token, email="z@x.com", name="Zed Unique")
    client.put(f"/api/v1/students/{sid}", headers=hdr, json={"name": "Zed Unique"})
    _drill(client, hdr, sid, qid, right=False)
    _tip(client, hdr, sid)
    assert len(seen) == 1
    assert "Zed" not in str(seen[0]) and "z@x.com" not in str(seen[0])
    assert seen[0]["weakest"][0]["skill"] == "slope"
    assert seen[0]["strongest"] == []  # one skill: weakest took it


def test_tip_without_assessment(client, admin_token, monkeypatch):
    seen = []
    _fake(monkeypatch, seen)
    hdr, sid, qid = _setup(client, admin_token)
    _drill(client, hdr, sid, qid, right=False)
    _tip(client, hdr, sid)
    assert seen[0]["assessment_weak_skills"] == []


def test_tip_assessment_weak_skills(client, admin_token, monkeypatch):
    seen = []
    _fake(monkeypatch, seen)
    hdr, sid, qid = _setup(client, admin_token)
    _drill(client, hdr, sid, qid, right=False, source="assessment")
    _tip(client, hdr, sid)
    assert seen[0]["assessment_weak_skills"] == ["slope"]
    assert seen[0]["recent"] == {"right": 0, "wrong": 1}


def test_tip_ai_failure_returns_stored_tip(client, admin_token, monkeypatch):
    seen = []
    _fake(monkeypatch, seen)
    hdr, sid, qid = _setup(client, admin_token)
    _drill(client, hdr, sid, qid)

    async def boom(summary):
        raise RuntimeError("ollama down")
    monkeypatch.setattr(ai_service, "generate_study_tip", boom)
    assert _tip(client, hdr, sid).json() == {"tip": None}  # nothing cached yet
    _fake(monkeypatch, seen)
    assert _tip(client, hdr, sid).json() == {"tip": "tip 1"}
    _drill(client, hdr, sid, qid, right=False)
    monkeypatch.setattr(ai_service, "generate_study_tip", boom)
    r = _tip(client, hdr, sid)
    assert r.status_code == 200 and r.json() == {"tip": "tip 1"}


def test_tip_other_student_403(client, admin_token, monkeypatch):
    _fake(monkeypatch, [])
    _, sid, _ = _setup(client, admin_token)
    other = client.post("/api/v1/auth/register", json={"email": "o@example.com", "password": "secret123", "role": "student"})
    hdr = {"Authorization": f"Bearer {other.json()['access_token']}"}
    assert _tip(client, hdr, sid).status_code == 403


def test_tip_weakest_excludes_mastered_skills(client, admin_token, monkeypatch):
    from app.api.v1.endpoints.students import _study_tip_summary
    from tests.conftest import TestingSessionLocal
    from app import models
    hdr, sid, _ = _setup(client, admin_token)
    db = TestingSessionLocal()
    db.add(models.SkillMastery(student_id=sid, subject=models.Subject.MATH, skill="slope", mastery_score=90))
    db.add(models.SkillMastery(student_id=sid, subject=models.Subject.MATH, skill="ratios", mastery_score=40))
    db.commit()
    summary = _study_tip_summary(db, sid)
    db.close()
    assert [w["skill"] for w in summary["weakest"]] == ["ratios"]


def test_tip_stamped_with_latest_result_time(client, admin_token, monkeypatch):
    from tests.conftest import TestingSessionLocal
    from app import models
    from sqlalchemy import func
    _fake(monkeypatch, [])
    hdr, sid, qid = _setup(client, admin_token)
    _drill(client, hdr, sid, qid)
    _tip(client, hdr, sid)
    db = TestingSessionLocal()
    latest = db.query(func.max(models.TestResult.created_at)).filter_by(student_id=sid).scalar()
    assert db.get(models.Student, sid).study_tip_at == latest
    db.close()
