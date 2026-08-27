import uuid

from tests.conftest import TestingSessionLocal
from app import models


def _course_and_students(n=2):
    db = TestingSessionLocal()
    course = models.Course(
        id=str(uuid.uuid4()), subject=models.Subject.MATH, title="Algebra I",
        short_title="Algebra", description="d", icon="x", color="#000", price=0.0,
        skills=[], grade_range="9-12", features=[], image_emoji="x",
    )
    db.add(course)
    students = []
    for i in range(n):
        s = models.Student(id=str(uuid.uuid4()), name=f"S{i}", grade_level=9)
        db.add(s)
        students.append(s.id)
    db.commit()
    course_id = course.id
    db.close()
    return course_id, students


def test_unrated_course_has_no_score(client):
    course_id, _ = _course_and_students(0)
    r = client.get(f"/api/v1/ratings/?target_type=course&target_id={course_id}")
    assert r.json()["average"] is None and r.json()["count"] == 0

    # And the course itself reports nothing rather than a zero the UI would draw.
    course = client.get(f"/api/v1/courses/{course_id}").json()
    assert course["rating"] is None and course["review_count"] == 0


def test_ratings_average_and_surface_on_the_course(client):
    course_id, (a, b) = _course_and_students(2)
    for student, stars in ((a, 5), (b, 4)):
        r = client.post("/api/v1/ratings/", json={
            "student_id": student, "target_type": "course", "target_id": course_id, "stars": stars,
        })
        assert r.status_code == 200, r.text

    assert client.get(f"/api/v1/ratings/?target_type=course&target_id={course_id}").json() == {
        "target_type": "course", "target_id": course_id,
        "average": 4.5, "count": 2, "my_stars": None,
    }
    course = client.get(f"/api/v1/courses/{course_id}").json()
    assert course["rating"] == 4.5 and course["review_count"] == 2


def test_rerating_replaces_rather_than_adds(client):
    course_id, (a, _) = _course_and_students(2)
    body = {"student_id": a, "target_type": "course", "target_id": course_id, "stars": 2}
    client.post("/api/v1/ratings/", json=body)
    out = client.post("/api/v1/ratings/", json={**body, "stars": 5}).json()
    assert out["count"] == 1 and out["average"] == 5.0 and out["my_stars"] == 5


def test_bad_input_is_rejected(client):
    course_id, (a, _) = _course_and_students(2)
    base = {"student_id": a, "target_type": "course", "target_id": course_id}
    assert client.post("/api/v1/ratings/", json={**base, "stars": 6}).status_code == 422
    assert client.post("/api/v1/ratings/", json={**base, "stars": 0}).status_code == 422
    assert client.post("/api/v1/ratings/", json={
        **base, "target_id": "nope", "stars": 3,
    }).status_code == 404
