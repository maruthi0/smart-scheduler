"""Business logic. Routes stay thin and delegate here; the timetabling
algorithm itself lives in scheduler.py and knows nothing about the database."""
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone

from . import scheduler
from .models import (
    ACCEPTED, ARCHIVED, DRAFT, INSTRUCTOR, PENDING, PERIODS, PUBLISHED, REJECTED, ROLES,
    ROOM_TYPES, ChangeRequest, Course, CoursePreference, NoOverlap, Room, Schedule,
    ScheduledSession, User, db,
)
from .scheduler import DAYS, HOURS, SchedulingError  # noqa: F401 (re-exported)

MAX_HOURS_PER_WEEK = 10


class ValidationError(Exception):
    """Input violates a business rule."""


class NotFoundError(Exception):
    """Requested record does not exist."""


class PermissionDenied(Exception):
    """User may not act on this record."""


class ConflictError(Exception):
    """A manual schedule change would break a hard constraint."""

    def __init__(self, reasons):
        self.reasons = reasons
        super().__init__("; ".join(reasons))


# --- Input helpers ---------------------------------------------------------

def _get(model, obj_id):
    obj = db.session.get(model, obj_id) if obj_id is not None else None
    if obj is None:
        raise NotFoundError(f"{model.__name__} {obj_id} not found.")
    return obj


def _int(value, name, minimum=0, maximum=None):
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{name} must be a whole number.")
    if maximum is None and number < minimum:
        raise ValidationError(f"{name} must be at least {minimum}.")
    if maximum is not None and not minimum <= number <= maximum:
        raise ValidationError(f"{name} must be between {minimum} and {maximum}.")
    return number


def _text(value, name, max_length, required=True):
    text = (value or "").strip()
    if required and not text:
        raise ValidationError(f"{name} is required.")
    if len(text) > max_length:
        raise ValidationError(f"{name} must be at most {max_length} characters.")
    return text


def _date(value, name):
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{name} must be a valid date.")


# --- Users -----------------------------------------------------------------

def register_user(username, password, role, full_name=""):
    username = (username or "").strip()
    if len(username) < 3:
        raise ValidationError("Username must be at least 3 characters.")
    if len(password or "") < 6:
        raise ValidationError("Password must be at least 6 characters.")
    if role not in ROLES:
        raise ValidationError("Choose a valid role.")
    if User.query.filter_by(username=username).first():
        raise ValidationError("Username is already taken.")
    user = User(username=username, role=role,
                full_name=_text(full_name, "Full name", 120, required=False))
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def authenticate(username, password):
    user = User.query.filter_by(username=(username or "").strip()).first()
    if user and user.check_password(password or ""):
        return user
    return None


def instructors():
    return User.query.filter_by(role=INSTRUCTOR).order_by(User.full_name, User.username).all()


# --- Rooms, courses and constraints (coordinator) --------------------------

def create_room(name, capacity, room_type):
    name = _text(name, "Room name", 60)
    capacity = _int(capacity, "Capacity", 1, 2000)
    if room_type not in ROOM_TYPES:
        raise ValidationError("Choose a valid room type.")
    if Room.query.filter_by(name=name).first():
        raise ValidationError(f"A room named {name} already exists.")
    room = Room(name=name, capacity=capacity, room_type=room_type)
    db.session.add(room)
    db.session.commit()
    return room


def delete_room(room_id):
    room = _get(Room, room_id)
    if ScheduledSession.query.filter_by(room_id=room.id).first():
        raise ValidationError(f"{room.name} is used in a schedule; delete that schedule first.")
    db.session.delete(room)
    db.session.commit()


def _instructor_or_none(instructor_id):
    if instructor_id in (None, ""):
        return None
    user = _get(User, _int(instructor_id, "Instructor"))
    if user.role != INSTRUCTOR:
        raise ValidationError(f"{user.display_name} is not an instructor.")
    return user


def create_course(code, title, enrollment, lecture_hours=3, lab_hours=0, instructor_id=None):
    code = _text(code, "Course code", 20).upper()
    title = _text(title, "Course title", 120)
    enrollment = _int(enrollment, "Enrollment", 1, 2000)
    lecture_hours = _int(lecture_hours, "Lecture hours", 0, MAX_HOURS_PER_WEEK)
    lab_hours = _int(lab_hours, "Lab hours", 0, MAX_HOURS_PER_WEEK)
    if lecture_hours + lab_hours == 0:
        raise ValidationError("A course needs at least one lecture or lab hour.")
    if Course.query.filter_by(code=code).first():
        raise ValidationError(f"Course {code} already exists.")
    course = Course(code=code, title=title, enrollment=enrollment, lecture_hours=lecture_hours,
                    lab_hours=lab_hours, instructor=_instructor_or_none(instructor_id))
    db.session.add(course)
    db.session.commit()
    return course


def assign_instructor(course_id, instructor_id):
    course = _get(Course, course_id)
    course.instructor = _instructor_or_none(instructor_id)
    db.session.commit()
    return course


