from app import ai_service
from app.api.v1.endpoints.questions import answer_leaks


def _question(client, admin_token, **over):
    body = {
        "subject": "math", "grade_level": 10, "question_type": "multiple-choice",
        "prompt": "2x = 10. x?", "options": ["A. 2", "B. 5", "C. 10", "D. 20"],
        "correct_answer": "B", "skill": "algebra", "explanation": "Divide by 2.",
        "difficulty": "medium",
    }
    body.update(over)
    r = client.post("/api/v1/questions/", json=body, headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 201
    return r.json()["id"]


def test_hint_generated_once_and_cached(client, admin_token, monkeypatch):
    calls = []

    async def fake(*a, **k):
        calls.append(1)
        return "Undo the multiplication on the left."
    monkeypatch.setattr(ai_service, "generate_hint", fake)
    qid = _question(client, admin_token)
    hdr = {"Authorization": f"Bearer {admin_token}"}
    r1 = client.post(f"/api/v1/questions/{qid}/hint", headers=hdr)
    r2 = client.post(f"/api/v1/questions/{qid}/hint", headers=hdr)
    assert r1.status_code == 200 and r1.json()["hint"] == "Undo the multiplication on the left."
    assert r2.json() == r1.json()
    assert len(calls) == 1


def test_hint_rejects_leak_then_retries(client, admin_token, monkeypatch):
    replies = iter(["The answer is B.", "Divide both sides by the same number."])

    async def fake(*a, **k):
        return next(replies)
    monkeypatch.setattr(ai_service, "generate_hint", fake)
    qid = _question(client, admin_token)
    r = client.post(f"/api/v1/questions/{qid}/hint", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.json()["hint"] == "Divide both sides by the same number."


def test_hint_ai_failure_saves_nothing(client, admin_token, monkeypatch):
    async def boom(*a, **k):
        raise RuntimeError("ollama down")
    monkeypatch.setattr(ai_service, "generate_hint", boom)
    qid = _question(client, admin_token)
    hdr = {"Authorization": f"Bearer {admin_token}"}
    assert client.post(f"/api/v1/questions/{qid}/hint", headers=hdr).status_code == 503
    assert client.get(f"/api/v1/questions/{qid}").json()["hint"] is None


def test_hint_needs_token(client, admin_token):
    qid = _question(client, admin_token)
    assert client.post(f"/api/v1/questions/{qid}/hint").status_code == 401


def test_answer_leaks():
    opts = ["A. 2", "B. 5", "C. 10", "D. 20"]
    assert answer_leaks("The answer is B.", opts, "B")
    assert answer_leaks("Pick option (B)", opts, "B")
    assert answer_leaks("It comes out to 5", opts, "B")          # option text
    assert not answer_leaks("Divide both sides by 2.", opts, "B")
    assert answer_leaks("x equals 2.5", None, "2.5")              # grid-in
    assert not answer_leaks("Think about halving.", None, "2.5")
    assert answer_leaks("It comes out to 5.", opts, "B")
    assert answer_leaks("x equals 2.5.", None, "2.5")
    assert answer_leaks("Answer: B", opts, "B")
    assert not answer_leaks("Use 12.55 as the rate.", None, "2.5")
