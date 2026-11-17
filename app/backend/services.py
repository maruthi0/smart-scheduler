"""Business logic. Routes stay thin and delegate here; the timetabling
algorithm itself lives in scheduler.py and knows nothing about the database."""
import secrets
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone

from . import scheduler
from .models import (
    ACCEPTED, ARCHIVED, DEFAULT_MAX_HOURS, DRAFT, INSTRUCTOR, LOCKED_HASH, PENDING, PERIODS, PUBLISHED, REJECTED,
    ROLES, ROOM_TYPES, ChangeRequest, Course, CoursePreference, LoginAttempt, NoOverlap, Room,
    Schedule, ScheduledSession, Unavailability, User, db,
)
from .scheduler import DAYS, HOURS, SchedulingError  # noqa: F401 (re-exported)

MAX_HOURS_PER_WEEK = 10
MAX_LOGIN_FAILURES = 5
LOGIN_LOCKOUT = timedelta(minutes=15)
PASSWORD_LENGTHS = (10, 128)


class ValidationError(Exception):
    """Input violates a business rule."""


class NotFoundError(Exception):
    """Requested record does not exist."""


class PermissionDenied(Exception):
    """User may not act on this record."""


class TooManyAttempts(Exception):
    """Too many failed logins for this username."""


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

def _valid_account(username, password, role):
    username = (username or "").strip()
    if len(username) < 3:
        raise ValidationError("Username must be at least 3 characters.")
    if len(password or "") < 6:
        raise ValidationError("Password must be at least 6 characters.")
    if role not in ROLES:
        raise ValidationError("Choose a valid role.")
    return username


def register_user(username, password, role, full_name=""):
    username = _valid_account(username, password, role)
    if User.query.filter_by(username=username).first():
        raise ValidationError("Username is already taken.")
    user = User(username=username, role=role,
                full_name=_text(full_name, "Full name", 120, required=False))
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def authenticate(username, password):
    """Return the user, or None if the login is wrong. Raises TooManyAttempts when throttled."""
    # shortcut: counts per username, so someone can briefly lock out a known username;
    # also count per client address if that becomes a problem.
    username = (username or "").strip()[:80]
    now = datetime.now()
    attempt = db.session.get(LoginAttempt, username)
    if attempt and now - attempt.last_failure >= LOGIN_LOCKOUT:
        attempt.failures = 0
    if attempt and attempt.failures >= MAX_LOGIN_FAILURES:
        raise TooManyAttempts("Too many failed attempts. Try again in 15 minutes.")

    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password or ""):
        if attempt:
            db.session.delete(attempt)
            db.session.commit()
        return user

    # Old rows are removed here so guessing random usernames cannot grow the table forever.
    LoginAttempt.query.filter(LoginAttempt.last_failure < now - LOGIN_LOCKOUT,
                              LoginAttempt.username != username).delete()
    if attempt is None:
        attempt = LoginAttempt(username=username, failures=0)
        db.session.add(attempt)
    attempt.failures += 1
    attempt.last_failure = now
    db.session.commit()
    return None


def change_password(user, current, new, confirm):
    if not user.check_password(current or ""):
        raise ValidationError("Your current password is incorrect.")
    low, high = PASSWORD_LENGTHS
    if not low <= len(new or "") <= high:
        raise ValidationError(f"The new password must be {low} to {high} characters long.")
    if new != confirm:
        raise ValidationError("The two new passwords do not match.")
    if new == current:
        raise ValidationError("The new password must be different from the current one.")
    user.set_password(new)
    user.must_change_password = False
    db.session.commit()


def accounts():
    return (User.query.filter(User.password_hash != LOCKED_HASH)
            .order_by(User.role, User.username).all())


def reset_password(coordinator, user_id):
    """Give an account a temporary password. Returns (user, temporary password)."""
    user = _get(User, user_id)
    if user.id == coordinator.id:
        raise ValidationError("Use the Password page to change your own password.")
    if user.is_locked:
        raise ValidationError(f"{user.username} is locked. Add them to the accounts file instead.")
    temporary = secrets.token_urlsafe(12)
    user.set_password(temporary)
    user.must_change_password = True
    db.session.commit()
    return user, temporary


