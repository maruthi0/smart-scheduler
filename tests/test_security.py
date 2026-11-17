"""US-16 Secure configuration: secrets from the environment, CSRF, cookie settings."""
import pathlib
import re
import sqlite3
from datetime import datetime, timedelta

import pytest

from app import create_app
from app.backend import services
from app.backend.models import DEFAULT_MAX_HOURS, INSTRUCTOR, LoginAttempt, User, db
from tests.conftest import login

BASE = {"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"}


def _close(app):
    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


@pytest.fixture
def clean_env(monkeypatch):
    for name in ("SECRET_KEY", "DEMO_PASSWORD", "SESSION_COOKIE_SECURE"):
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


@pytest.fixture
def csrf_app():
    app = create_app({**BASE, "SECRET_KEY": "test"})
    with app.app_context():
        services.register_user("smith", "secret123", INSTRUCTOR)
        yield app
    _close(app)


# AC 16.1
def test_app_refuses_to_start_without_secret_key(clean_env):
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app(BASE)


def test_settings_are_read_from_environment(clean_env):
    clean_env.setenv("SECRET_KEY", "from-env")
    clean_env.setenv("SESSION_COOKIE_SECURE", "1")
    app = create_app(BASE)
    assert app.config["SECRET_KEY"] == "from-env"
    assert app.config["SESSION_COOKIE_SECURE"] is True
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"
    _close(app)


def test_demo_accounts_use_password_from_config(clean_env):
    app = create_app({**BASE, "SECRET_KEY": "test", "DEMO_PASSWORD": "demo-pass-1"})
    with app.app_context():
        app.test_cli_runner().invoke(args=["seed"])
        assert services.authenticate("coord", "demo-pass-1") is not None
        assert services.authenticate("coord", "password") is None
    _close(app)


def test_existing_database_gains_hour_limit_and_keeps_users(clean_env, tmp_path):
    path = tmp_path / "old.db"
    old = sqlite3.connect(path)
    old.execute('CREATE TABLE "user" (id INTEGER PRIMARY KEY, username VARCHAR(80) UNIQUE NOT NULL,'
                " full_name VARCHAR(120), role VARCHAR(20) NOT NULL,"
                " password_hash VARCHAR(255) NOT NULL, created_at DATETIME NOT NULL)")
    old.execute('INSERT INTO "user" (username, role, password_hash, created_at) VALUES'
                " ('old', 'instructor', 'x', '2026-01-01 00:00:00')")
    old.commit()
    old.close()
    config = {**BASE, "SECRET_KEY": "test",
              "SQLALCHEMY_DATABASE_URI": f"sqlite:///{path.as_posix()}"}
    app = create_app(config)
    create_app(config)  # a second start must not try to add the column again
    with app.app_context():
        user = User.query.one()
        assert (user.username, user.max_hours) == ("old", DEFAULT_MAX_HOURS)
        assert user.must_change_password is True
    _close(app)


# Login throttling
def _bad_login(client, username="smith"):
    return client.post("/login", data={"username": username, "password": "wrong-password"})


def test_login_locked_after_repeated_failures(client, instructor):
    for _ in range(services.MAX_LOGIN_FAILURES):
        assert b"Invalid username or password" in _bad_login(client).data
    resp = client.post("/login", data={"username": "smith", "password": "secret123"})
    assert resp.status_code == 429 and b"Too many failed attempts" in resp.data


def test_login_works_again_after_lockout_expires(client, instructor):
    for _ in range(services.MAX_LOGIN_FAILURES):
        _bad_login(client)
    attempt = db.session.get(LoginAttempt, "smith")
    attempt.last_failure = datetime.now() - services.LOGIN_LOCKOUT - timedelta(seconds=1)
    db.session.commit()
    resp = client.post("/login", data={"username": "smith", "password": "secret123"})
    assert resp.status_code == 302
    assert db.session.get(LoginAttempt, "smith") is None


def test_successful_login_clears_failures(client, instructor):
    for _ in range(services.MAX_LOGIN_FAILURES - 1):
        _bad_login(client)
    assert client.post("/login", data={"username": "smith",
                                       "password": "secret123"}).status_code == 302
    assert db.session.get(LoginAttempt, "smith") is None


def test_unknown_username_is_throttled_the_same_way(client, app):
    # Otherwise the different behaviour would reveal which usernames exist.
    for _ in range(services.MAX_LOGIN_FAILURES):
        assert b"Invalid username or password" in _bad_login(client, "nobody").data
    assert _bad_login(client, "nobody").status_code == 429


def test_old_failed_logins_are_removed(client, app):
    old = datetime.now() - services.LOGIN_LOCKOUT - timedelta(minutes=1)
    db.session.add(LoginAttempt(username="stale", failures=1, last_failure=old))
    db.session.commit()
    _bad_login(client, "fresh")
    assert db.session.get(LoginAttempt, "stale") is None


# Passwords
def _must_change(user):
    user.must_change_password = True
    db.session.commit()


def _change(client, current="secret123", new="a-new-password", confirm=None):
    return client.post("/password", data={"current_password": current, "new_password": new,
                                          "confirm_password": confirm or new},
                       follow_redirects=True)


def test_assigned_password_must_be_changed_before_anything_else(client, instructor):
    _must_change(instructor)
    login(client, "smith")
    assert "/password" in client.get("/instructor/").headers["Location"]
    assert client.post("/instructor/requests", data={}).status_code == 302
    assert client.get("/password").status_code == 200

    resp = _change(client)
    assert b"Your password was changed" in resp.data and b"My courses" in resp.data
    assert not instructor.must_change_password
    assert client.get("/instructor/").status_code == 200  # still logged in
    assert services.authenticate("smith", "a-new-password") == instructor


