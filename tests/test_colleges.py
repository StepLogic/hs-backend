import pytest
from fastapi.testclient import TestClient


def test_create_and_search_college(client: TestClient, admin_token: str):
    # Create a college
    r = client.post(
        "/api/v1/colleges/",
        json={
            "name": "Tech University",
            "location": "San Francisco, CA",
            "acceptance_rate": 0.12,
            "avg_sat": 1480,
            "avg_act": 33,
            "tuition_in_state": 42000,
            "tuition_out_state": 62000,
            "majors": ["Computer Science", "Engineering"],
            "tags": ["research", "urban"],
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Tech University"
    cid = data["id"]

    # Get by id
    r = client.get(f"/api/v1/colleges/{cid}")
    assert r.status_code == 200
    assert r.json()["name"] == "Tech University"

    # Search by name
    r = client.get("/api/v1/colleges/search?q=Tech")
    assert r.status_code == 200
    results = r.json()
    assert len(results) == 1
    assert results[0]["name"] == "Tech University"

    # Search by SAT range
    r = client.get("/api/v1/colleges/search?sat_min=1400&sat_max=1500")
    assert r.status_code == 200
    results = r.json()
    assert len(results) == 1

    # Search by SAT range that excludes
    r = client.get("/api/v1/colleges/search?sat_min=1500")
    assert r.status_code == 200
    assert len(r.json()) == 0

    # Search by major
    r = client.get("/api/v1/colleges/search?major=Computer%20Science")
    assert r.status_code == 200
    results = r.json()
    assert len(results) == 1

    # Search by tag
    r = client.get("/api/v1/colleges/search?tags=research")
    assert r.status_code == 200
    results = r.json()
    assert len(results) == 1


def test_get_college_not_found(client: TestClient):
    r = client.get("/api/v1/colleges/nonexistent-id")
    assert r.status_code == 404


def test_create_college_unauthorized(client: TestClient):
    r = client.post(
        "/api/v1/colleges/",
        json={"name": "Bad", "location": "Nowhere"},
    )
    assert r.status_code == 401
