import pytest
from datetime import date, timedelta


def test_study_plan_crud(client, admin_token):
    # Create student
    rs = client.post("/api/v1/students/", json={"name": "Plan Student", "grade_level": 10}, headers={"Authorization": f"Bearer {admin_token}"})
    assert rs.status_code == 201
    student_id = rs.json()["id"]

    # Create plan with items
    r = client.post("/api/v1/plans", json={
        "student_id": student_id,
        "title": "SAT Prep",
        "start_date": str(date.today()),
        "end_date": str(date.today() + timedelta(days=30)),
        "target_exam": "SAT",
        "items": [
            {"title": "Algebra Review", "description": "Review basics", "due_date": str(date.today()), "status": "scheduled"},
            {"title": "Geometry Review", "description": "Review shapes", "due_date": str(date.today() + timedelta(days=1)), "status": "scheduled"},
        ]
    })
    assert r.status_code == 201
    plan = r.json()
    assert plan["title"] == "SAT Prep"
    assert len(plan["items"]) == 2
    plan_id = plan["id"]

    # List plans by student
    r2 = client.get(f"/api/v1/plans/student/{student_id}")
    assert r2.status_code == 200
    plans = r2.json()
    assert len(plans) == 1
    assert plans[0]["id"] == plan_id

    # Get plan detail
    r3 = client.get(f"/api/v1/plans/{plan_id}")
    assert r3.status_code == 200
    detail = r3.json()
    assert detail["id"] == plan_id
    assert len(detail["items"]) == 2

    # Update item status
    item_id = detail["items"][0]["id"]
    r4 = client.put(f"/api/v1/plans/{plan_id}/items/{item_id}", json={"status": "completed"})
    assert r4.status_code == 200
    updated_item = r4.json()
    assert updated_item["status"] == "completed"

    # Verify reflected in plan
    r5 = client.get(f"/api/v1/plans/{plan_id}")
    assert r5.status_code == 200
    assert r5.json()["items"][0]["status"] == "completed"


def test_generate_plan(client, admin_token):
    # Create student and diagnostic
    rs = client.post("/api/v1/students/", json={"name": "Gen Student", "grade_level": 11}, headers={"Authorization": f"Bearer {admin_token}"})
    student_id = rs.json()["id"]

    # Create diagnostic result with skill gaps
    client.post("/api/v1/diagnostics", json={
        "student_id": student_id,
        "subject": "math",
        "grade_level_equivalent": 10,
        "skill_gaps": [{"skill": "algebra"}, {"skill": "geometry"}],
        "recommended_courses": []
    }, headers={"Authorization": f"Bearer {admin_token}"})

    target = date.today() + timedelta(days=14)
    r = client.post("/api/v1/plans/generate", json={
        "student_id": student_id,
        "target_exam": "SAT",
        "target_exam_date": str(target)
    })
    assert r.status_code == 201
    plan = r.json()
    assert plan["title"] == "SAT Study Plan"
    assert plan["student_id"] == student_id
    assert len(plan["items"]) >= 1


def test_plan_not_found(client):
    r = client.get("/api/v1/plans/nonexistent-id")
    assert r.status_code == 404
