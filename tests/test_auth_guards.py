"""Writes that change content or someone's record must be authenticated and owned."""


def _student(client, email):
    reg = client.post("/api/v1/auth/register", json={"email": email, "password": "secret123"})
    hdr = {"Authorization": f"Bearer {reg.json()['access_token']}"}
    return hdr, client.get("/api/v1/students/", headers=hdr).json()[0]["id"]


def test_content_writes_need_staff(client, admin_token):
    course = {"subject": "math", "course_type": "core", "title": "T", "short_title": "T",
              "description": "d", "icon": "x", "color": "#000", "price": 0, "skills": [],
              "grade_range": "9-12", "features": [], "image_emoji": "x"}
    # anonymous: refused
    assert client.post("/api/v1/courses/", json=course).status_code == 401
    assert client.delete("/api/v1/courses/anything").status_code == 401
    assert client.delete("/api/v1/questions/anything").status_code == 401
    # a signed-in student: still refused
    hdr, _ = _student(client, "s@example.com")
    assert client.post("/api/v1/courses/", json=course, headers=hdr).status_code == 403
    assert client.post("/api/v1/units/", json={}, headers=hdr).status_code == 403
    # staff: allowed
    admin = {"Authorization": f"Bearer {admin_token}"}
    r = client.post("/api/v1/courses/", json=course, headers=admin)
    assert r.status_code in (200, 201), r.text
    assert client.delete(f"/api/v1/courses/{r.json()['id']}", headers=admin).status_code == 200


def test_the_wipe_everything_endpoint_is_gone(client, admin_token):
    admin = {"Authorization": f"Bearer {admin_token}"}
    # /all is now just an unknown course id
    assert client.delete("/api/v1/courses/all", headers=admin).status_code == 404


def test_student_writes_need_the_owner(client, admin_token):
    mine, my_student = _student(client, "me@example.com")
    theirs, _ = _student(client, "them@example.com")
    body = {"student_id": my_student, "subject": "math", "answers": []}
    assert client.post("/api/v1/practice/submit", json=body).status_code == 401
    assert client.post("/api/v1/practice/submit", json=body, headers=theirs).status_code == 403
    assert client.post("/api/v1/practice/submit", json=body, headers=mine).status_code == 200

    rating = {"student_id": my_student, "target_type": "course", "target_id": "x", "stars": 4}
    assert client.post("/api/v1/ratings/", json=rating).status_code == 401
    assert client.post("/api/v1/ratings/", json=rating, headers=theirs).status_code == 403

    progress = {"student_id": my_student, "lesson_id": "x", "status": "completed", "mastery_score": 0}
    assert client.post("/api/v1/learning/progress", json=progress, headers=theirs).status_code == 403
    assert client.post("/api/v1/sat/assessment/submit", params={"student_id": my_student},
                       json=[], headers=theirs).status_code == 403
