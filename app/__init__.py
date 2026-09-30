"""Application factory for the course scheduling app."""
import os

import click
from flask import Flask

from .models import db
from .services import NotFoundError, PermissionDenied


def create_app(config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-change-me"),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL",
            "sqlite:///" + os.path.join(app.instance_path, "scheduler.db"),
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        # Registering as a coordinator requires this code, so any visitor
        # cannot give themselves permission to edit schedules.
        COORDINATOR_CODE=os.environ.get("COORDINATOR_CODE", "coordinator-demo"),
    )
    if config:
        app.config.update(config)

    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)

    from .auth import bp as auth_bp
    from .coordinator import bp as coordinator_bp
    from .instructor import bp as instructor_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(coordinator_bp)
    app.register_blueprint(instructor_bp)

    app.register_error_handler(NotFoundError, lambda e: (str(e), 404))
    app.register_error_handler(PermissionDenied, lambda e: (str(e), 403))

    @app.cli.command("seed")
    def seed_command():
        """Fill the database with demo users, rooms and courses."""
        from .seed import seed_demo
        seed_demo()
        click.echo("Demo data created. Log in as 'coord' or 'smith' (password: password).")

    with app.app_context():
        db.create_all()

    return app
