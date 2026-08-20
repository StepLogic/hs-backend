"""Account slice: composed /profiles/me read+write and password change."""


def _register(client, email="learner@test.com", password="hunter2pass"):
    r = client.post(
        "/api/v1/auth/register",
        json={"email": email, "name": "Alfred Johnson", "password": password},
    )
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_profile_me_composes_user_and_profile_rows(client):
    token = _register(client)
    r = client.get("/api/v1/profiles/me", headers=_auth(token))
    assert r.status_code == 200, r.text
    body = r.json()
    # from users
    assert body["name"] == "Alfred Johnson"
    assert body["email"] == "learner@test.com"
    # from user_profiles, with the defaults the settings toggles render
    assert body["theme"] == "system"
    assert body["notify_weekly_email"] is True
    assert body["notify_practice_tips"] is False
    assert body["display_name"] is None
    assert body["bio"] is None
    assert body["xp"] == 0


def test_profile_update_writes_through_to_both_tables(client):
    token = _register(client)
    r = client.put(
        "/api/v1/profiles/me",
        headers=_auth(token),
        json={
            "name": "Alfred J. Johnson",
            "display_name": "Alfred",
            "bio": "Working through Algebra II.",
            "theme": "dark",
            "notify_practice_tips": True,
        },
    )
    assert r.status_code == 200, r.text
    assert r.json()["name"] == "Alfred J. Johnson"

    body = client.get("/api/v1/profiles/me", headers=_auth(token)).json()
    assert body["name"] == "Alfred J. Johnson"
    assert body["display_name"] == "Alfred"
    assert body["bio"] == "Working through Algebra II."
    assert body["theme"] == "dark"
    assert body["notify_practice_tips"] is True
    # untouched fields survive a partial write
    assert body["notify_weekly_email"] is True


def test_profile_update_rejects_taken_email(client):
    token = _register(client)
    _register(client, email="taken@test.com")
    r = client.put(
        "/api/v1/profiles/me", headers=_auth(token), json={"email": "taken@test.com"}
    )
    assert r.status_code == 409
    # the address did not move
    assert client.get("/api/v1/profiles/me", headers=_auth(token)).json()["email"] == "learner@test.com"


def test_profile_update_keeps_own_email(client):
    token = _register(client)
    r = client.put(
        "/api/v1/profiles/me", headers=_auth(token), json={"email": "learner@test.com"}
    )
    assert r.status_code == 200


def test_guardian_fields_round_trip(client, admin_token):
    r = client.post(
        "/api/v1/students/",
        headers=_auth(admin_token),
        json={
            "name": "Alfred",
            "grade_level": 9,
            "guardian_name": "Marie Johnson",
            "guardian_email": "marie@test.com",
        },
    )
    assert r.status_code == 201, r.text
    student_id = r.json()["id"]
    assert r.json()["guardian_email"] == "marie@test.com"

    r = client.put(
        f"/api/v1/students/{student_id}",
        headers=_auth(admin_token),
        json={"guardian_name": "Marie J. Johnson"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["guardian_name"] == "Marie J. Johnson"
    assert r.json()["guardian_email"] == "marie@test.com"


def test_guardian_email_must_be_an_address(client, admin_token):
    r = client.post(
        "/api/v1/students/",
        headers=_auth(admin_token),
        json={"name": "Alfred", "grade_level": 9, "guardian_email": "not-an-email"},
    )
    assert r.status_code == 422


def test_change_password_then_login_with_it(client):
    token = _register(client)
    r = client.post(
        "/api/v1/auth/change-password",
        headers=_auth(token),
        json={"current_password": "hunter2pass", "new_password": "correcthorse"},
    )
    assert r.status_code == 204, r.text

    assert client.post(
        "/api/v1/auth/login", json={"email": "learner@test.com", "password": "hunter2pass"}
    ).status_code == 401
    assert client.post(
        "/api/v1/auth/login", json={"email": "learner@test.com", "password": "correcthorse"}
    ).status_code == 200


def test_change_password_rejects_wrong_current(client):
    token = _register(client)
    r = client.post(
        "/api/v1/auth/change-password",
        headers=_auth(token),
        json={"current_password": "wrongpassword", "new_password": "correcthorse"},
    )
    assert r.status_code == 400
    # old password still works
    assert client.post(
        "/api/v1/auth/login", json={"email": "learner@test.com", "password": "hunter2pass"}
    ).status_code == 200


def test_change_password_rejects_short_and_unchanged(client):
    token = _register(client)
    assert client.post(
        "/api/v1/auth/change-password",
        headers=_auth(token),
        json={"current_password": "hunter2pass", "new_password": "short"},
    ).status_code == 422
    assert client.post(
        "/api/v1/auth/change-password",
        headers=_auth(token),
        json={"current_password": "hunter2pass", "new_password": "hunter2pass"},
    ).status_code == 400


def test_change_password_refused_for_passwordless_google_account(client):
    from app import models
    from tests.conftest import TestingSessionLocal

    db = TestingSessionLocal()
    db.add(
        models.User(
            id="google-user-001",
            email="google@test.com",
            name="Google User",
            password_hash="",
            role=models.Role.STUDENT,
        )
    )
    db.commit()
    db.close()

    from app.security import create_access_token

    token = create_access_token("google-user-001", "student")
    r = client.post(
        "/api/v1/auth/change-password",
        headers=_auth(token),
        json={"current_password": "anything", "new_password": "correcthorse"},
    )
    assert r.status_code == 400
    assert "Google" in r.json()["detail"]


def test_change_password_requires_auth(client):
    r = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "hunter2pass", "new_password": "correcthorse"},
    )
    assert r.status_code in (401, 403)


