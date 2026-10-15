import os

import pytest

from app import create_app
from app.backend import services
from app.backend.models import COORDINATOR, INSTRUCTOR, db


@pytest.fixture
def app():
    app = create_app({
        "TESTING": True,
        # Set TEST_DATABASE_URL to run the suite against PostgreSQL instead.
        "SQLALCHEMY_DATABASE_URI": os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"),
        "SECRET_KEY": "test",
        "COORDINATOR_CODE": "letmein",
        "WTF_CSRF_ENABLED": False,  # CSRF itself is covered in test_security.py
    })
    with app.app_context():
        yield app
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def coordinator(app):
    return services.register_user("coord", "secret123", COORDINATOR, "Coordinator")


@pytest.fixture
def instructor(app):
    return services.register_user("smith", "secret123", INSTRUCTOR, "Dr. Smith")


@pytest.fixture
def other_instructor(app):
    return services.register_user("jones", "secret123", INSTRUCTOR, "Dr. Jones")


def login(client, username):
    client.post("/login", data={"username": username, "password": "secret123"})
    return client


@pytest.fixture
def coord_client(client, coordinator):
    return login(client, "coord")


@pytest.fixture
def instructor_client(client, instructor):
    return login(client, "smith")


@pytest.fixture
def catalog(app, instructor, other_instructor):
    """Two rooms, a lab, and three courses."""
    services.create_room("Hall A", 100, "lecture_hall")
    services.create_room("Room B", 30, "small_room")
    services.create_room("Lab 1", 30, "lab")
    se = services.create_course("CS5551", "Software Engineering", 60, 2, 0, instructor.id)
    ml = services.create_course("CS5590", "Machine Learning", 25, 2, 1, other_instructor.id)
    db_ = services.create_course("CS5530", "Databases", 20, 1, 0, instructor.id)
    return {"se": se, "ml": ml, "db": db_}


@pytest.fixture
def published(catalog):
    schedule = services.generate_schedule("Fall 2026", "2026-08-24", "2026-12-11")
    return services.publish_schedule(schedule.id)
