"""Course diagnostic: tag resolution, sampling depth, and the asymmetric scoring rule."""
import pytest

from app import models
from tests.conftest import TestingSessionLocal


SKILLS = ["Circles", "Linear Functions", "Probability"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _register(client, email="diag@test.com"):
    r = client.post(
        "/api/v1/auth/register",
        json={"email": email, "name": "Diag", "password": "hunter2pass"},
    )
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


@pytest.fixture
def course():
    """A course shaped like the seeded SAT Math one: unit.title IS the skill,
    and description is human-readable prose that matches nothing."""
    db = TestingSessionLocal()
    c = models.Course(
        id="course-diag", subject="math", course_type="test_prep", title="Diag Course",
        short_title="Diag", description="d", icon="", color="", price=0.0, skills=[],
        grade_range="9-12", features=[], image_emoji="",
    )
    db.add(c)
    for i, skill in enumerate(SKILLS):
        db.add(models.Unit(
            id=f"unit-{i}", course_id="course-diag", title=skill,
            slug=f"u{i}", order_index=i,
            description=f"Geometry and Trigonometry — {skill}",  # deliberately non-matching
        ))
        for j, diff in enumerate(("easy", "medium", "medium", "medium", "hard")):
            db.add(models.Question(
                id=f"q-{i}-{j}", subject="math", grade_level=11,
                question_type="multiple-choice", prompt=f"{skill} q{j}",
                options=["A. 1", "B. 2"], correct_answer="A", skill=skill,
                explanation="because", review_status="published", difficulty=diff,
            ))
    db.commit()
    db.close()
    return "course-diag"


def test_quick_depth_asks_one_question_per_skill(client, course):
    token = _register(client)
    r = client.post(f"/api/v1/courses/{course}/assessment/start", headers=_auth(token))
    assert r.status_code == 200, r.text
    qs = r.json()["questions"]
    assert len(qs) == len(SKILLS)
    assert {q["unit_tag"] for q in qs} == set(SKILLS)


def test_tag_resolves_from_unit_title_not_description(client, course):
    """The regression that made every diagnostic 404: descriptions never match a skill."""
    token = _register(client)
    qs = client.post(f"/api/v1/courses/{course}/assessment/start", headers=_auth(token)).json()["questions"]
    assert all(q["unit_tag"] in SKILLS for q in qs)
    assert all("—" not in q["unit_tag"] for q in qs)


def test_quick_prefers_medium_difficulty(client, course):
    token = _register(client)
    qs = client.post(f"/api/v1/courses/{course}/assessment/start", headers=_auth(token)).json()["questions"]
    assert all(q["difficulty"] == "medium" for q in qs)


def test_full_depth_asks_three_per_skill(client, course):
    token = _register(client)
    r = client.post(f"/api/v1/courses/{course}/assessment/start?depth=full", headers=_auth(token))
    assert r.status_code == 200
    qs = r.json()["questions"]
    assert len(qs) == 3 * len(SKILLS)
    for skill in SKILLS:
        assert sum(1 for q in qs if q["unit_tag"] == skill) == 3


def test_quick_is_capped_so_the_test_stays_short(client, course):
    """A course with more skills than the cap must not return an hour-long test."""
    db = TestingSessionLocal()
    for i in range(30):
        skill = f"Extra Skill {i}"
        db.add(models.Unit(id=f"x-unit-{i}", course_id=course, title=skill,
                           slug=f"x{i}", order_index=100 + i))
        db.add(models.Question(
            id=f"x-q-{i}", subject="math", grade_level=11, question_type="multiple-choice",
            prompt=f"{skill}?", options=["A. 1"], correct_answer="A", skill=skill,
            explanation="e", review_status="published", difficulty="medium"))
    db.commit(); db.close()

    token = _register(client)
    qs = client.post(f"/api/v1/courses/{course}/assessment/start", headers=_auth(token)).json()["questions"]
    assert len(qs) <= 20


def test_rejects_unknown_depth(client, course):
    token = _register(client)
    r = client.post(f"/api/v1/courses/{course}/assessment/start?depth=enormous", headers=_auth(token))
    assert r.status_code == 422


def test_course_with_no_matching_questions_still_404s(client):
    db = TestingSessionLocal()
    db.add(models.Course(
        id="empty-course", subject="math", course_type="test_prep", title="Empty",
        short_title="E", description="d", icon="", color="", price=0.0, skills=[],
        grade_range="9-12", features=[], image_emoji=""))
    db.add(models.Unit(id="empty-unit", course_id="empty-course", title="Nothing Here",
                       slug="n", order_index=0))
    db.commit(); db.close()
    token = _register(client)
    r = client.post("/api/v1/courses/empty-course/assessment/start", headers=_auth(token))
    assert r.status_code == 404


def test_missing_a_single_item_marks_the_unit_weak(client, course):
    """The asymmetry: one miss => study that unit."""
    token = _register(client)
    student = client.post("/api/v1/students/", headers=_auth(token),
                          json={"name": "S", "grade_level": 10}).json()
    qs = client.post(f"/api/v1/courses/{course}/assessment/start", headers=_auth(token)).json()["questions"]

    answers = [{"question_id": q["id"], "answer": "A" if q["unit_tag"] != "Circles" else "B",
                "skill": q["skill"], "unit_tag": q["unit_tag"]} for q in qs]
    r = client.post(f"/api/v1/courses/{course}/assessment/submit", headers=_auth(token),
                    json={"student_id": student["id"], "answers": answers})
    assert r.status_code == 200, r.text
    body = r.json()
    assert "Circles" in body["weak_tags"]
    assert "Linear Functions" in body["strong_tags"]
