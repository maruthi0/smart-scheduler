"""Database models."""
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()

COORDINATOR = "coordinator"
INSTRUCTOR = "instructor"
ROLES = (COORDINATOR, INSTRUCTOR)

ROOM_TYPES = ("theater", "lecture_hall", "small_room", "lab")
PERIODS = ("any", "morning", "afternoon")

DRAFT, PUBLISHED, ARCHIVED = "draft", "published", "archived"
PENDING, ACCEPTED, REJECTED = "pending", "accepted", "rejected"


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    full_name = db.Column(db.String(120), default="")
    role = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    courses = db.relationship("Course", back_populates="instructor")

    @property
    def display_name(self):
        return self.full_name or self.username

    @property
    def is_coordinator(self):
        return self.role == COORDINATOR

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    room_type = db.Column(db.String(20), nullable=False)


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    title = db.Column(db.String(120), nullable=False)
    enrollment = db.Column(db.Integer, nullable=False)
    lecture_hours = db.Column(db.Integer, nullable=False, default=3)
    lab_hours = db.Column(db.Integer, nullable=False, default=0)
    instructor_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    instructor = db.relationship("User", back_populates="courses")
    preference = db.relationship("CoursePreference", back_populates="course",
                                 uselist=False, cascade="all, delete-orphan")

    # The instructor's submitted hours override the coordinator's defaults.
    @property
    def effective_lecture_hours(self):
        return self.preference.lecture_hours if self.preference else self.lecture_hours

    @property
    def effective_lab_hours(self):
        return self.preference.lab_hours if self.preference else self.lab_hours


class NoOverlap(db.Model):
    """Hard constraint: two courses (e.g. same-cohort core courses) must not clash."""
    id = db.Column(db.Integer, primary_key=True)
    course_a_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    course_b_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)

    course_a = db.relationship("Course", foreign_keys=[course_a_id])
    course_b = db.relationship("Course", foreign_keys=[course_b_id])


class CoursePreference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), unique=True, nullable=False)
    lecture_hours = db.Column(db.Integer, nullable=False)
    lab_hours = db.Column(db.Integer, nullable=False)
    midterms = db.Column(db.Integer, nullable=False, default=1)
    final_exam = db.Column(db.Boolean, nullable=False, default=True)
    venue_type = db.Column(db.String(20))
    preferred_days = db.Column(db.String(20), default="")  # e.g. "0,2,4"
    preferred_period = db.Column(db.String(10), nullable=False, default="any")
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    course = db.relationship("Course", back_populates="preference")

    @property
    def days(self):
        return [int(d) for d in self.preferred_days.split(",") if d]


class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    semester = db.Column(db.String(40), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default=DRAFT)
    soft_penalty = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    sessions = db.relationship(
        "ScheduledSession", back_populates="schedule", cascade="all, delete-orphan",
        order_by="(ScheduledSession.day, ScheduledSession.hour)",
    )
    requests = db.relationship("ChangeRequest", back_populates="schedule",
                               cascade="all, delete-orphan")


class ScheduledSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey("schedule.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey("room.id"), nullable=False)
    day = db.Column(db.Integer, nullable=False)   # 0 = Monday
    hour = db.Column(db.Integer, nullable=False)  # start hour, 24h clock
    kind = db.Column(db.String(10), nullable=False)

    schedule = db.relationship("Schedule", back_populates="sessions")
    course = db.relationship("Course")
    room = db.relationship("Room")


class ChangeRequest(db.Model):
    """An instructor's suggestion to change the schedule. Only coordinators act on it."""
    id = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey("schedule.id"), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey("scheduled_session.id",
                                                     ondelete="SET NULL"))
    instructor_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default=PENDING)
    response = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    schedule = db.relationship("Schedule", back_populates="requests")
    session = db.relationship("ScheduledSession")
    instructor = db.relationship("User")
