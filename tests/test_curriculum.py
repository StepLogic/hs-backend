import pytest


def test_learning_path_prereq_lock(client, admin_token):
    client.headers["Authorization"] = f"Bearer {admin_token}"  # content writes are staff-only
    # Create course, unit, lessons
    r = client.post("/api/v1/courses/", json={
        "subject": "math",
        "title": "Algebra",
        "short_title": "Algebra",
        "description": "Algebra course",
        "icon": "calc",
        "color": "#3b82f6",
        "price": 0,
        "grade_range": "6-8",
        "image_emoji": "📐",
        "skills": ["equations"],
        "features": ["Lessons"],
    }, headers={"Authorization": f"Bearer {admin_token}"})
    course_id = r.json()["id"]

    r = client.post("/api/v1/units/", json={
        "course_id": course_id,
        "title": "Unit 1",
        "slug": "unit-1",
        "order_index": 0,
    }, headers={"Authorization": f"Bearer {admin_token}"})
    unit_id = r.json()["id"]

    r = client.post("/api/v1/lessons/", json={
        "unit_id": unit_id,
        "title": "Lesson 1",
        "slug": "lesson-1",
        "content": "# Lesson 1",
        "skills": ["equations"],
    }, headers={"Authorization": f"Bearer {admin_token}"})
    lesson1_id = r.json()["id"]

    r = client.post("/api/v1/lessons/", json={
        "unit_id": unit_id,
        "title": "Lesson 2",
        "slug": "lesson-2",
        "content": "# Lesson 2",
        "skills": ["equations"],
        "prerequisite_lesson_id": lesson1_id,
    }, headers={"Authorization": f"Bearer {admin_token}"})
    lesson2_id = r.json()["id"]

    # Create student (needs auth)
    rs = client.post("/api/v1/students/", json={"name": "Test", "grade_level": 8}, headers={"Authorization": f"Bearer {admin_token}"})
    student_id = rs.json()["id"]

    # Get learning path
    r = client.get(f"/api/v1/learning/path?student_id={student_id}&course_id={course_id}")
    assert r.status_code == 200
    path = r.json()
    assert len(path) == 1
    assert len(path[0]["lessons"]) == 2
    # Lesson 1 unlocked, Lesson 2 locked
    assert path[0]["lessons"][0]["locked"] == False
    assert path[0]["lessons"][1]["locked"] == True

    # Mark lesson 1 complete
    r = client.post("/api/v1/learning/progress", json={
        "student_id": student_id,
        "lesson_id": lesson1_id,
        "status": "completed",
        "mastery_score": 80,
    })
    assert r.status_code == 201

    # Get path again
    r = client.get(f"/api/v1/learning/path?student_id={student_id}&course_id={course_id}")
    path = r.json()
    assert path[0]["lessons"][1]["locked"] == False


def test_course_outline_matches_units_plus_their_lessons(client, admin_token):
    admin = {"Authorization": f"Bearer {admin_token}"}
    course = client.post("/api/v1/courses/", headers=admin, json={
        "subject": "math", "course_type": "core", "title": "Outline", "short_title": "O",
        "description": "d", "icon": "x", "color": "#000", "price": 0, "skills": [],
        "grade_range": "9-12", "features": [], "image_emoji": "x"}).json()
    units = [client.post("/api/v1/units/", headers=admin, json={
        "course_id": course["id"], "title": f"U{i}", "slug": f"u{i}", "order_index": i}).json() for i in (2, 1)]
    for u in units:
        for j in (1, 0):
            client.post("/api/v1/lessons/", headers=admin, json={
                "unit_id": u["id"], "title": f"{u['title']}-L{j}", "slug": f"{u['slug']}-l{j}", "order_index": j})

    outline = client.get(f"/api/v1/units/course/{course['id']}/outline").json()   # public, like the old calls
    assert [u["title"] for u in outline] == ["U1", "U2"]
    assert [l["title"] for l in outline[0]["lessons"]] == ["U1-L0", "U1-L1"]
    # same records the per-unit endpoint returns
    for u in outline:
        per_unit = client.get(f"/api/v1/lessons/unit/{u['id']}").json()
        assert sorted(per_unit, key=lambda l: l["id"]) == sorted(u["lessons"], key=lambda l: l["id"])
