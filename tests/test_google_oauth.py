"""Google OAuth: the redirect URI, the CSRF state, and the token-audience checks."""

import urllib.parse

import pytest

from app.config import settings


def _authorize_params(client):
    resp = client.get("/api/v1/auth/google")
    assert resp.status_code == 200, resp.text
    url = resp.json()["url"]
    return resp, dict(urllib.parse.parse_qsl(urllib.parse.urlparse(url).query))


@pytest.fixture(autouse=True)
def _configured(monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", "test-client-secret")
    monkeypatch.setattr(settings, "BACKEND_URL", "http://backend.test")
    monkeypatch.setattr(settings, "FRONTEND_URL", "http://frontend.test")


def test_redirect_uri_points_at_this_api_not_the_frontend(client):
    """It must hit the callback route on this service, or Google redirects into a 404."""
    _, params = _authorize_params(client)
    assert params["redirect_uri"] == "http://backend.test/api/v1/auth/google/callback"
    assert "frontend.test" not in params["redirect_uri"]


def test_authorize_sets_a_state_cookie_matching_the_state_param(client):
    resp, params = _authorize_params(client)
    assert params["state"]
    assert resp.cookies.get("hs-oauth-state") == params["state"]


def test_callback_rejects_a_missing_state(client):
    resp = client.get("/api/v1/auth/google/callback", params={"code": "x"})
    assert resp.status_code == 400
    assert "state" in resp.json()["detail"].lower()


def test_callback_rejects_a_forged_state(client):
    """A state we never issued must not be accepted — this is the CSRF defence."""
    client.cookies.set("hs-oauth-state", "attacker-supplied")
    resp = client.get(
        "/api/v1/auth/google/callback", params={"code": "x", "state": "attacker-supplied"}
    )
    assert resp.status_code == 400


def test_callback_rejects_a_token_minted_for_another_app(client, monkeypatch):
    """tokeninfo proves the token is well-formed, not that it was issued to us."""
    _, params = _authorize_params(client)
    client.cookies.set("hs-oauth-state", params["state"])

    import app.api.v1.endpoints.auth as auth_mod

    class _Resp:
        ok = True

        def __init__(self, payload):
            self._payload = payload

        def json(self):
            return self._payload

    monkeypatch.setattr(auth_mod.requests, "post", lambda *a, **k: _Resp({"id_token": "tok"}))
    monkeypatch.setattr(
        auth_mod.requests,
        "get",
        lambda *a, **k: _Resp(
            {"aud": "some-other-app.apps.googleusercontent.com",
             "email": "victim@example.com", "email_verified": "true"}
        ),
    )

    resp = client.get(
        "/api/v1/auth/google/callback",
        params={"code": "x", "state": params["state"]},
        follow_redirects=False,
    )
    assert resp.status_code == 400
    assert "not issued for this app" in resp.json()["detail"]


def test_callback_rejects_an_unverified_email(client, monkeypatch):
    """An unverified address must never match an existing account."""
    _, params = _authorize_params(client)
    client.cookies.set("hs-oauth-state", params["state"])

    import app.api.v1.endpoints.auth as auth_mod

    class _Resp:
        ok = True

        def __init__(self, payload):
            self._payload = payload

        def json(self):
            return self._payload

    monkeypatch.setattr(auth_mod.requests, "post", lambda *a, **k: _Resp({"id_token": "tok"}))
    monkeypatch.setattr(
        auth_mod.requests,
        "get",
        lambda *a, **k: _Resp(
            {"aud": settings.GOOGLE_CLIENT_ID,
             "email": "victim@example.com", "email_verified": "false"}
        ),
    )

    resp = client.get(
        "/api/v1/auth/google/callback",
        params={"code": "x", "state": params["state"]},
        follow_redirects=False,
    )
    assert resp.status_code == 400
    assert "not verified" in resp.json()["detail"].lower()


def test_happy_path_creates_a_user_and_redirects_with_a_token(client, monkeypatch):
    _, params = _authorize_params(client)
    client.cookies.set("hs-oauth-state", params["state"])

    import app.api.v1.endpoints.auth as auth_mod

    class _Resp:
        ok = True

        def __init__(self, payload):
            self._payload = payload

        def json(self):
            return self._payload

    monkeypatch.setattr(auth_mod.requests, "post", lambda *a, **k: _Resp({"id_token": "tok"}))
    monkeypatch.setattr(
        auth_mod.requests,
        "get",
        lambda *a, **k: _Resp(
            {"aud": settings.GOOGLE_CLIENT_ID,
             "email": "newuser@example.com", "name": "New User", "email_verified": "true"}
        ),
    )

    resp = client.get(
        "/api/v1/auth/google/callback",
        params={"code": "x", "state": params["state"]},
        follow_redirects=False,
    )
    assert resp.status_code in (302, 307), resp.text
    assert resp.headers["location"].startswith("http://frontend.test/login#token=")
