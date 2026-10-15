"""Application factory for the course scheduling app.

A single Flask application (monolith) with two layers:
  backend/   models, business rules (services) and the scheduling algorithm
  frontend/  routes (blueprints), Jinja templates and static files
"""
import os

import click
from flask import Flask
from flask_wtf.csrf import CSRFProtect

from .backend.models import db
from .config import load_config

csrf = CSRFProtect()


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

    @app.cli.command("seed")
    def seed_command():
        """Fill the database with demo users, rooms and courses."""
        from .backend.seed import seed_demo
        seed_demo()
        click.echo("Demo data created. Log in as 'coord' or 'smith' "
                   "(password: DEMO_PASSWORD from .env).")

    with app.app_context():
        db.create_all()

    return app