def sync_accounts(rows, reset_passwords=False):
    """Make these rows the only accounts that can log in. Returns the usernames locked.

    Existing accounts keep the password they chose unless reset_passwords is set.
    """
    listed = {_valid_account(r.get("username"), r.get("password"), r.get("role")) for r in rows}
    if not listed:
        raise ValidationError("The accounts file lists no accounts.")
    for row in rows:
        username = row["username"].strip()
        user = User.query.filter_by(username=username).first()
        is_new = user is None
        if is_new:
            user = User(username=username)
            db.session.add(user)
        user.role = row["role"]
        user.full_name = _text(row.get("full_name"), "Full name", 120, required=False)
        if is_new or reset_passwords or user.is_locked:
            user.set_password(row["password"])
            user.must_change_password = True
    locked = User.query.filter(User.username.notin_(listed)).order_by(User.username).all()
    for user in locked:
        user.password_hash = LOCKED_HASH  # their courses and history stay intact
    db.session.commit()
    return [user.username for user in locked]


def import_instructors(rows):
    rows = list(rows)
    if not rows:
        raise ValidationError("The instructors file lists no instructors.")
    usernames = set()
    users = []
    for row in rows:
        username = _valid_account(row.get("username"), row.get("password"), INSTRUCTOR)
        if username in usernames:
            raise ValidationError(f"Username {username} appears more than once.")
        usernames.add(username)
        full_name = _text(row.get("full_name"), "Full name", 120, required=False)
        max_hours = _int(row.get("max_hours") or DEFAULT_MAX_HOURS,
                         "Hour limit", 0, 60)
        user = User.query.filter_by(username=username).first()
        if user is not None and user.role != INSTRUCTOR:
            raise ValidationError(f"{username} is not an instructor.")
        users.append((user, username, row.get("password"), full_name, max_hours))
    for user, username, password, full_name, max_hours in users:
        if user is None:  # existing accounts keep their own password and lock, as in load-accounts
            user = User(username=username, role=INSTRUCTOR)
            user.set_password(password)
            user.must_change_password = True
            db.session.add(user)
        user.full_name = full_name
        user.max_hours = max_hours
    db.session.commit()
    return [User.query.filter_by(username=username).one() for _, username, *_ in users]


def import_rooms(rows):
    rows = list(rows)
    if not rows:
        raise ValidationError("The rooms file lists no rooms.")
    names = set()
    rooms = []
    for row in rows:
        name = _text(row.get("name"), "Room name", 60)
        if name in names:
            raise ValidationError(f"Room {name} appears more than once.")
        names.add(name)
        capacity = _int(row.get("capacity"), "Capacity", 1, 2000)
        room_type = row.get("room_type")
        if room_type not in ROOM_TYPES:
            raise ValidationError("Choose a valid room type.")
        room = Room.query.filter_by(name=name).first()
        rooms.append((room, name, capacity, room_type))
    for room, name, capacity, room_type in rooms:
        if room is None:
            room = Room(name=name, capacity=capacity, room_type=room_type)
            db.session.add(room)
        else:
            room.capacity = capacity
            room.room_type = room_type
    db.session.commit()
    return [Room.query.filter_by(name=name).one() for _, name, *_ in rooms]


