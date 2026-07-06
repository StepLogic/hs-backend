from fastapi.testclient import TestClient


def test_generate_personalized_course_from_weak_tags(client: TestClient, admin_token: str):
    """POST personalized should create a course with only weak-tag units."""
    # ponytail: stub tables so Better Auth fallback doesn't crash
    from tests.conftest import TestingSessionLocal
    from sqlalchemy import text
    db = TestingSessionLocal()
    db.execute(text("CREATE TABLE IF NOT EXISTS session (token TEXT, \"userId\" TEXT, \"expiresAt\" TIMESTAMP)"))
    db.execute(text("CREATE TABLE IF NOT EXISTS \"user\" (id TEXT PRIMARY KEY, name TEXT, email TEXT)"))
    db.commit()

    from app import models

    # Seed course with tagged units
    course = models.Course(
        id="test-pc-course-001",
        title="PC Test Course",
        short_title="PC Test",
        description="Personalized course test",
        subject=models.Subject.MATH,
        course_type=models.CourseType.CORE,
        icon="📚",
        color="#000",
        price=0,
        grade_range="9-12",
        image_emoji="📚",
        features=[],
        skills=[],
    )
    db.add(course)
    db.commit()

    unit_alg = models.Unit(id="pc-unit-alg", course_id="test-pc-course-001", title="Algebra", slug="algebra", order_index=0, description="algebra")
    unit_geo = models.Unit(id="pc-unit-geo", course_id="test-pc-course-001", title="Geometry", slug="geometry", order_index=1, description="geometry")
    unit_stats = models.Unit(id="pc-unit-stats", course_id="test-pc-course-001", title="Statistics", slug="statistics", order_index=2, description="statistics")
    db.add_all([unit_alg, unit_geo, unit_stats])
    db.commit()
    db.close()

    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {
        "student_id": "student-001",
        "weak_tags": ["algebra", "statistics"],
    }
    r = client.post(
        "/api/v1/courses/test-pc-course-001/personalized",
        json=payload,
        headers=headers,
    )
    assert r.status_code == 201
    data = r.json()
    assert data["status"] == "draft"
    assert len(data["unit_ids"]) == 2
    # Should only include algebra and statistics units
    unit_ids = set(data["unit_ids"])
    assert "pc-unit-alg" in unit_ids
    assert "pc-unit-stats" in unit_ids
    assert "pc-unit-geo" not in unit_ids
