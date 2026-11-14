"""Settings read from environment variables. Copy .env.example to .env to set them."""
import os
from datetime import timedelta

REQUIRED = ("SECRET_KEY",)


def _flag(name):
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes", "on")


def _with_driver(url):
    """Use the psycopg 3 driver for PostgreSQL URLs (SQLAlchemy defaults to psycopg2)."""
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


def load_config(app, overrides=None):
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY"),
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL")
        or "sqlite:///" + os.path.join(app.instance_path, "scheduler.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        # Password given to the demo accounts created by `flask --app run seed`.
        DEMO_PASSWORD=os.environ.get("DEMO_PASSWORD") or "password",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=2),  # logged out after 2 idle hours
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=_flag("SESSION_COOKIE_SECURE"),
    )
    if overrides:
        app.config.update(overrides)
    app.config["SQLALCHEMY_DATABASE_URI"] = _with_driver(app.config["SQLALCHEMY_DATABASE_URI"])

    missing = [name for name in REQUIRED if not app.config.get(name)]
    if missing:
        raise RuntimeError(f"Missing required setting(s): {', '.join(missing)}. "
                           "Copy .env.example to .env and fill them in.")
