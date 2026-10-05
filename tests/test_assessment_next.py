def _course(client, admin_token, per_skill=6):
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
    for i, tag in enumerate(["algebra", "geometry"]):
        client.post("/api/v1/units/", json={"course_id": cid, "title": tag, "slug": tag,
                    "order_index": i, "description": tag}, headers=hdr)
        for j in range(per_skill):
            client.post("/api/v1/questions/", json={
                "subject": "math", "grade_level": 10, "question_type": "multiple-choice",
                "prompt": f"{tag} {j}", "options": ["A. yes", "B. no"], "correct_answer": "A",
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
