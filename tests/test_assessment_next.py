def _course(client, admin_token, per_skill=6, tag_names=("algebra", "geometry")):
    from tests.conftest import TestingSessionLocal
    from sqlalchemy import text
    db = TestingSessionLocal()
    db.execute(text("CREATE TABLE IF NOT EXISTS session (token TEXT, \"userId\" TEXT, \"expiresAt\" TIMESTAMP)"))
    db.execute(text("CREATE TABLE IF NOT EXISTS \"user\" (id TEXT PRIMARY KEY, name TEXT, email TEXT)"))
    db.commit()
    db.close()
    hdr = {"Authorization": f"Bearer {admin_token}"}
    cid = client.post("/api/v1/courses/", json={
        "subject": "math", "course_type": "core", "title": "Adaptive", "short_title": "A",
        "description": "d", "icon": "x", "color": "#000", "price": 0, "skills": [],
        "grade_range": "9-12", "features": [], "image_emoji": "x"}, headers=hdr).json()["id"]
    for i, tag in enumerate(tag_names):
        client.post("/api/v1/units/", json={"course_id": cid, "title": tag, "slug": tag,
                    "order_index": i, "description": tag}, headers=hdr)
        for j in range(per_skill):
            client.post("/api/v1/questions/", json={
                "subject": "math", "grade_level": 10, "question_type": "multiple-choice",
                "prompt": f"{tag} {j}", "context": f"Passage for {tag}", "options": ["A. yes", "B. no"], "correct_answer": "A",
                "skill": tag, "explanation": "x",
                "difficulty": ["easy", "medium", "hard"][j % 3]}, headers=hdr)
    reg = client.post("/api/v1/auth/register", json={"email": f"s{per_skill}@example.com", "password": "secret123", "role": "student"})
    shdr = {"Authorization": f"Bearer {reg.json()['access_token']}"}
    sid = client.get("/api/v1/students/", headers=shdr).json()[0]["id"]
    return cid, shdr, sid


def _run(client, cid, hdr, sid, answer_for):
    answers, asked = [], []
    for _ in range(40):
        r = client.post(f"/api/v1/courses/{cid}/assessment/next", headers=hdr,
                        json={"student_id": sid, "answers": answers})
        assert r.status_code == 200
        body = r.json()
        if body["done"]:
            return asked, body
        q = body["question"]
        asked.append(q)
        answers.append({"question_id": q["id"], "answer": answer_for(q)})
    raise AssertionError("never finished")


def test_two_right_settles_each_tag(client, admin_token):
    cid, hdr, sid = _course(client, admin_token)
    asked, body = _run(client, cid, hdr, sid, lambda q: "A. yes")
    assert len(asked) == 4  # 2 per tag
    assert body["settled"] == body["total_tags"] == 2
    assert all(q["difficulty"] != "easy" for q in asked)  # starts medium, steps up
    # Reading questions are unanswerable without their passage.
    assert all(q["context"] == f"Passage for {q['unit_tag']}" for q in asked)


def test_two_wrong_settles_each_tag(client, admin_token):
    cid, hdr, sid = _course(client, admin_token)
    asked, _ = _run(client, cid, hdr, sid, lambda q: "B. no")
    assert len(asked) == 4


def test_mixed_stops_at_four_per_tag(client, admin_token):
    cid, hdr, sid = _course(client, admin_token)
    flip = {"n": 0}

    def alternate(q):
        flip["n"] += 1
        return "A. yes" if flip["n"] % 2 else "B. no"
    asked, _ = _run(client, cid, hdr, sid, alternate)
    per_tag = {}
    for q in asked:
        per_tag[q["unit_tag"]] = per_tag.get(q["unit_tag"], 0) + 1
    assert all(n <= 4 for n in per_tag.values())


def test_next_settles_tag_when_bank_runs_out(client, admin_token):
    cid, hdr, sid = _course(client, admin_token, per_skill=1)
    flip = {"n": 0}

    def alternate(q):
        flip["n"] += 1
        return "A. yes" if flip["n"] % 2 else "B. no"
    asked, body = _run(client, cid, hdr, sid, alternate)
    assert len(asked) == 2 and body["done"]


def test_next_unknown_course_404(client, admin_token):
    _, hdr, sid = _course(client, admin_token)
    r = client.post("/api/v1/courses/nope/assessment/next", headers=hdr, json={"student_id": sid, "answers": []})
    assert r.status_code == 404


def test_next_other_student_403(client, admin_token):
    cid, _, sid = _course(client, admin_token)
    other = client.post("/api/v1/auth/register", json={"email": "o@example.com", "password": "secret123", "role": "student"})
    hdr = {"Authorization": f"Bearer {other.json()['access_token']}"}
    r = client.post(f"/api/v1/courses/{cid}/assessment/next", headers=hdr, json={"student_id": sid, "answers": []})
    assert r.status_code == 403


def test_many_tags_all_get_asked_before_any_third_question(client, admin_token):
    tags = tuple(f"tag{i}" for i in range(10))
    cid, hdr, sid = _course(client, admin_token, tag_names=tags)
    asked, body = _run(client, cid, hdr, sid, lambda q: "A. yes")
    order = [q["unit_tag"] for q in asked]
    assert set(order) == set(tags)
    third = next((i for i in range(len(order)) if order[:i + 1].count(order[i]) == 3), len(order))
    assert set(order[:third]) == set(tags)
    assert body["done"]


def test_next_oversized_answers_422(client, admin_token):
    cid, hdr, sid = _course(client, admin_token)
    r = client.post(f"/api/v1/courses/{cid}/assessment/next", headers=hdr,
                    json={"student_id": sid, "answers": [{"question_id": "x", "answer": "A"}] * 61})
    assert r.status_code == 422


def test_fixed_diagnostic_replaces_adaptive(client, admin_token):
    from tests.conftest import TestingSessionLocal
    from app import models
    cid, hdr, sid = _course(client, admin_token)
    db = TestingSessionLocal()
    for n, tag in [(2, "geometry"), (1, "algebra"), (3, "algebra")]:  # out of order on purpose
        db.add(models.Question(
            id=f"diagnostic-x-{n:02d}", subject="math", grade_level=11, question_type="fill-in",
            prompt=f"d{n}", correct_answer="1", skill=tag, explanation="x",
            source_test_id="diagnostic-x", mock_position=n, course_id=cid))
    db.commit()
    db.close()
    asked, body = _run(client, cid, hdr, sid, lambda q: "1")
    assert [q["prompt"] for q in asked] == ["d1", "d2", "d3"]
    assert [q["unit_tag"] for q in asked] == ["algebra", "geometry", "algebra"]
    assert body["fixed"] and body["settled"] == body["total_tags"] == 3


def test_diagnostic_data_keys_grade():
    """Every key in the shipped diagnostics is gradable, in the forms students type."""
    import json
    from pathlib import Path
    from app.api.v1.endpoints.assessment import answers_match
    for f in ("diagnostic_math.json", "diagnostic_rw.json"):
        for q in json.loads((Path(__file__).parent.parent / "data" / f).read_text())["questions"]:
            if q.get("options"):
                picked = next(o for o in q["options"] if o.startswith(q["correct_answer"] + ". "))
                assert answers_match(picked, q["correct_answer"])
                assert not any(answers_match(o, q["correct_answer"]) for o in q["options"] if o != picked)
            else:
                assert answers_match(q["correct_answer"], q["correct_answer"])
    for typed, key in [("0.05", "1/20"), ("-0.6", "-3/5"), ("1.82", "1.82")]:
        assert answers_match(typed, key)
