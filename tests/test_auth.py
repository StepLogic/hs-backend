import pytest


def test_register_login_me(client):
    # Register
    r = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "secret123",
        "role": "student",
    })
    assert r.status_code == 201
    token = r.json()["access_token"]
    assert token
    assert r.json()["role"] == "student"

    # Me
    r2 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    assert r2.json()["email"] == "test@example.com"

    # Login
    r3 = client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "secret123",
    })
    assert r3.status_code == 200
    assert r3.json()["access_token"]


def test_register_duplicate_email(client):
    client.post("/api/v1/auth/register", json={
        "email": "dup@example.com",
        "password": "secret123",
        "role": "student",
    })
    r = client.post("/api/v1/auth/register", json={
        "email": "dup@example.com",
        "password": "secret123",
        "role": "student",
    })
    assert r.status_code == 409


def test_register_teacher_rejected(client):
    r = client.post("/api/v1/auth/register", json={
        "email": "teach@example.com",
        "password": "secret123",
        "role": "teacher",
    })
    assert r.status_code == 403


def test_me_without_auth(client):
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401