def delete_course(course_id):
    course = _get(Course, course_id)
    if ScheduledSession.query.filter_by(course_id=course.id).first():
        raise ValidationError(f"{course.code} is used in a schedule; delete that schedule first.")
    NoOverlap.query.filter((NoOverlap.course_a_id == course.id)
                           | (NoOverlap.course_b_id == course.id)).delete()
    db.session.delete(course)
    db.session.commit()


def add_no_overlap(course_a_id, course_b_id):
    a = _get(Course, _int(course_a_id, "First course"))
    b = _get(Course, _int(course_b_id, "Second course"))
    if a.id == b.id:
        raise ValidationError("Choose two different courses.")
    low, high = sorted((a.id, b.id))
    if NoOverlap.query.filter_by(course_a_id=low, course_b_id=high).first():
        raise ValidationError(f"{a.code} and {b.code} are already marked as no-overlap.")
    rule = NoOverlap(course_a_id=low, course_b_id=high)
    db.session.add(rule)
    db.session.commit()
    return rule


def delete_no_overlap(rule_id):
    db.session.delete(_get(NoOverlap, rule_id))
    db.session.commit()


# --- Instructor preferences ------------------------------------------------

def instructor_course(instructor, course_id):
    course = _get(Course, course_id)
    if course.instructor_id != instructor.id:
        raise PermissionDenied(f"You do not teach {course.code}.")
    return course


def save_preference(instructor, course_id, data):
    course = instructor_course(instructor, course_id)
    lecture_hours = _int(data.get("lecture_hours"), "Lecture hours", 0, MAX_HOURS_PER_WEEK)
    lab_hours = _int(data.get("lab_hours"), "Lab hours", 0, MAX_HOURS_PER_WEEK)
    if lecture_hours + lab_hours == 0:
        raise ValidationError("A course needs at least one lecture or lab hour.")
    midterms = _int(data.get("midterms", 0), "Number of midterms", 0, 5)
    venue = data.get("venue_type") or None
    if venue is not None and (venue not in ROOM_TYPES or venue == "lab"):
        raise ValidationError("Choose a valid venue type.")
    period = data.get("preferred_period") or "any"
    if period not in PERIODS:
        raise ValidationError("Choose a valid time of day.")
    days = sorted({_int(d, "Preferred day", 0, len(DAYS) - 1)
                   for d in data.get("preferred_days") or []})

    pref = course.preference or CoursePreference(course=course)
    pref.lecture_hours = lecture_hours
    pref.lab_hours = lab_hours
    pref.midterms = midterms
    pref.final_exam = str(data.get("final_exam", "")).lower() in ("on", "true", "1", "yes")
    pref.venue_type = venue
    pref.preferred_days = ",".join(map(str, days))
    pref.preferred_period = period
    db.session.add(pref)
    db.session.commit()
    return pref


# --- Schedule generation and editing ---------------------------------------

def _room_spec(room):
    return scheduler.RoomSpec(room.id, room.name, room.capacity, room.room_type)


def _session_spec(course, kind, index):
    pref = course.preference
    return scheduler.SessionSpec(
        course_id=course.id, course_code=course.code, kind=kind, index=index,
        enrollment=course.enrollment, instructor_id=course.instructor_id,
        venue_pref=pref.venue_type if pref else None,
        preferred_days=frozenset(pref.days) if pref else frozenset(),
        preferred_period=pref.preferred_period if pref else "any",
    )


def _no_overlap_pairs():
    return {frozenset((r.course_a_id, r.course_b_id)) for r in NoOverlap.query}


def build_problem():
    sessions = []
    for course in Course.query.order_by(Course.id):
        sessions += [_session_spec(course, "lecture", i)
                     for i in range(course.effective_lecture_hours)]
        sessions += [_session_spec(course, "lab", i) for i in range(course.effective_lab_hours)]
    rooms = [_room_spec(r) for r in Room.query.order_by(Room.id)]
    return scheduler.Problem(rooms, sessions, _no_overlap_pairs())


def generate_schedule(semester, start_date, end_date):
    semester = _text(semester, "Semester", 40)
    start_date = _date(start_date, "Start date")
    end_date = _date(end_date, "End date")
    if end_date <= start_date:
        raise ValidationError("End date must be after start date.")
    problem = build_problem()
    if not problem.sessions:
        raise ValidationError("Add at least one course before generating a schedule.")

    result = scheduler.generate(problem)  # raises SchedulingError if infeasible

    schedule = Schedule(semester=semester, start_date=start_date, end_date=end_date,
                        status=DRAFT, soft_penalty=result.penalty)
    for p in result.placements:
        schedule.sessions.append(ScheduledSession(
            course_id=p.session.course_id, room_id=p.room.id,
            day=p.day, hour=p.hour, kind=p.session.kind))
    db.session.add(schedule)
    db.session.commit()
    return schedule


def get_schedule(schedule_id):
    return _get(Schedule, schedule_id)


