"""Course goals: the two progress lines, and the distinction between
'not practiced yet' and 'tried and failed'."""
import pytest

from app import models
from tests.conftest import TestingSessionLocal

COURSE = "goal-course"
SKILLS = ["Circles", "Probability"]


def _auth(t):
    return {"Authorization": f"Bearer {t}"}


@pytest.fixture
def setup(client):
    token = client.post("/api/v1/auth/register", json={
        "email": "goal@test.com", "name": "Goal", "password": "hunter2pass"}).json()["access_token"]
    student = client.post("/api/v1/students/", headers=_auth(token),
                          json={"name": "G", "grade_level": 11}).json()
    db = TestingSessionLocal()
    db.add(models.Course(
        id=COURSE, subject="math", course_type="test_prep", title="Goal Course",
        short_title="G", description="d", icon="", color="", price=0.0, skills=[],
        grade_range="9-12", features=[], image_emoji=""))
    db.commit(); db.close()
    return token, student["id"]


def _set_goal(client, token, sid, **kw):
    body = {"student_id": sid, "scope": "weak_units", "target_skills": SKILLS,
            "baseline": {"Circles": 0.0, "Probability": 50.0}}
    body.update(kw)
    return client.post(f"/api/v1/courses/{COURSE}/goals", headers=_auth(token), json=body)


def _mastery(sid, skill, score):
    db = TestingSessionLocal()
    db.add(models.SkillMastery(student_id=sid, subject="math", skill=skill, mastery_score=score))
    db.commit(); db.close()


def _exam(sid, score):
    db = TestingSessionLocal()
    db.add(models.FinalExamAttempt(student_id=sid, course_id=COURSE, score=score, passed=score >= 70))
    db.commit(); db.close()


def test_untouched_skills_read_as_not_practiced_not_failed(client, setup):
    """SkillMastery is only written by the practice runner. A student who has not
    practiced must not be reported as having failed the goal."""
    token, sid = setup
    r = _set_goal(client, token, sid)
    assert r.status_code == 201, r.text
    body = r.json()
    assert {s["status"] for s in body["skills"]} == {"not_practiced"}
    assert body["skills_met"] == 0
    assert body["skills_total"] == 2
    assert body["achieved_at"] is None


def test_baseline_is_carried_through(client, setup):
    token, sid = setup
    body = _set_goal(client, token, sid).json()
    by_skill = {s["skill"]: s for s in body["skills"]}
    assert by_skill["Probability"]["baseline_percent"] == 50.0
    assert by_skill["Circles"]["baseline_percent"] == 0.0


def test_mastery_line_advances_independently_of_the_exam(client, setup):
    token, sid = setup
    _set_goal(client, token, sid)
    _mastery(sid, "Circles", 85)
    _mastery(sid, "Probability", 40)
    body = client.get(f"/api/v1/courses/{COURSE}/goals?student_id={sid}", headers=_auth(token)).json()
    by_skill = {s["skill"]: s["status"] for s in body["skills"]}
    assert by_skill == {"Circles": "met", "Probability": "in_progress"}
    assert body["skills_met"] == 1
    assert body["exam"]["attempted"] is False
    assert body["achieved_at"] is None


def test_exam_passed_but_skills_unmet_is_not_achieved(client, setup):
    """The two lines can disagree; that disagreement must stay visible."""
    token, sid = setup
    _set_goal(client, token, sid)
    _exam(sid, 90)
    body = client.get(f"/api/v1/courses/{COURSE}/goals?student_id={sid}", headers=_auth(token)).json()
    assert body["exam"]["passed"] is True
    assert body["exam"]["best_score"] == 90
    assert body["skills_met"] == 0
    assert body["achieved_at"] is None


def test_achieved_only_when_both_lines_are_satisfied(client, setup):
    token, sid = setup
    _set_goal(client, token, sid)
    _mastery(sid, "Circles", 90)
    _mastery(sid, "Probability", 75)
    _exam(sid, 88)
    body = client.get(f"/api/v1/courses/{COURSE}/goals?student_id={sid}", headers=_auth(token)).json()
    assert body["skills_met"] == body["skills_total"] == 2
    assert body["exam"]["passed"] is True
    assert body["achieved_at"] is not None


def test_best_exam_attempt_wins(client, setup):
    token, sid = setup
    _set_goal(client, token, sid)
    _exam(sid, 40)
    _exam(sid, 82)
    body = client.get(f"/api/v1/courses/{COURSE}/goals?student_id={sid}", headers=_auth(token)).json()
    assert body["exam"]["best_score"] == 82


def test_re_running_the_diagnostic_replaces_the_goal(client, setup):
    token, sid = setup
    first = _set_goal(client, token, sid).json()
    second = _set_goal(client, token, sid, target_skills=["Circles"], scope="full_course").json()
    assert first["id"] == second["id"], "should update in place, not stack a second goal"
    assert second["scope"] == "full_course"
    assert second["skills_total"] == 1


def test_full_course_scope_is_accepted(client, setup):
    token, sid = setup
    assert _set_goal(client, token, sid, scope="full_course").status_code == 201


def test_unknown_scope_rejected(client, setup):
    token, sid = setup
    assert _set_goal(client, token, sid, scope="whatever").status_code == 422


def test_cannot_set_a_goal_on_someone_elses_student(client, setup):
    _, sid = setup
    other = client.post("/api/v1/auth/register", json={
        "email": "other@test.com", "name": "O", "password": "hunter2pass"}).json()["access_token"]
    r = _set_goal(client, other, sid)
    assert r.status_code == 403


def test_goal_404s_before_one_is_set(client, setup):
    token, sid = setup
    r = client.get(f"/api/v1/courses/{COURSE}/goals?student_id={sid}", headers=_auth(token))
    assert r.status_code == 404