def test_can_log_out_during_forced_password_change(client, instructor):
    _must_change(instructor)
    login(client, "smith")
    assert "/login" in client.post("/logout").headers["Location"]


@pytest.mark.parametrize("current,new,confirm,message", [
    ("wrong-password", "a-new-password", None, b"current password is incorrect"),
    ("secret123", "short", None, b"10 to 128 characters"),
    ("secret123", "x" * 129, None, b"10 to 128 characters"),
    ("secret123", "a-new-password", "different-password", b"do not match"),
])
def test_change_password_validation(instructor_client, instructor, current, new, confirm, message):
    assert message in _change(instructor_client, current, new, confirm).data
    assert services.authenticate("smith", "secret123") == instructor


def test_new_password_must_differ(client, instructor):
    instructor.set_password("same-long-password")
    db.session.commit()
    client.post("/login", data={"username": "smith", "password": "same-long-password"})
    resp = _change(client, "same-long-password", "same-long-password")
    assert b"must be different" in resp.data


def test_password_page_requires_login(client):
    assert "/login" in client.get("/password").headers["Location"]


def test_changing_password_ends_other_sessions(app, instructor):
    first, second = login(app.test_client(), "smith"), login(app.test_client(), "smith")
    assert second.get("/instructor/").status_code == 200
    _change(first)
    assert first.get("/instructor/").status_code == 200
    assert "/login" in second.get("/instructor/").headers["Location"]


def test_locked_account_loses_its_open_session(instructor_client, instructor):
    assert instructor_client.get("/instructor/").status_code == 200
    services.sync_accounts([{"username": "boss", "password": "new-pass-2",
                             "role": "coordinator", "full_name": ""}])
    assert "/login" in instructor_client.get("/instructor/").headers["Location"]


# Coordinator password reset
def test_coordinator_resets_a_password(coord_client, instructor):
    resp = coord_client.post(f"/coordinator/accounts/{instructor.id}/reset-password")
    temporary = re.search(r'class="mono"><strong>([^<]+)<', resp.get_data(as_text=True)).group(1)
    assert services.authenticate("smith", "secret123") is None
    assert services.authenticate("smith", temporary) == instructor
    assert instructor.must_change_password
    assert resp.headers["Cache-Control"] == "no-store"


def test_coordinator_cannot_reset_own_or_locked_account(coord_client, coordinator, instructor):
    resp = coord_client.post(f"/coordinator/accounts/{coordinator.id}/reset-password",
                             follow_redirects=True)
    assert b"Use the Password page" in resp.data
    instructor.password_hash = "!"
    db.session.commit()
    resp = coord_client.post(f"/coordinator/accounts/{instructor.id}/reset-password",
                             follow_redirects=True)
    assert b"is locked" in resp.data
    assert instructor.is_locked


def test_instructor_cannot_reset_passwords(instructor_client, other_instructor):
    url = f"/coordinator/accounts/{other_instructor.id}/reset-password"
    assert instructor_client.post(url).status_code == 403
    assert services.authenticate("jones", "secret123") == other_instructor


# Headers and sessions
def test_security_headers(client, app):
    headers = client.get("/login").headers
    assert "script-src 'self'" in headers["Content-Security-Policy"]
    assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["Referrer-Policy"] == "same-origin"
    assert "Strict-Transport-Security" not in headers
    assert "Cache-Control" not in headers  # only pages for logged-in users are private


def test_https_only_header_when_served_over_https(client, app):
    app.config["SESSION_COOKIE_SECURE"] = True
    assert "max-age" in client.get("/login").headers["Strict-Transport-Security"]


def test_logged_in_pages_are_not_cached(instructor_client):
    assert instructor_client.get("/instructor/").headers["Cache-Control"] == "no-store"


def test_session_expires_after_idle_time(client, app, instructor):
    assert app.config["PERMANENT_SESSION_LIFETIME"] == timedelta(hours=2)
    resp = client.post("/login", data={"username": "smith", "password": "secret123"})
    assert "Expires=" in resp.headers["Set-Cookie"]


def test_templates_have_no_inline_scripts():
    # The Content-Security-Policy blocks these, so they would silently stop working.
    root = pathlib.Path(create_app.__code__.co_filename).parent / "frontend" / "templates"
    for path in root.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"\son[a-z]+=|<script(?![^>]*\bsrc=)|<style|\sstyle=", text), path


def test_delete_prompt_cannot_run_a_crafted_name(coord_client, app):
    services.create_room("x');alert(1);//", 10, "lab")
    page = coord_client.get("/coordinator/rooms").get_data(as_text=True)
    assert "onclick" not in page
    assert 'data-confirm="Delete x&#39;);alert(1);//?"' in page


# AC 16.2
def test_post_without_csrf_token_is_rejected(csrf_app):
    response = csrf_app.test_client().post(
        "/login", data={"username": "smith", "password": "secret123"})
    assert response.status_code == 400


def test_post_with_csrf_token_is_accepted(csrf_app):
    client = csrf_app.test_client()
    page = client.get("/login").get_data(as_text=True)
    token = re.search(r'name="csrf_token" value="([^"]+)"', page).group(1)
    response = client.post(
        "/login", data={"username": "smith", "password": "secret123", "csrf_token": token})
    assert response.status_code == 302
