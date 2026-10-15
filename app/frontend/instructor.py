"""Instructor pages: preferences, read-only timetable, change requests, calendar."""
from flask import Blueprint, Response, flash, g, redirect, render_template, request, url_for

from ..backend import services
from .auth import require_role
from ..backend.models import INSTRUCTOR, PERIODS, ROOM_TYPES, ChangeRequest, Course
from ..backend.services import DAYS, HOURS, ValidationError

bp = Blueprint("instructor", __name__, url_prefix="/instructor")


@bp.before_request
def only_instructors():
    return require_role(INSTRUCTOR)


@bp.get("/")
def dashboard():
    schedule = services.published_schedule()
    return render_template(
        "instructor/dashboard.html",
        courses=Course.query.filter_by(instructor_id=g.user.id).order_by(Course.code).all(),
        schedule=schedule,
        sessions=services.instructor_sessions(g.user, schedule) if schedule else [],
        my_requests=ChangeRequest.query.filter_by(instructor_id=g.user.id)
                                       .order_by(ChangeRequest.created_at.desc()).all(),
        days=DAYS,
    )


@bp.route("/courses/<int:course_id>/preferences", methods=["GET", "POST"])
def preferences(course_id):
    course = services.instructor_course(g.user, course_id)
    if request.method == "POST":
        data = request.form.to_dict()
        data["preferred_days"] = request.form.getlist("preferred_days")
        try:
            services.save_preference(g.user, course_id, data)
        except ValidationError as e:
            flash(str(e), "error")
        else:
            flash(f"Preferences for {course.code} saved.", "success")
            return redirect(url_for("instructor.dashboard"))
    return render_template("instructor/preferences.html", course=course, pref=course.preference,
                           days=DAYS, periods=PERIODS,
                           venues=[t for t in ROOM_TYPES if t != "lab"])


@bp.get("/schedule")
def schedule():
    published = services.published_schedule()
    return render_template(
        "instructor/schedule.html",
        schedule=published,
        grid=services.timetable_grid(published.sessions) if published else {},
        days=DAYS, hours=HOURS,
    )


@bp.post("/requests")
def create_request():
    try:
        services.create_change_request(g.user, request.form.get("session_id"),
                                       request.form.get("message"))
    except ValidationError as e:
        flash(str(e), "error")
    else:
        flash("Change request sent to the coordinators.", "success")
    return redirect(url_for("instructor.dashboard"))


@bp.get("/calendar.ics")
def calendar():
    published = services.published_schedule()
    if published is None:
        flash("There is no published schedule yet.", "error")
        return redirect(url_for("instructor.dashboard"))
    return Response(
        services.instructor_calendar(g.user, published),
        mimetype="text/calendar",
        headers={"Content-Disposition": "attachment; filename=teaching-schedule.ics"},
    )
