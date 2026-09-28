"""Registration is gated on an admin-issued, single-use invite code — both pipelines."""

import pytest

from app.config import settings
from tests import test_google_oauth


@pytest.fixture(autouse=True)
def _gate_on(monkeypatch):
    monkeypatch.setattr(settings, "REGISTRATION_INVITE_REQUIRED", True)


def _new_code(client, admin_token, note="Paid: Ada"):
    r = client.post(
        "/api/v1/invite-codes/", json={"note": note},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 201, r.text
    return r.json()["code"]


def _register(client, email, code=None):
    body = {"email": email, "password": "secret123", "role": "student"}
    if code is not None:
        body["invite_code"] = code
    return client.post("/api/v1/auth/register", json=body)


def test_only_admins_manage_codes(client, admin_token):
    assert client.post("/api/v1/invite-codes/", json={}).status_code == 401
    code = _new_code(client, admin_token)
    student = _register(client, "s@x.com", code).json()["access_token"]
    hdr = {"Authorization": f"Bearer {student}"}
    assert client.get("/api/v1/invite-codes/", headers=hdr).status_code == 403
    assert client.post("/api/v1/invite-codes/", json={}, headers=hdr).status_code == 403


def test_register_requires_a_valid_unused_code(client, admin_token):
    assert _register(client, "a@x.com").status_code == 403
    assert _register(client, "a@x.com", "NOPE").status_code == 403

    code = _new_code(client, admin_token)
    # typed loosely: lower case, dashes, spaces
    loose = " " + code[:5].lower() + "-" + code[5:] + " "
    assert _register(client, "a@x.com", loose).status_code == 201
    # single use
    assert _register(client, "b@x.com", code).status_code == 403

    rows = client.get(
        "/api/v1/invite-codes/", headers={"Authorization": f"Bearer {admin_token}"}
    ).json()
    assert rows[0]["used_by_email"] == "a@x.com" and rows[0]["used_at"]


def test_failed_signup_does_not_burn_the_code(client, admin_token):
    code = _new_code(client, admin_token)
    assert _register(client, "dup@x.com", code).status_code == 201
    code2 = _new_code(client, admin_token)
    assert _register(client, "dup@x.com", code2).status_code == 409
    assert _register(client, "fresh@x.com", code2).status_code == 201


def test_used_codes_cannot_be_deleted(client, admin_token):
    hdr = {"Authorization": f"Bearer {admin_token}"}
    code = _new_code(client, admin_token)
    spare = _new_code(client, admin_token)
    _register(client, "u@x.com", code)
    ids = {r["code"]: r["id"] for r in client.get("/api/v1/invite-codes/", headers=hdr).json()}
    assert client.delete(f"/api/v1/invite-codes/{ids[code]}", headers=hdr).status_code == 409
    assert client.delete(f"/api/v1/invite-codes/{ids[spare]}", headers=hdr).status_code == 200


def test_create_user_is_admin_only(client, admin_token):
    body = {"email": "c@x.com", "password": "secret123"}
    assert client.post("/api/v1/auth/create-user", json=body).status_code == 401
    r = client.post(
        "/api/v1/auth/create-user", json=body,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 201


# ── Google ──────────────────────────────────────────────────────────────

@pytest.fixture
def google(monkeypatch):
    for k, v in {
        "GOOGLE_CLIENT_ID": "test-client-id.apps.googleusercontent.com",
        "GOOGLE_CLIENT_SECRET": "s", "BACKEND_URL": "http://backend.test",
        "FRONTEND_URL": "http://frontend.test",
    }.items():
        monkeypatch.setattr(settings, k, v)


def _google(client, monkeypatch, email, code=None):
    """Same as test_google_oauth._sign_in, but passing an invite code on the way out."""
    import urllib.parse
    claims = {"aud": settings.GOOGLE_CLIENT_ID, "email_verified": "true", "email": email}
    test_google_oauth._stub_google(monkeypatch, claims)
    r = client.get("/api/v1/auth/google", params={"invite_code": code} if code else None)
    if r.status_code != 200:
        return r
    state = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(r.json()["url"]).query))["state"]
    client.cookies.set("hs-oauth-state", state)
    return client.get(
        "/api/v1/auth/google/callback", params={"code": "x", "state": state},
        follow_redirects=False,
    )


def test_google_new_account_without_code_is_sent_back_to_register(client, monkeypatch, google):
    r = _google(client, monkeypatch, "g@x.com")
    assert r.headers["location"].startswith("http://frontend.test/register#error=")
    from app import models
    from tests.conftest import TestingSessionLocal
    db = TestingSessionLocal()
    assert db.query(models.User).filter(models.User.email == "g@x.com").first() is None
    db.close()


def test_google_rejects_a_bad_code_before_leaving_for_google(client, monkeypatch, google):
    assert _google(client, monkeypatch, "g@x.com", "BADCODE").status_code == 403


def test_google_new_account_with_code_claims_it(client, monkeypatch, google, admin_token):
    code = _new_code(client, admin_token)
    r = _google(client, monkeypatch, "g@x.com", code)
    assert r.headers["location"].startswith("http://frontend.test/login#token=")
    # the code is spent
    assert _register(client, "other@x.com", code).status_code == 403


def test_google_existing_account_needs_no_code(client, monkeypatch, google, admin_token):
    _register(client, "back@x.com", _new_code(client, admin_token))
    r = _google(client, monkeypatch, "back@x.com")
    assert r.headers["location"].startswith("http://frontend.test/login#token=")
