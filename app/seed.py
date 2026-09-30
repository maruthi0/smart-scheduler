"""Demo data for development and the sprint demonstration video."""
from .models import COORDINATOR, INSTRUCTOR, Course, User, db
from . import services

DEMO_PASSWORD = "password"


def seed_demo():
    if User.query.first():
        raise SystemExit("Database is not empty; delete instance/scheduler.db first.")

    services.register_user("coord", DEMO_PASSWORD, COORDINATOR, "Dr. Rivera (Coordinator)")
    smith = services.register_user("smith", DEMO_PASSWORD, INSTRUCTOR, "Dr. Smith")
    jones = services.register_user("jones", DEMO_PASSWORD, INSTRUCTOR, "Dr. Jones")
    lee = services.register_user("lee", DEMO_PASSWORD, INSTRUCTOR, "Dr. Lee")

    for name, capacity, kind in [
        ("Haag 201 Theater", 200, "theater"),
        ("Flarsheim 310", 80, "lecture_hall"),
        ("Flarsheim 312", 60, "lecture_hall"),
        ("Royall 105", 30, "small_room"),
        ("Linda Hall Lab A", 40, "lab"),
        ("Linda Hall Lab B", 30, "lab"),
    ]:
        services.create_room(name, capacity, kind)

    courses = {}
    for code, title, enrollment, lectures, labs, teacher in [
        ("CS5551", "Advanced Software Engineering", 70, 3, 0, smith),
        ("CS5565", "Networks", 55, 3, 0, jones),
        ("CS5590", "Machine Learning", 150, 3, 0, lee),
        ("CS5520", "Mobile Computing", 35, 2, 2, smith),
        ("CS5592", "Algorithms", 60, 3, 0, jones),
        ("CS5530", "Databases", 28, 2, 1, lee),
    ]:
        courses[code] = services.create_course(code, title, enrollment, lectures, labs,
                                               teacher.id)

    services.add_no_overlap(courses["CS5551"].id, courses["CS5592"].id)
    services.add_no_overlap(courses["CS5565"].id, courses["CS5590"].id)

    services.save_preference(smith, courses["CS5551"].id, {
        "lecture_hours": 3, "lab_hours": 0, "midterms": 1, "final_exam": "on",
        "venue_type": "lecture_hall", "preferred_days": [0, 2, 4],
        "preferred_period": "morning"})
    services.save_preference(lee, courses["CS5590"].id, {
        "lecture_hours": 3, "lab_hours": 0, "midterms": 2, "final_exam": "on",
        "venue_type": "theater", "preferred_days": [1, 3], "preferred_period": "afternoon"})
    db.session.commit()
    return Course.query.count()