def import_courses(rows):
    rows = list(rows)
    if not rows:
        raise ValidationError("The courses file lists no courses.")
    codes = set()
    courses = []
    for row in rows:
        code = _text(row.get("code"), "Course code", 20).upper()
        if code in codes:
            raise ValidationError(f"Course {code} appears more than once.")
        codes.add(code)
        title = _text(row.get("title"), "Course title", 120)
        enrollment = _int(row.get("enrollment"), "Enrollment", 1, 2000)
        lecture_hours, lab_hours = _hours(row.get("lecture_hours") or 0,
                                          row.get("lab_hours") or 0)
        username = (row.get("instructor_username") or "").strip()
        instructor = None
        if username:
            instructor = User.query.filter_by(username=username).first()
            if instructor is None or instructor.role != INSTRUCTOR:
                raise ValidationError(f"{username} is not an instructor.")
        course = Course.query.filter_by(code=code).first()
        courses.append((course, code, title, enrollment, lecture_hours, lab_hours, instructor))
    for course, code, title, enrollment, lecture_hours, lab_hours, instructor in courses:
        if course is None:
            course = Course(code=code)
            db.session.add(course)
        course.title = title
        course.enrollment = enrollment
        course.lecture_hours = lecture_hours
        course.lab_hours = lab_hours
        course.instructor = instructor
    db.session.commit()
    return [Course.query.filter_by(code=code).one() for _, code, *_ in courses]


def instructors():
    return User.query.filter_by(role=INSTRUCTOR).order_by(User.full_name, User.username).all()


def workloads():
    return [{"user": user, "assigned": user.assigned_hours, "left": user.hours_left}
            for user in instructors()]


def set_max_hours(user_id, max_hours):
    user = _instructor_or_none(user_id)
    user.max_hours = _int(max_hours, "Hour limit", 0, 60)
    db.session.commit()
    return user


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


def _hours(lecture_hours, lab_hours):
    lecture_hours = _int(lecture_hours, "Lecture hours", 0, MAX_HOURS_PER_WEEK)
    lab_hours = _int(lab_hours, "Lab hours", 0, MAX_HOURS_PER_WEEK)
    if lecture_hours + lab_hours == 0:
        raise ValidationError("A course needs at least one lecture or lab hour.")
    return lecture_hours, lab_hours


def create_course(code, title, enrollment, lecture_hours=3, lab_hours=0, instructor_id=None):
    code = _text(code, "Course code", 20).upper()
    title = _text(title, "Course title", 120)
    enrollment = _int(enrollment, "Enrollment", 1, 2000)
    lecture_hours, lab_hours = _hours(lecture_hours, lab_hours)
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


def set_course_hours(course_id, lecture_hours, lab_hours):
    course = _get(Course, course_id)
    course.lecture_hours, course.lab_hours = _hours(lecture_hours, lab_hours)
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
    pref.midterms = midterms
    pref.final_exam = str(data.get("final_exam", "")).lower() in ("on", "true", "1", "yes")
    pref.venue_type = venue
    pref.preferred_days = ",".join(map(str, days))
    pref.preferred_period = period
    db.session.add(pref)
    db.session.commit()
    return pref


def save_unavailability(instructor, slots):
    """Replace the instructor's unavailable slots. Each slot is "day-hour", e.g. "0-9"."""
    chosen = set()
    for slot in slots:
        day, _, hour = str(slot).partition("-")
        chosen.add((_int(day, "Day", 0, len(DAYS) - 1), _int(hour, "Hour", HOURS[0], HOURS[-1])))
    free = len(DAYS) * len(HOURS) - len(chosen)
    if free < instructor.assigned_hours:
        raise ValidationError(f"You teach {instructor.assigned_hours} hours a week, "
                              f"so at least that many time slots must stay free.")
    instructor.unavailable.clear()
    db.session.flush()
    instructor.unavailable.extend(Unavailability(day=d, hour=h) for d, h in sorted(chosen))
    db.session.commit()


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
        unavailable=course.instructor.blocked_slots if course.instructor else frozenset(),
    )


def _no_overlap_pairs():
    return {frozenset((r.course_a_id, r.course_b_id)) for r in NoOverlap.query}


def build_problem():
    sessions = []
    for course in Course.query.order_by(Course.id):
        sessions += [_session_spec(course, "lecture", i)
                     for i in range(course.lecture_hours)]
        sessions += [_session_spec(course, "lab", i) for i in range(course.lab_hours)]
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
    return (value.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")
            .replace("\r", "").replace("\n", "\\n"))


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
