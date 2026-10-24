from app import ai_service, models
from tests.conftest import TestingSessionLocal
from tests.test_hints import _question


def _fake(monkeypatch, calls):
    async def fake(prompt, context, options, chosen, correct, explanation):
        calls.append(chosen)
        return f"You picked {chosen}."
    monkeypatch.setattr(ai_service, "generate_wrong_feedback", fake)


def _post(client, token, qid, answer):
    return client.post(f"/api/v1/questions/{qid}/wrong-feedback", json={"answer": answer},
                       headers={"Authorization": f"Bearer {token}"})


def test_wrong_feedback_cached_per_option(client, admin_token, monkeypatch):
    calls = []
    _fake(monkeypatch, calls)
    qid = _question(client, admin_token)
    assert _post(client, admin_token, qid, "A").json() == {"feedback": "You picked A. 2."}
    _post(client, admin_token, qid, "A")
    assert len(calls) == 1
    _post(client, admin_token, qid, "C")
    assert len(calls) == 2
    db = TestingSessionLocal()
    row = db.get(models.Question, qid)
    assert set(row.wrong_feedback) == {"A", "C"}
    db.close()


def test_wrong_feedback_letter_and_text_share_cache(client, admin_token, monkeypatch):
    calls = []
    _fake(monkeypatch, calls)
    qid = _question(client, admin_token)
    r1 = _post(client, admin_token, qid, "A")
    r2 = _post(client, admin_token, qid, "A. 2")
    assert len(calls) == 1 and r1.json() == r2.json()


def test_wrong_feedback_correct_answer_400(client, admin_token, monkeypatch):
    calls = []
    _fake(monkeypatch, calls)
    qid = _question(client, admin_token)
    assert _post(client, admin_token, qid, "B").status_code == 400
    assert _post(client, admin_token, qid, "B. 5").status_code == 400
    assert calls == []


def test_wrong_feedback_not_multiple_choice_400(client, admin_token, monkeypatch):
    _fake(monkeypatch, [])
    qid = _question(client, admin_token, question_type="fill-in", options=None, correct_answer="5")
    assert _post(client, admin_token, qid, "4").status_code == 400


def test_wrong_feedback_ai_failure_503(client, admin_token, monkeypatch):
    async def boom(*a, **k):
        raise RuntimeError("ollama down")
    monkeypatch.setattr(ai_service, "generate_wrong_feedback", boom)
    qid = _question(client, admin_token)
    assert _post(client, admin_token, qid, "A").status_code == 503
    db = TestingSessionLocal()
    assert db.get(models.Question, qid).wrong_feedback is None
    db.close()


def test_wrong_feedback_unknown_question_404(client, admin_token):
    assert _post(client, admin_token, "nope", "A").status_code == 404


def test_wrong_feedback_requires_auth(client, admin_token):
    qid = _question(client, admin_token)
    assert client.post(f"/api/v1/questions/{qid}/wrong-feedback", json={"answer": "A"}).status_code == 401


def test_wrong_feedback_key_stored_as_option_text_400(client, admin_token, monkeypatch):
    calls = []
    _fake(monkeypatch, calls)
    qid = _question(client, admin_token, correct_answer="B. 5")
    assert _post(client, admin_token, qid, "B").status_code == 400
    assert _post(client, admin_token, qid, "B. 5").status_code == 400
    assert calls == []
