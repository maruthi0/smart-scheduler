"""US-16 Secure configuration: secrets from the environment, CSRF, cookie settings."""
import re

import pytest

from app import create_app
from app.backend import services
from app.backend.models import INSTRUCTOR, db

BASE = {"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"}


def _close(app):
    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


@pytest.fixture
def clean_env(monkeypatch):
    for name in ("SECRET_KEY", "COORDINATOR_CODE", "DEMO_PASSWORD", "SESSION_COOKIE_SECURE"):
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


@pytest.fixture
def csrf_app():
    app = create_app({**BASE, "SECRET_KEY": "test", "COORDINATOR_CODE": "letmein"})
    with app.app_context():
        services.register_user("smith", "secret123", INSTRUCTOR)
        yield app
    _close(app)


# AC 16.1
@pytest.mark.parametrize("missing", ["SECRET_KEY", "COORDINATOR_CODE"])
def test_app_refuses_to_start_without_required_secret(clean_env, missing):
    config = {**BASE, "SECRET_KEY": "test", "COORDINATOR_CODE": "letmein"}
    del config[missing]
    with pytest.raises(RuntimeError, match=missing):
        create_app(config)


def test_settings_are_read_from_environment(clean_env):
    clean_env.setenv("SECRET_KEY", "from-env")
    clean_env.setenv("COORDINATOR_CODE", "env-code")
    clean_env.setenv("SESSION_COOKIE_SECURE", "1")
    app = create_app(BASE)
    assert app.config["SECRET_KEY"] == "from-env"
    assert app.config["COORDINATOR_CODE"] == "env-code"
    assert app.config["SESSION_COOKIE_SECURE"] is True
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"
    _close(app)


def test_demo_accounts_use_password_from_config(clean_env):
    app = create_app({**BASE, "SECRET_KEY": "test", "COORDINATOR_CODE": "letmein",
                      "DEMO_PASSWORD": "demo-pass-1"})
    with app.app_context():
        app.test_cli_runner().invoke(args=["seed"])
        assert services.authenticate("coord", "demo-pass-1") is not None
        assert services.authenticate("coord", "password") is None
    _close(app)


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
