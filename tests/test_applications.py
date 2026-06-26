import pytest
from datetime import date


def test_application_crud(client, admin_token):
    # create a student first
    r = client.post("/api/v1/students/", json={
        "name": "Test Student",
        "email": "test@student.com",
        "grade_level": 11,
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 201
    student_id = r.json()["id"]

    # create a college first
    r = client.post("/api/v1/colleges/", json={
        "name": "Test College",
        "location": "Testville",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 201
    college_id = r.json()["id"]

    # create application
    r = client.post("/api/v1/applications/", json={
        "student_id": student_id,
        "college_id": college_id,
        "round": "ED",
        "deadline": "2025-11-01",
        "status": "planning",
        "essays": [],
        "requirements": {},
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 201
    app_id = r.json()["id"]
    assert r.json()["status"] == "planning"

    # get by student
    r = client.get(f"/api/v1/applications/student/{student_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    assert len(r.json()) == 1

    # update status
    r = client.put(f"/api/v1/applications/{app_id}/status", json={
        "status": "in_progress",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    assert r.json()["status"] == "in_progress"

    # update full
    r = client.put(f"/api/v1/applications/{app_id}", json={
        "round": "RD",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    assert r.json()["round"] == "RD"

    # delete
    r = client.delete(f"/api/v1/applications/{app_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    assert r.json()["ok"] is True

    # verify deleted
    r = client.get(f"/api/v1/applications/student/{student_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    assert len(r.json()) == 0