# ── Password reset ─────────────────────────────────────────────────────


def _issue_reset(client, email="learner@test.com"):
    """Grab the token the way the email would carry it."""
    from unittest.mock import patch

    with patch("app.api.v1.endpoints.auth.send_password_reset") as sender:
        r = client.post("/api/v1/auth/password-reset/request", json={"email": email})
        assert r.status_code == 204, r.text
        if not sender.call_args:
            return None
        url = sender.call_args[0][1]
        return url.split("token=")[1]


def test_password_reset_end_to_end(client):
    _register(client)
    token = _issue_reset(client)
    assert token

    r = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": token, "new_password": "brandnewpass"},
    )
    assert r.status_code == 204, r.text

    assert client.post(
        "/api/v1/auth/login", json={"email": "learner@test.com", "password": "hunter2pass"}
    ).status_code == 401
    assert client.post(
        "/api/v1/auth/login", json={"email": "learner@test.com", "password": "brandnewpass"}
    ).status_code == 200


def test_reset_token_is_single_use(client):
    _register(client)
    token = _issue_reset(client)
    assert (
        client.post(
            "/api/v1/auth/password-reset/confirm",
            json={"token": token, "new_password": "brandnewpass"},
        ).status_code
        == 204
    )
    # replaying the same link must not work
    r = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": token, "new_password": "attackerpass"},
    )
    assert r.status_code == 400
    assert client.post(
        "/api/v1/auth/login", json={"email": "learner@test.com", "password": "brandnewpass"}
    ).status_code == 200


def test_reset_token_invalidated_by_a_password_change(client):
    token_str = _register(client)
    reset = _issue_reset(client)
    # user changes their password through the account screen instead
    assert (
        client.post(
            "/api/v1/auth/change-password",
            headers=_auth(token_str),
            json={"current_password": "hunter2pass", "new_password": "chosenbyme"},
        ).status_code
        == 204
    )
    assert (
        client.post(
            "/api/v1/auth/password-reset/confirm",
            json={"token": reset, "new_password": "attackerpass"},
        ).status_code
        == 400
    )


def test_reset_request_does_not_leak_whether_an_account_exists(client):
    _register(client)
    known = client.post(
        "/api/v1/auth/password-reset/request", json={"email": "learner@test.com"}
    )
    unknown = client.post(
        "/api/v1/auth/password-reset/request", json={"email": "nobody@test.com"}
    )
    assert known.status_code == unknown.status_code == 204
    assert known.content == unknown.content
    # and no mail goes to the stranger
    assert _issue_reset(client, "nobody@test.com") is None


def test_reset_rejects_garbage_and_foreign_tokens(client):
    import jwt as pyjwt

    _register(client)
    assert (
        client.post(
            "/api/v1/auth/password-reset/confirm",
            json={"token": "not-a-jwt", "new_password": "brandnewpass"},
        ).status_code
        == 400
    )
    # a validly-signed token minted for a different purpose must not reset a password
    from app.config import settings

    wrong_purpose = pyjwt.encode(
        {"sub": "x", "purpose": "google-oauth-state"},
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    assert (
        client.post(
            "/api/v1/auth/password-reset/confirm",
            json={"token": wrong_purpose, "new_password": "brandnewpass"},
        ).status_code
        == 400
    )
    # signed with the wrong key
    forged = pyjwt.encode(
        {"sub": "x", "purpose": "password-reset", "pwh": "0" * 16}, "wrong-key", algorithm="HS256"
    )
    assert (
        client.post(
            "/api/v1/auth/password-reset/confirm",
            json={"token": forged, "new_password": "brandnewpass"},
        ).status_code
        == 400
    )


def test_reset_token_expires(client):
    from datetime import datetime, timedelta, timezone
    import jwt as pyjwt
    from app.config import settings
    from app.api.v1.endpoints.auth import _password_fingerprint
    from app import crud
    from tests.conftest import TestingSessionLocal

    _register(client)
    db = TestingSessionLocal()
    user = crud.get_user_by_email(db, "learner@test.com")
    stale = pyjwt.encode(
        {
            "sub": str(user.id),
            "purpose": "password-reset",
            "pwh": _password_fingerprint(user.password_hash),
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        },
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    db.close()
    assert (
        client.post(
            "/api/v1/auth/password-reset/confirm",
            json={"token": stale, "new_password": "brandnewpass"},
        ).status_code
        == 400
    )


def test_reset_enforces_password_length(client):
    _register(client)
    token = _issue_reset(client)
    assert (
        client.post(
            "/api/v1/auth/password-reset/confirm",
            json={"token": token, "new_password": "short"},
        ).status_code
        == 422
    )
