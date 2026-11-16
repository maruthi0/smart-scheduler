"""Application factory for the course scheduling app.

A single Flask application (monolith) with two layers:
  backend/   models, business rules (services) and the scheduling algorithm
  frontend/  routes (blueprints), Jinja templates and static files
"""
import csv
import os

import click
from flask import Flask, current_app, g
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import inspect, text

from .backend.models import DEFAULT_MAX_HOURS, db
from .config import load_config

csrf = CSRFProtect()


NEW_USER_COLUMNS = {
    "max_hours": f"INTEGER NOT NULL DEFAULT {DEFAULT_MAX_HOURS}",
    # TRUE: existing accounts may hold passwords shared in a file, so they must choose their own.
    "must_change_password": "BOOLEAN NOT NULL DEFAULT TRUE",
}

CONTENT_SECURITY_POLICY = (
    "default-src 'self'; script-src 'self'; style-src 'self' https://fonts.googleapis.com; "
    "font-src https://fonts.gstatic.com; img-src 'self' data:; object-src 'none'; "
    "base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
)


def _add_missing_columns():
    # shortcut: create_all never alters existing tables and there are no migrations;
    # move to Alembic if the schema keeps changing.
    existing = {c["name"] for c in inspect(db.engine).get_columns("user")}
    for name, definition in NEW_USER_COLUMNS.items():
        if name not in existing:
            db.session.execute(text(f'ALTER TABLE "user" ADD COLUMN {name} {definition}'))
    db.session.commit()


def _add_security_headers(response):
    response.headers["Content-Security-Policy"] = CONTENT_SECURITY_POLICY
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    if current_app.config["SESSION_COOKIE_SECURE"]:  # served over HTTPS
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
    if g.get("user"):
        response.headers["Cache-Control"] = "no-store"  # Back button must not reveal pages after logout
    return response


def create_app(config=None):
    app = Flask(__name__, instance_relative_config=True,
                template_folder="frontend/templates", static_folder="frontend/static")
    load_config(app, config)

    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)
    csrf.init_app(app)

    from .frontend.auth import bp as auth_bp
    from .frontend.coordinator import bp as coordinator_bp
    from .frontend.instructor import bp as instructor_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(coordinator_bp)
    app.register_blueprint(instructor_bp)

    from .frontend.errors import register_error_pages
    register_error_pages(app)

    app.after_request(_add_security_headers)

    @app.cli.command("seed")
    def seed_command():
        """Fill the database with demo users, rooms and courses."""
        from .backend.seed import seed_demo
        seed_demo()
        click.echo("Demo data created. Log in as 'coord' or 'smith' "
                   "(password: DEMO_PASSWORD from .env).")

    @app.cli.command("load-accounts")
    @click.argument("path", default="usernames&passwords.csv",
                    type=click.Path(exists=True, dir_okay=False))
    @click.option("--reset-passwords", is_flag=True,
                  help="Also replace the passwords of existing accounts with the file's.")
    def load_accounts_command(path, reset_passwords):
        """Make the accounts file the only logins. Accounts not listed are locked."""
        from .backend import services
        # utf-8-sig: Excel adds a byte-order mark when it saves a CSV.
        with open(path, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        try:
            locked = services.sync_accounts(rows, reset_passwords)
        except services.ValidationError as e:
            raise click.ClickException(str(e))
        click.echo(f"Loaded {len(rows)} account(s). Locked: {', '.join(locked) or 'none'}.")

    def read_csv(path, required):
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            missing = [column for column in required if column not in (reader.fieldnames or [])]
            if missing:
                raise click.ClickException(
                    f"CSV is missing required column(s): {', '.join(missing)}.")
            return list(reader)

    @app.cli.command("import-instructors")
    @click.argument("path", type=click.Path(exists=True, dir_okay=False))
    def import_instructors_command(path):
        """Add or update instructors from a CSV file."""
        from .backend import services
        try:
            rows = read_csv(path, ("username", "password", "full_name", "max_hours"))
            users = services.import_instructors(rows)
        except services.ValidationError as e:
            raise click.ClickException(str(e))
        click.echo(f"Imported {len(users)} instructor(s).")

    @app.cli.command("import-rooms")
    @click.argument("path", type=click.Path(exists=True, dir_okay=False))
    def import_rooms_command(path):
        """Add or update rooms from a CSV file."""
        from .backend import services
        try:
            rows = read_csv(path, ("name", "capacity", "room_type"))
            rooms = services.import_rooms(rows)
        except services.ValidationError as e:
            raise click.ClickException(str(e))
        click.echo(f"Imported {len(rooms)} room(s).")

    @app.cli.command("import-courses")
    @click.argument("path", type=click.Path(exists=True, dir_okay=False))
    def import_courses_command(path):
        """Add or update courses from a CSV file."""
        from .backend import services
        try:
            rows = read_csv(path, ("code", "title", "enrollment", "lecture_hours",
                                   "lab_hours", "instructor_username"))
            courses = services.import_courses(rows)
        except services.ValidationError as e:
            raise click.ClickException(str(e))
        click.echo(f"Imported {len(courses)} course(s).")

    with app.app_context():
        db.create_all()
        _add_missing_columns()

    return app
