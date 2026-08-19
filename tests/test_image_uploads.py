from fastapi.testclient import TestClient
from unittest.mock import patch


def test_create_student_persists_profile_image(client: TestClient, admin_token: str):
    r = client.post(
        "/api/v1/students/",
        json={"name": "Ada Lovelace", "grade_level": 5, "profile_image_url": "https://hs-platform.s3.us-east-005.backblazeb2.com/uploads/x/ada.png"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 201
    assert r.json()["profile_image_url"] == "https://hs-platform.s3.us-east-005.backblazeb2.com/uploads/x/ada.png"


def test_create_student_without_image_defaults_none(client: TestClient, admin_token: str):
    r = client.post(
        "/api/v1/students/",
        json={"name": "No Pic", "grade_level": 3},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 201
    assert r.json().get("profile_image_url") is None


def test_update_student_profile_image(client: TestClient, admin_token: str):
    create = client.post(
        "/api/v1/students/",
        json={"name": "Grace", "grade_level": 4},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    sid = create.json()["id"]
    r = client.put(
        f"/api/v1/students/{sid}",
        json={"profile_image_url": "https://hs-platform.s3.us-east-005.backblazeb2.com/uploads/x/grace.png"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 200
    assert r.json()["profile_image_url"] == "https://hs-platform.s3.us-east-005.backblazeb2.com/uploads/x/grace.png"


def test_create_course_persists_banner_image(client: TestClient):
    r = client.post(
        "/api/v1/courses/",
        json={
            "subject": "math", "course_type": "core", "title": "Algebra",
            "short_title": "Alg", "description": "x", "icon": "📐", "color": "#fff",
            "price": 0, "skills": [], "grade_range": "9-12", "features": [],
            "image_emoji": "📐", "banner_image_url": "https://hs-platform.s3.us-east-005.backblazeb2.com/uploads/x/alg.png",
        },
    )
    assert r.status_code in (200, 201)
    assert r.json()["banner_image_url"] == "https://hs-platform.s3.us-east-005.backblazeb2.com/uploads/x/alg.png"


def test_presign_returns_permanent_public_url(client: TestClient, admin_token: str):
    with patch(
        "app.api.v1.endpoints.uploads.generate_upload_url",
        return_value="https://signed.example/put",
    ):
        r = client.post(
            "/api/v1/uploads/presign?filename=photo.jpg&content_type=image/jpeg",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
    assert r.status_code == 200
    body = r.json()
    assert body["upload_url"] == "https://signed.example/put"
    # permanent public URL, not a presigned download URL
    assert body["public_url"].startswith("https://hs-platform.s3.us-east-005.backblazeb2.com/uploads/admin-user-001/")
    assert "X-Amz" not in body["public_url"]
    # uuid key — original filename must not appear verbatim
    assert "photo.jpg" not in body["public_url"]
    # but the extension is preserved
    assert body["public_url"].endswith(".jpg")


def test_presign_rejects_non_image(client: TestClient, admin_token: str):
    r = client.post(
        "/api/v1/uploads/presign?filename=data.json&content_type=application/json",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 400