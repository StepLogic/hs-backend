import pytest
from datetime import datetime, timedelta


def test_tutor_meeting_crud(client, admin_token):
    # Create a student profile owned by the admin user
    rs = client.post("/api/v1/students/", json={"name": "Tutee", "grade_level": 9, "owner_user_id": "admin-user-001"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert rs.status_code == 201
    student_id = rs.json()["id"]

    # Create a course
    rc = client.post("/api/v1/courses/", json={
        "subject": "math",
        "course_type": "core",
        "title": "Algebra Basics",
        "short_title": "Algebra",
        "description": "Learn algebra",
        "icon": "📐",
        "color": "#3b82f6",
        "price": 0,
        "skills": ["algebra"],
        "grade_range": "9-12",
        "lesson_count": 0,
        "student_count": 0,
        "rating": 0,
        "review_count": 0,
        "features": ["Videos"],
        "image_emoji": "📐"
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert rc.status_code == 201
    course_id = rc.json()["id"]

    # Create meeting request
    r = client.post("/api/v1/tutor/meetings", json={
        "student_id": student_id,
        "course_id": course_id,
        "topic": "Quadratic equations",
        "scheduled_at": (datetime.utcnow() + timedelta(days=1)).isoformat(),
        "duration_min": 45,
        "student_notes": "Need help with factoring"
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 201
    meeting = r.json()
    assert meeting["topic"] == "Quadratic equations"
    assert meeting["status"] == "requested"
    assert meeting["student_id"] == student_id
    meeting_id = meeting["id"]

    # List meetings (admin sees all)
    r2 = client.get("/api/v1/tutor/meetings", headers={"Authorization": f"Bearer {admin_token}"})
    assert r2.status_code == 200
    meetings = r2.json()
    assert any(m["id"] == meeting_id for m in meetings)

    # Get meeting detail
    r3 = client.get(f"/api/v1/tutor/meetings/{meeting_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert r3.status_code == 200
    detail = r3.json()
    assert detail["id"] == meeting_id

    # Tutor schedules the meeting
    r4 = client.put(f"/api/v1/tutor/meetings/{meeting_id}", json={
        "tutor_id": "admin-user-001",
        "status": "scheduled",
        "meeting_url": "https://zoom.us/j/123456"
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert r4.status_code == 200
    updated = r4.json()
    assert updated["status"] == "scheduled"
    assert updated["meeting_url"] == "https://zoom.us/j/123456"
    assert updated["tutor_id"] == "admin-user-001"

    # Cancel the meeting
    r5 = client.delete(f"/api/v1/tutor/meetings/{meeting_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert r5.status_code == 204

    # Verify deleted
    r6 = client.get(f"/api/v1/tutor/meetings/{meeting_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert r6.status_code == 404


def test_tutor_meeting_student_view(client, admin_token):
    # Create student user and profile
    ru = client.post("/api/v1/auth/register", json={"email": "student@test.com", "password": "student123", "name": "Student"})
    assert ru.status_code == 201
    student_user = ru.json()
    student_user_id = student_user["user_id"]
    student_token = student_user["access_token"]

    # Register auto-creates a student profile; fetch it
    rs = client.get("/api/v1/students/", headers={"Authorization": f"Bearer {student_token}"})
    assert rs.status_code == 200
    students = rs.json()
    assert len(students) >= 1
    student_id = students[0]["id"]

    # Create course
    rc = client.post("/api/v1/courses/", json={
        "subject": "english_language_arts",
        "course_type": "core",
        "title": "Essay Writing",
        "short_title": "Essays",
        "description": "Write better essays",
        "icon": "✍️",
        "color": "#10b981",
        "price": 0,
        "skills": ["writing"],
        "grade_range": "9-12",
        "lesson_count": 0,
        "student_count": 0,
        "rating": 0,
        "review_count": 0,
        "features": ["Practice"],
        "image_emoji": "✍️"
    }, headers={"Authorization": f"Bearer {admin_token}"})
    course_id = rc.json()["id"]

    # Student creates meeting for their own profile
    r = client.post("/api/v1/tutor/meetings", json={
        "student_id": student_id,
        "course_id": course_id,
        "topic": "Thesis statements"
    }, headers={"Authorization": f"Bearer {student_token}"})
    assert r.status_code == 201
    meeting_id = r.json()["id"]

    # Student can list their own meetings
    r2 = client.get("/api/v1/tutor/meetings", headers={"Authorization": f"Bearer {student_token}"})
    assert r2.status_code == 200
    assert any(m["id"] == meeting_id for m in r2.json())

    # Student can cancel their own meeting
    r3 = client.delete(f"/api/v1/tutor/meetings/{meeting_id}", headers={"Authorization": f"Bearer {student_token}"})
    assert r3.status_code == 204


def test_tutor_meeting_unauthorized(client, admin_token):
    # Create two students
    rs1 = client.post("/api/v1/students/", json={"name": "A", "grade_level": 9, "owner_user_id": "admin-user-001"}, headers={"Authorization": f"Bearer {admin_token}"})
    student_a = rs1.json()["id"]

    rs2 = client.post("/api/v1/students/", json={"name": "B", "grade_level": 9}, headers={"Authorization": f"Bearer {admin_token}"})
    student_b = rs2.json()["id"]

    rc = client.post("/api/v1/courses/", json={
        "subject": "science",
        "course_type": "core",
        "title": "Biology",
        "short_title": "Bio",
        "description": "Life science",
        "icon": "🧬",
        "color": "#8b5cf6",
        "price": 0,
        "skills": ["biology"],
        "grade_range": "9-12",
        "lesson_count": 0,
        "student_count": 0,
        "rating": 0,
        "review_count": 0,
        "features": ["Labs"],
        "image_emoji": "🧬"
    }, headers={"Authorization": f"Bearer {admin_token}"})
    course_id = rc.json()["id"]

    # Create meeting for student A
    r = client.post("/api/v1/tutor/meetings", json={
        "student_id": student_a,
        "course_id": course_id,
        "topic": "Cell division"
    }, headers={"Authorization": f"Bearer {admin_token}"})
    meeting_id = r.json()["id"]

    # Student B (no token, anonymous) cannot access meeting A
    # Since no auth, they get 401 on list
    r2 = client.get("/api/v1/tutor/meetings")
    assert r2.status_code == 401

    # Anonymous cannot update
    r3 = client.put(f"/api/v1/tutor/meetings/{meeting_id}", json={"status": "scheduled"})
    assert r3.status_code == 401
