from app import ai_service


def _setup(client, admin_token):
    hdr_admin = {"Authorization": f"Bearer {admin_token}"}
    ids = []
    for i, d in enumerate(["easy", "medium", "hard"]):
        r = client.post("/api/v1/questions/", json={
            "subject": "math", "grade_level": 10, "question_type": "multiple-choice",
            "prompt": f"Q{i}", "options": ["A. 1", "B. 2"], "correct_answer": "A",
            "skill": "slope", "explanation": "x", "difficulty": d}, headers=hdr_admin)
        ids.append(r.json()["id"])
    reg = client.post("/api/v1/auth/register", json={"email": "ai@example.com", "password": "secret123", "role": "student"})
    hdr = {"Authorization": f"Bearer {reg.json()['access_token']}"}
    sid = client.get("/api/v1/students/", headers=hdr).json()[0]["id"]
    return hdr, sid, ids


def test_ai_next_returns_a_candidate(client, admin_token, monkeypatch):
    hdr, sid, ids = _setup(client, admin_token)

    async def fake(history, candidates):
        return {"question_id": candidates[0]["id"], "reason": "Easing off after a miss."}
    monkeypatch.setattr(ai_service, "choose_next", fake)
    r = client.post("/api/v1/practice/ai-next", headers=hdr, json={
        "student_id": sid, "history": [{"question_id": ids[1], "correct": False}],
        "candidate_ids": [ids[0], ids[2]]})
    assert r.status_code == 200
    assert r.json() == {"question_id": ids[0], "reason": "Easing off after a miss."}


def test_ai_next_rejects_foreign_id(client, admin_token, monkeypatch):
    hdr, sid, ids = _setup(client, admin_token)

    async def fake(history, candidates):
        return {"question_id": "not-a-candidate", "reason": "?"}
    monkeypatch.setattr(ai_service, "choose_next", fake)
    r = client.post("/api/v1/practice/ai-next", headers=hdr, json={
        "student_id": sid, "history": [], "candidate_ids": [ids[0]]})
    assert r.status_code == 502


def test_ai_next_ai_failure_is_502(client, admin_token, monkeypatch):
    hdr, sid, ids = _setup(client, admin_token)

    async def boom(history, candidates):
        raise ValueError("bad json")
    monkeypatch.setattr(ai_service, "choose_next", boom)
    r = client.post("/api/v1/practice/ai-next", headers=hdr, json={
        "student_id": sid, "history": [], "candidate_ids": [ids[0]]})
    assert r.status_code == 502


def test_ai_next_other_students_forbidden(client, admin_token):
    _, sid, ids = _setup(client, admin_token)
    other = client.post("/api/v1/auth/register", json={"email": "x@example.com", "password": "secret123", "role": "student"})
    hdr = {"Authorization": f"Bearer {other.json()['access_token']}"}
    r = client.post("/api/v1/practice/ai-next", headers=hdr, json={
        "student_id": sid, "history": [], "candidate_ids": [ids[0]]})
    assert r.status_code == 403


def test_ai_next_needs_candidates(client, admin_token):
    hdr, sid, _ = _setup(client, admin_token)
    r = client.post("/api/v1/practice/ai-next", headers=hdr, json={
        "student_id": sid, "history": [], "candidate_ids": []})
    assert r.status_code == 422


def test_ai_next_oversized_history_is_422(client, admin_token):
    hdr, sid, ids = _setup(client, admin_token)
    r = client.post("/api/v1/practice/ai-next", headers=hdr, json={
        "student_id": sid, "history": [{"question_id": ids[0], "correct": True}] * 51,
        "candidate_ids": [ids[0]]})
    assert r.status_code == 422
