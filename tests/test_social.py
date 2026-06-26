import pytest
from fastapi.testclient import TestClient


def test_forum_post_crud(client: TestClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # create a student first
    r = client.post("/api/v1/students", json={"name": "Forum Student", "grade_level": 10}, headers=headers)
    student_id = r.json()["id"]

    # create a course
    r = client.post("/api/v1/courses", json={
        "subject": "math",
        "title": "Forum Course",
        "short_title": "FC",
        "description": "test",
        "icon": "book",
        "color": "#3b82f6",
        "price": 0,
        "grade_range": "9-12",
        "image_emoji": "📚",
        "skills": ["algebra"],
        "features": ["test"]
    }, headers=headers)
    course_id = r.json()["id"]

    # create post
    r = client.post("/api/v1/social/forum", json={
        "course_id": course_id,
        "student_id": student_id,
        "title": "Hello Forum",
        "body": "This is a test post",
        "tags": ["test", "hello"]
    }, headers=headers)
    assert r.status_code == 201
    data = r.json()
    post_id = data["id"]
    assert data["title"] == "Hello Forum"
    assert data["body"] == "This is a test post"
    assert data["tags"] == ["test", "hello"]

    # list posts
    r = client.get("/api/v1/social/forum", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) >= 1

    # list by course
    r = client.get(f"/api/v1/social/forum?course_id={course_id}", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) == 1

    # get detail
    r = client.get(f"/api/v1/social/forum/{post_id}", headers=headers)
    assert r.status_code == 200
    assert r.json()["id"] == post_id


def test_leaderboard(client: TestClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    r = client.get("/api/v1/profiles/leaderboard?limit=5", headers=headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)
