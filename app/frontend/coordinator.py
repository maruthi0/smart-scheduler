"""Coordinator pages: rooms, courses, constraints, schedule generation and editing."""
from datetime import date

from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from ..backend import services
from .auth import require_role
from ..backend.models import (
    COORDINATOR, PENDING, ROOM_TYPES, ChangeRequest, Course, NoOverlap, Room, Schedule,
)
from ..backend.services import DAYS, HOURS, ConflictError, SchedulingError, ValidationError

bp = Blueprint("coordinator", __name__, url_prefix="/coordinator")


@bp.before_request
def only_coordinators():
    return require_role(COORDINATOR)


def _run(action, success_message):
    """Run a service call, flashing the outcome. Returns the result or None."""
    try:
        result = action()
    except (ValidationError, ConflictError, SchedulingError) as e:
        flash(str(e), "error")
        return None
    flash(success_message, "success")
    return result if result is not None else True


def _back(page="dashboard"):
    return redirect(url_for(f"coordinator.{page}"))


def _warn_if_over_limit(course):
    """`course` is None when the save failed, and its instructor may be unassigned."""
    teacher = course and course.instructor
    if teacher and teacher.hours_left < 0:
        flash(f"{teacher.display_name} is now over their limit by {-teacher.hours_left} "
              "hour(s) a week.", "error")


@bp.get("/")
def dashboard():
    return render_template(
        "coordinator/dashboard.html",
        schedules=Schedule.query.order_by(Schedule.created_at.desc()).all(),
        pending=ChangeRequest.query.filter_by(status=PENDING).count(),
        today=date.today(),
    )


@bp.get("/rooms")
def rooms():
    return render_template(
        "coordinator/rooms.html",
        rooms=Room.query.order_by(Room.name).all(),
        room_types=ROOM_TYPES,
    )


@bp.get("/courses")
def courses():
    return render_template(
        "coordinator/courses.html",
        courses=Course.query.order_by(Course.code).all(),
        instructors=services.instructors(),
        rules=NoOverlap.query.all(),
    )


@bp.get("/workload")
def workload():
    return render_template("coordinator/workload.html", workloads=services.workloads())


@bp.get("/passwords")
def passwords():
    return render_template("coordinator/passwords.html", accounts=services.accounts())


# --- Rooms -----------------------------------------------------------------

@bp.post("/rooms")
def add_room():
    f = request.form
    _run(lambda: services.create_room(f.get("name"), f.get("capacity"), f.get("room_type")),
         "Room added.")
    return _back("rooms")


@bp.post("/rooms/<int:room_id>/delete")
def delete_room(room_id):
    _run(lambda: services.delete_room(room_id), "Room deleted.")
    return _back("rooms")


# --- Courses ---------------------------------------------------------------

@bp.post("/courses")
def add_course():
    f = request.form
    _warn_if_over_limit(_run(lambda: services.create_course(
        f.get("code"), f.get("title"), f.get("enrollment"), f.get("lecture_hours"),
        f.get("lab_hours"), f.get("instructor_id")), "Course added."))
    return _back("courses")


@bp.post("/courses/<int:course_id>/instructor")
def assign_instructor(course_id):
    _warn_if_over_limit(_run(
        lambda: services.assign_instructor(course_id, request.form.get("instructor_id")),
        "Instructor updated."))
    return _back("courses")


@bp.post("/courses/<int:course_id>/hours")
def set_course_hours(course_id):
    f = request.form
    _warn_if_over_limit(_run(
        lambda: services.set_course_hours(course_id, f.get("lecture_hours"), f.get("lab_hours")),
        "Hours updated."))
    return _back("courses")


@bp.post("/courses/<int:course_id>/delete")
def delete_course(course_id):
    _run(lambda: services.delete_course(course_id), "Course deleted.")
    return _back("courses")


@bp.post("/instructors/<int:user_id>/max-hours")
def set_max_hours(user_id):
    _run(lambda: services.set_max_hours(user_id, request.form.get("max_hours")),
         "Hour limit updated.")
    return _back("workload")


@bp.post("/accounts/<int:user_id>/reset-password")
def reset_password(user_id):
    try:
        account, temporary = services.reset_password(g.user, user_id)
    except ValidationError as e:
        flash(str(e), "error")
        return redirect(url_for("coordinator.passwords"))
    # Shown on this page only: a flash message would store it in the session cookie.
    return render_template("coordinator/temp_password.html", account=account, temporary=temporary)


# --- No-overlap rules ------------------------------------------------------

@bp.post("/rules")
def add_rule():
    f = request.form
    _run(lambda: services.add_no_overlap(f.get("course_a_id"), f.get("course_b_id")),
         "No-overlap rule added.")
    return _back("courses")


@bp.post("/rules/<int:rule_id>/delete")
def delete_rule(rule_id):
    _run(lambda: services.delete_no_overlap(rule_id), "Rule removed.")
    return _back("courses")


# --- Schedules -------------------------------------------------------------

@bp.post("/schedules")
def generate():
    f = request.form
    schedule = _run(lambda: services.generate_schedule(
        f.get("semester"), f.get("start_date"), f.get("end_date")), "Schedule generated.")
    if schedule:
        return redirect(url_for("coordinator.view_schedule", schedule_id=schedule.id))
    return _back()


@bp.get("/schedules/<int:schedule_id>")
def view_schedule(schedule_id):
    schedule = services.get_schedule(schedule_id)
    return render_template(
        "coordinator/schedule.html",
        schedule=schedule,
        grid=services.timetable_grid(schedule.sessions),
        soft=services.soft_report(schedule),
        rooms=Room.query.order_by(Room.name).all(),
        days=DAYS, hours=HOURS,
    )


@bp.post("/schedules/<int:schedule_id>/sessions/<int:session_id>/move")
def move_session(schedule_id, session_id):
    f = request.form
    _run(lambda: services.move_session(schedule_id, session_id, f.get("room_id"),
                                       f.get("day"), f.get("hour")), "Session moved.")
    return redirect(url_for("coordinator.view_schedule", schedule_id=schedule_id))


@bp.post("/schedules/<int:schedule_id>/publish")
def publish(schedule_id):
    _run(lambda: services.publish_schedule(schedule_id),
         "Schedule published. Instructors can now see it.")
    return redirect(url_for("coordinator.view_schedule", schedule_id=schedule_id))


@bp.post("/schedules/<int:schedule_id>/delete")
def delete_schedule(schedule_id):
    if _run(lambda: services.delete_schedule(schedule_id), "Schedule deleted."):
        return _back()
    return redirect(url_for("coordinator.view_schedule", schedule_id=schedule_id))


# --- Change requests -------------------------------------------------------

@bp.get("/requests")
def requests():
    return render_template(
        "coordinator/requests.html",
        requests=ChangeRequest.query.order_by(ChangeRequest.status != PENDING,
                                              ChangeRequest.created_at.desc()).all(),
        days=DAYS,
    )


@bp.post("/requests/<int:request_id>/respond")
def respond(request_id):
    f = request.form
    accept = f.get("decision") == "accept"
    _run(lambda: services.respond_change_request(request_id, accept, f.get("response")),
         "Request accepted." if accept else "Request rejected.")
    return redirect(url_for("coordinator.requests"))
