"""A signed-in student must not reach another student's records."""


def _student(client, email):
    reg = client.post("/api/v1/auth/register", json={"email": email, "password": "secret123", "role": "student"})
    hdr = {"Authorization": f"Bearer {reg.json()['access_token']}"}
    return hdr, client.get("/api/v1/students/", headers=hdr).json()[0]["id"]


def test_student_cannot_touch_another_student(client):
    _, victim = _student(client, "victim@example.com")
    attacker, _ = _student(client, "attacker@example.com")

    assert client.delete(f"/api/v1/students/{victim}", headers=attacker).status_code == 403
    assert client.get(f"/api/v1/analytics/student/{victim}/progress", headers=attacker).status_code == 403
    assert client.get(f"/api/v1/plans/student/{victim}", headers=attacker).status_code == 403
    assert client.get(f"/api/v1/enrollments/?student_id={victim}", headers=attacker).status_code == 403


def test_private_reads_need_a_token(client):
    _, sid = _student(client, "anon@example.com")
    assert client.get(f"/api/v1/learning/path?student_id={sid}&course_id=x").status_code == 401
    assert client.get(f"/api/v1/plans/student/{sid}").status_code == 401
    assert client.get("/api/v1/results/").status_code == 401