def _placement(session):
    # The DB id is used as the spec index so every placement is distinct.
    return scheduler.Placement(_session_spec(session.course, session.kind, session.id),
                               _room_spec(session.room), session.day, session.hour)


def _timetable(schedule, exclude_id=None):
    timetable = scheduler.Timetable(_no_overlap_pairs())
    for s in schedule.sessions:
        if s.id != exclude_id:
            timetable.add(_placement(s))
    return timetable


def soft_report(schedule):
    """{session id: [unmet preference, ...]} for the given schedule."""
    report = scheduler.evaluate_soft(_timetable(schedule))
    return {p.session.index: reasons for p, reasons in report.items()}


def move_session(schedule_id, session_id, room_id, day, hour):
    schedule = _get(Schedule, schedule_id)
    session = _get(ScheduledSession, session_id)
    if session.schedule_id != schedule.id:
        raise NotFoundError(f"Session {session_id} is not in this schedule.")
    room = _get(Room, _int(room_id, "Room"))
    day = _int(day, "Day", 0, len(DAYS) - 1)
    hour = _int(hour, "Hour", HOURS[0], HOURS[-1])

    reasons = _timetable(schedule, exclude_id=session.id).hard_violations(
        _session_spec(session.course, session.kind, session.id), _room_spec(room), day, hour)
    if reasons:
        raise ConflictError(reasons)

    session.room, session.day, session.hour = room, day, hour
    db.session.flush()
    schedule.soft_penalty = sum(len(r) for r in soft_report(schedule).values())
    db.session.commit()
    return session


def publish_schedule(schedule_id):
    schedule = _get(Schedule, schedule_id)
    for other in Schedule.query.filter_by(status=PUBLISHED):
        other.status = ARCHIVED
    schedule.status = PUBLISHED
    db.session.commit()
    return schedule


def delete_schedule(schedule_id):
    schedule = _get(Schedule, schedule_id)
    if schedule.status == PUBLISHED:
        raise ValidationError("A published schedule cannot be deleted.")
    db.session.delete(schedule)
    db.session.commit()


def published_schedule():
    return Schedule.query.filter_by(status=PUBLISHED).first()


def instructor_sessions(instructor, schedule):
    return [s for s in schedule.sessions if s.course.instructor_id == instructor.id]


def timetable_grid(sessions):
    grid = defaultdict(list)
    for s in sessions:
        grid[(s.day, s.hour)].append(s)
    return grid


# --- Change requests -------------------------------------------------------

def create_change_request(instructor, session_id, message):
    schedule = published_schedule()
    if schedule is None:
        raise ValidationError("There is no published schedule to comment on.")
    message = _text(message, "Message", 1000)
    session = None
    if session_id not in (None, ""):
        session = _get(ScheduledSession, _int(session_id, "Session"))
        if session.schedule_id != schedule.id:
            raise NotFoundError(f"Session {session_id} is not in the published schedule.")
        if session.course.instructor_id != instructor.id:
            raise PermissionDenied("You can only request changes to your own sessions.")
    request = ChangeRequest(schedule=schedule, session=session, instructor=instructor,
                            message=message)
    db.session.add(request)
    db.session.commit()
    return request


def respond_change_request(request_id, accept, response=""):
    request = _get(ChangeRequest, request_id)
    if request.status != PENDING:
        raise ValidationError("This request has already been answered.")
    request.status = ACCEPTED if accept else REJECTED
    request.response = _text(response, "Response", 1000, required=False)
    db.session.commit()
    return request


# --- Calendar export -------------------------------------------------------

def _ics_text(value):
    return (value.replace("\\", "\\\\").replace(";", "\\;")
            .replace(",", "\\,").replace("\n", "\\n"))


def instructor_calendar(instructor, schedule):
    """iCalendar (.ics) feed of the instructor's weekly sessions for the semester.

    Google Calendar, Outlook and Apple Calendar can all import this file.
    """
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    until = schedule.end_date.strftime("%Y%m%dT235959")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//CS5551 Scheduler//EN",
             "CALSCALE:GREGORIAN", f"X-WR-CALNAME:{_ics_text(schedule.semester)} teaching"]
    for s in instructor_sessions(instructor, schedule):
        offset = (s.day - schedule.start_date.weekday()) % 7
        start = datetime.combine(schedule.start_date + timedelta(days=offset), time(s.hour))
        end = start + timedelta(hours=1)
        lines += [
            "BEGIN:VEVENT",
            f"UID:session-{s.id}-schedule-{schedule.id}@cs5551-scheduler",
            f"DTSTAMP:{stamp}",
            f"DTSTART:{start:%Y%m%dT%H%M%S}",
            f"DTEND:{end:%Y%m%dT%H%M%S}",
            f"RRULE:FREQ=WEEKLY;UNTIL={until}",
            f"SUMMARY:{_ics_text(s.course.code)} {s.kind.title()}",
            f"LOCATION:{_ics_text(s.room.name)}",
            f"DESCRIPTION:{_ics_text(s.course.title)}",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"
