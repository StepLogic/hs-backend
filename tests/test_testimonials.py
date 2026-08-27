QUOTE = "He broke every hard problem down step by step and my son is no longer afraid of math."


def test_public_submission_stays_unpublished(client):
    r = client.post("/api/v1/testimonials/", json={"quote": QUOTE, "name": "", "role": "Parent"})
    assert r.status_code == 201, r.text
    assert r.json()["published"] is False
    assert r.json()["name"] == "Anonymous"

    # Anonymous readers see nothing until an admin publishes it.
    assert client.get("/api/v1/testimonials/").json() == []


def test_admin_sees_pending_and_can_publish(client, admin_token):
    auth = {"Authorization": f"Bearer {admin_token}"}
    pending_id = client.post("/api/v1/testimonials/", json={"quote": QUOTE}).json()["id"]

    assert len(client.get("/api/v1/testimonials/", headers=auth).json()) == 1

    r = client.put(f"/api/v1/testimonials/{pending_id}", json={"published": True}, headers=auth)
    assert r.status_code == 200, r.text
    assert [t["id"] for t in client.get("/api/v1/testimonials/").json()] == [pending_id]


def test_admin_posts_published_and_deletes(client, admin_token):
    auth = {"Authorization": f"Bearer {admin_token}"}
    r = client.post("/api/v1/testimonials/", json={"quote": QUOTE, "published": True}, headers=auth)
    assert r.json()["published"] is True
    posted_id = r.json()["id"]

    assert client.delete(f"/api/v1/testimonials/{posted_id}").status_code == 401
    assert client.delete(f"/api/v1/testimonials/{posted_id}", headers=auth).status_code == 200
    assert client.get("/api/v1/testimonials/").json() == []
