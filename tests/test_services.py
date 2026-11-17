"""Unit tests for the service layer (business rules + database)."""
import pytest

from app.backend import services
from app.backend.models import (
    ACCEPTED, ARCHIVED, COORDINATOR, DEFAULT_MAX_HOURS, DRAFT, INSTRUCTOR, PUBLISHED, REJECTED,
    Course, Room, ScheduledSession, User,
)
from app.backend.services import (
    ConflictError, NotFoundError, PermissionDenied, SchedulingError, ValidationError,
)

PREFS = {"midterms": 2, "final_exam": "on",
         "venue_type": "lecture_hall", "preferred_days": ["1", "3"],
         "preferred_period": "afternoon"}


# --- Users -----------------------------------------------------------------

def test_register_and_authenticate(app):
    user = services.register_user("amy", "password1", INSTRUCTOR, "Dr. Amy")
    assert user.password_hash != "password1"
    assert services.authenticate("amy", "password1") == user
    assert services.authenticate("amy", "wrong") is None


@pytest.mark.parametrize("username,password,role,message", [
    ("ab", "password1", INSTRUCTOR, "Username"),
    ("amy", "123", INSTRUCTOR, "Password"),
    ("amy", "password1", "admin", "role"),
])
def test_register_rejects_bad_input(app, username, password, role, message):
    with pytest.raises(ValidationError, match=message):
        services.register_user(username, password, role)


def test_register_rejects_duplicate(app, instructor):
    with pytest.raises(ValidationError, match="taken"):
        services.register_user("smith", "password1", COORDINATOR)


# --- Rooms & courses -------------------------------------------------------

def test_create_room_validation(app):
    services.create_room("Hall A", 100, "lecture_hall")
    with pytest.raises(ValidationError, match="already exists"):
        services.create_room("Hall A", 50, "small_room")
    with pytest.raises(ValidationError, match="Capacity"):
        services.create_room("Hall B", 0, "small_room")
    with pytest.raises(ValidationError, match="room type"):
        services.create_room("Hall C", 10, "garage")


@pytest.mark.parametrize("room_type", ["theater", "lecture_hall", "small_room", "lab"])
def test_create_room_accepts_all_types_and_capacity_boundaries(app, room_type):
    room = services.create_room(room_type, 1, room_type)
    assert room.room_type == room_type
    assert room.capacity == 1

    largest = services.create_room(f"{room_type}-large", 2000, room_type)
    assert largest.capacity == 2000


def test_create_course_validation(app, instructor, coordinator):
    course = services.create_course("cs101", "Intro", 40, 3, 1, instructor.id)
    assert course.code == "CS101" and course.instructor == instructor
    with pytest.raises(ValidationError, match="already exists"):
        services.create_course("CS101", "Again", 10)
    with pytest.raises(ValidationError, match="at least one"):
        services.create_course("CS102", "Empty", 10, 0, 0)
    with pytest.raises(ValidationError, match="not an instructor"):
        services.create_course("CS103", "Bad", 10, 1, 0, coordinator.id)
    with pytest.raises(ValidationError, match="Enrollment"):
        services.create_course("CS104", "Bad", "lots")


def test_assign_instructor(catalog, other_instructor):
    course = services.assign_instructor(catalog["se"].id, other_instructor.id)
    assert course.instructor == other_instructor
    assert services.assign_instructor(catalog["se"].id, "").instructor is None


def test_no_overlap_rules(catalog):
    se, ml = catalog["se"], catalog["ml"]
    rule = services.add_no_overlap(ml.id, se.id)
    assert (rule.course_a_id, rule.course_b_id) == tuple(sorted((se.id, ml.id)))
    with pytest.raises(ValidationError, match="already"):
        services.add_no_overlap(se.id, ml.id)
    with pytest.raises(ValidationError, match="different"):
        services.add_no_overlap(se.id, se.id)
    services.delete_no_overlap(rule.id)
    services.add_no_overlap(se.id, ml.id)  # can be re-added after deletion


def test_delete_course_removes_its_rules(catalog):
    services.add_no_overlap(catalog["se"].id, catalog["ml"].id)
    services.delete_course(catalog["se"].id)
    assert services.build_problem().no_overlap == set()


def test_cannot_delete_room_or_course_used_by_schedule(published, catalog):
    room_id = published.sessions[0].room_id
    with pytest.raises(ValidationError, match="used in a schedule"):
        services.delete_room(room_id)
    with pytest.raises(ValidationError, match="used in a schedule"):
        services.delete_course(catalog["se"].id)


# --- Pre-assigned accounts -------------------------------------------------

ACCOUNTS = [
    {"username": "smith", "password": "new-pass-1", "role": "instructor", "full_name": "Dr. Smith"},
    {"username": "boss", "password": "new-pass-2", "role": "coordinator", "full_name": "The Boss"},
]


def test_sync_accounts_creates_updates_and_locks(catalog, instructor, other_instructor):
    assert services.sync_accounts(ACCOUNTS) == ["jones"]
    boss = services.authenticate("boss", "new-pass-2")
    assert boss.is_coordinator and boss.must_change_password
    # An existing account keeps the password its owner chose.
    assert services.authenticate("smith", "secret123") == instructor
    assert not instructor.must_change_password
    # Locked out, but the account and its courses are kept.
    assert services.authenticate("jones", "secret123") is None
    assert catalog["ml"].instructor == other_instructor


def test_sync_accounts_can_reset_existing_passwords(app, instructor):
    services.sync_accounts(ACCOUNTS, reset_passwords=True)
    assert services.authenticate("smith", "new-pass-1") == instructor
    assert services.authenticate("smith", "secret123") is None
    assert instructor.must_change_password


def test_sync_accounts_restores_a_locked_account(app, instructor):
    services.sync_accounts([ACCOUNTS[1]])
    assert instructor.is_locked
    services.sync_accounts(ACCOUNTS)
    assert services.authenticate("smith", "new-pass-1") == instructor


@pytest.mark.parametrize("override,message", [
    ({"username": "ab"}, "Username"),
    ({"password": "short"}, "Password"),
    ({"role": "admin"}, "role"),
])
def test_sync_accounts_rejects_bad_row_without_changes(app, instructor, override, message):
    with pytest.raises(ValidationError, match=message):
        services.sync_accounts([ACCOUNTS[1], {**ACCOUNTS[0], **override}])
    assert services.authenticate("smith", "secret123") == instructor
    assert User.query.count() == 1


def test_sync_accounts_refuses_empty_list(app, instructor):
    with pytest.raises(ValidationError, match="no accounts"):
        services.sync_accounts([])
    assert services.authenticate("smith", "secret123") == instructor


def test_load_accounts_command(app, instructor, tmp_path):
    path = tmp_path / "accounts.csv"
    path.write_text("username,password,full_name,role\nboss,new-pass-2,The Boss,coordinator\n",
                    encoding="utf-8-sig")  # as Excel saves it
    result = app.test_cli_runner().invoke(args=["load-accounts", str(path)])
    assert "Loaded 1 account(s). Locked: smith." in result.output
    assert "new-pass-2" not in result.output
    assert services.authenticate("boss", "new-pass-2") is not None


def test_load_accounts_command_reports_bad_file(app, instructor, tmp_path):
    path = tmp_path / "accounts.csv"
    path.write_text("username,password,full_name,role\nboss,short,The Boss,coordinator\n")
    result = app.test_cli_runner().invoke(args=["load-accounts", str(path)])
    assert result.exit_code != 0 and "Password must be" in result.output
    assert services.authenticate("smith", "secret123") == instructor


def test_import_instructors_adds_and_updates_rows(app, tmp_path):
    path = tmp_path / "instructors.csv"
    path.write_text(
        "username,password,full_name,max_hours\n"
        "newsmith,new-pass-1,New Smith,15\n",
        encoding="utf-8",
    )

    result = app.test_cli_runner().invoke(args=["import-instructors", str(path)])

    assert result.exit_code == 0
    user = User.query.filter_by(username="newsmith").one()
    assert user.full_name == "New Smith"
    assert user.max_hours == 15
    assert services.authenticate("newsmith", "new-pass-1") == user


def test_import_instructors_keeps_existing_password_and_lock(app, instructor, other_instructor):
    services.sync_accounts([ACCOUNTS[0]])  # smith listed, jones locked
    services.import_instructors([
        {"username": "smith", "password": "file-pass-1", "full_name": "Dr. Smith", "max_hours": "9"},
        {"username": "jones", "password": "file-pass-2", "full_name": "", "max_hours": ""},
    ])
    assert services.authenticate("smith", "secret123") == instructor
    assert not instructor.must_change_password and instructor.max_hours == 9
    assert other_instructor.is_locked
    assert services.authenticate("jones", "file-pass-2") is None


def test_import_rooms_and_courses_resolve_instructor(app, instructor, tmp_path):
    rooms = tmp_path / "rooms.csv"
    rooms.write_text("name,capacity,room_type\nHall C,80,lecture_hall\n", encoding="utf-8")
    courses = tmp_path / "courses.csv"
    courses.write_text(
        "code,title,enrollment,lecture_hours,lab_hours,instructor_username\n"
        "cs6000,Advanced Topics,40,2,1,smith\n",
        encoding="utf-8",
    )

    assert app.test_cli_runner().invoke(args=["import-rooms", str(rooms)]).exit_code == 0
    result = app.test_cli_runner().invoke(args=["import-courses", str(courses)])

    assert result.exit_code == 0
    assert Room.query.filter_by(name="Hall C").one().capacity == 80
    course = Course.query.filter_by(code="CS6000").one()
    assert course.instructor == instructor
    assert (course.lecture_hours, course.lab_hours) == (2, 1)


def test_import_courses_rejects_unknown_instructor_without_changes(app, tmp_path):
    path = tmp_path / "courses.csv"
    path.write_text(
        "code,title,enrollment,lecture_hours,lab_hours,instructor_username\n"
        "cs6000,Advanced Topics,40,2,1,missing\n",
        encoding="utf-8",
    )

    result = app.test_cli_runner().invoke(args=["import-courses", str(path)])

    assert result.exit_code != 0
    assert "not an instructor" in result.output
    assert Course.query.count() == 0


def test_import_rooms_requires_expected_columns(app, tmp_path):
    path = tmp_path / "rooms.csv"
    path.write_text("name,capacity\nHall C,80\n", encoding="utf-8")

    result = app.test_cli_runner().invoke(args=["import-rooms", str(path)])

    assert result.exit_code != 0
    assert "room_type" in result.output
    assert Room.query.count() == 0


# --- Instructor workload ---------------------------------------------------

def test_workloads_show_limit_assigned_and_left(catalog, instructor, other_instructor):
    rows = {w["user"].username: w for w in services.workloads()}
    assert (rows["smith"]["assigned"], rows["smith"]["left"]) == (3, DEFAULT_MAX_HOURS - 3)
    assert (rows["jones"]["assigned"], rows["jones"]["left"]) == (3, DEFAULT_MAX_HOURS - 3)
    services.set_max_hours(instructor.id, "2")
    services.set_course_hours(catalog["ml"].id, "4", "1")
    rows = {w["user"].username: w for w in services.workloads()}
    assert rows["smith"]["left"] == -1
    assert rows["jones"]["assigned"] == 5


@pytest.mark.parametrize("value,message", [("61", "Hour limit"), ("many", "Hour limit")])
def test_set_max_hours_validation(app, instructor, value, message):
    with pytest.raises(ValidationError, match=message):
        services.set_max_hours(instructor.id, value)
    assert instructor.max_hours == DEFAULT_MAX_HOURS


def test_set_max_hours_only_for_instructors(app, coordinator):
    with pytest.raises(ValidationError, match="not an instructor"):
        services.set_max_hours(coordinator.id, "5")


# --- Instructor unavailability ---------------------------------------------

def test_generate_never_uses_unavailable_slots(catalog, instructor):
    # Every morning is blocked for smith, who would otherwise be placed there.
    services.save_unavailability(instructor, [f"{d}-{h}" for d in range(5) for h in range(8, 12)])
    schedule = services.generate_schedule("Fall 2026", "2026-08-24", "2026-12-11")
    mine = [s for s in schedule.sessions if s.course.instructor_id == instructor.id]
    assert len(mine) == 3 and all(s.hour >= 12 for s in mine)


def test_move_session_rejects_unavailable_slot(published, catalog, instructor):
    services.save_unavailability(instructor, ["4-17"])
    s = _session(published, catalog["db"])
    with pytest.raises(ConflictError, match="unavailable at Fri 17:00"):
        services.move_session(published.id, s.id, s.room_id, 4, 17)


def test_save_unavailability_replaces_previous_slots(app, instructor):
    services.save_unavailability(instructor, ["0-9", "1-10"])
    services.save_unavailability(instructor, ["1-10", "2-11"])
    assert instructor.blocked_slots == {(1, 10), (2, 11)}
    services.save_unavailability(instructor, [])
    assert instructor.blocked_slots == frozenset()


@pytest.mark.parametrize("slot,message", [("5-9", "Day"), ("0-18", "Hour"), ("junk", "Day")])
def test_save_unavailability_validation(app, instructor, slot, message):
    with pytest.raises(ValidationError, match=message):
        services.save_unavailability(instructor, [slot])
    assert instructor.blocked_slots == frozenset()


def test_save_unavailability_keeps_enough_free_slots(catalog, instructor):
    everything = [f"{d}-{h}" for d in range(5) for h in range(8, 18)]
    with pytest.raises(ValidationError, match="must stay free"):  # smith teaches 3 hours
        services.save_unavailability(instructor, everything)
    services.save_unavailability(instructor, everything[3:])  # exactly 3 free is allowed
    assert len(instructor.blocked_slots) == 47


# --- Preferences -----------------------------------------------------------

def test_save_preference(catalog, instructor):
    pref = services.save_preference(instructor, catalog["se"].id, PREFS)
    assert pref.days == [1, 3]
    assert pref.final_exam is True and pref.midterms == 2
    assert pref.preferred_period == "afternoon"
    # Saving again updates rather than duplicates
    pref2 = services.save_preference(instructor, catalog["se"].id, {**PREFS, "final_exam": ""})
    assert pref2.id == pref.id and pref2.final_exam is False


def test_instructor_cannot_change_course_hours(catalog, instructor):
    services.save_preference(instructor, catalog["se"].id,
                             {**PREFS, "lecture_hours": 4, "lab_hours": 3})
    assert (catalog["se"].lecture_hours, catalog["se"].lab_hours) == (2, 0)
    schedule = services.generate_schedule("Fall 2026", "2026-08-24", "2026-12-11")
    assert sum(s.course_id == catalog["se"].id for s in schedule.sessions) == 2


def test_coordinator_sets_course_hours(catalog):
    services.set_course_hours(catalog["se"].id, "3", "0")
    assert (catalog["se"].lecture_hours, catalog["se"].lab_hours) == (3, 0)
    schedule = services.generate_schedule("Fall 2026", "2026-08-24", "2026-12-11")
    assert sum(s.course_id == catalog["se"].id for s in schedule.sessions) == 3


@pytest.mark.parametrize("lecture,lab,message", [
    ("0", "0", "at least one"),
    ("11", "0", "Lecture hours"),
    ("1", "many", "Lab hours"),
])
def test_set_course_hours_validation(catalog, lecture, lab, message):
    with pytest.raises(ValidationError, match=message):
        services.set_course_hours(catalog["se"].id, lecture, lab)
    assert (catalog["se"].lecture_hours, catalog["se"].lab_hours) == (2, 0)


def test_preference_hours_do_not_change_generated_session_count(catalog, instructor):
    services.save_preference(instructor, catalog["se"].id, {**PREFS, "lecture_hours": 4})
    schedule = services.generate_schedule("Fall 2026", "2026-08-24", "2026-12-11")
    assert sum(session.course_id == catalog["se"].id and session.kind == "lecture"
               for session in schedule.sessions) == catalog["se"].lecture_hours


def test_instructor_cannot_set_preferences_for_others_course(catalog, instructor):
    with pytest.raises(PermissionDenied):
        services.save_preference(instructor, catalog["ml"].id, PREFS)


@pytest.mark.parametrize("override,message", [
    ({"venue_type": "lab"}, "venue"),
    ({"preferred_period": "night"}, "time of day"),
    ({"preferred_days": ["7"]}, "Preferred day"),
])
def test_preference_validation(catalog, instructor, override, message):
    with pytest.raises(ValidationError, match=message):
        services.save_preference(instructor, catalog["se"].id, {**PREFS, **override})


# --- Schedule generation ---------------------------------------------------

def test_generate_schedule_places_every_session(catalog):
    schedule = services.generate_schedule("Fall 2026", "2026-08-24", "2026-12-11")
    assert schedule.status == DRAFT
    # 2 SE lectures + 2 ML lectures + 1 ML lab + 1 DB lecture
    assert len(schedule.sessions) == 6
    assert sum(s.kind == "lab" for s in schedule.sessions) == 1


def test_generated_schedule_satisfies_room_and_people_constraints(published, catalog):
    placements = [
        (session.day, session.hour, session.room_id, session.course_id,
         session.course.instructor_id)
        for session in published.sessions
    ]

    assert all(session.room.capacity >= session.course.enrollment
               for session in published.sessions)
    assert all(session.kind == "lab" and session.room.room_type == "lab"
               or session.kind == "lecture" and session.room.room_type != "lab"
               for session in published.sessions)
    assert len({(day, hour, room_id) for day, hour, room_id, _, _ in placements}) == len(placements)
    assert len({(day, hour, course_id) for day, hour, _, course_id, _ in placements}) == len(placements)
    instructor_slots = [(day, hour, instructor_id) for day, hour, _, _, instructor_id in placements
                        if instructor_id is not None]
    assert len(set(instructor_slots)) == len(instructor_slots)


def test_generate_uses_preferences(catalog, instructor):
    services.save_preference(instructor, catalog["se"].id, PREFS)
    schedule = services.generate_schedule("Fall 2026", "2026-08-24", "2026-12-11")
    se_sessions = [s for s in schedule.sessions if s.course_id == catalog["se"].id]
    assert {s.day for s in se_sessions} == {1, 3}
    assert all(s.hour >= 12 for s in se_sessions)


@pytest.mark.parametrize("semester,start,end,message", [
    ("", "2026-08-24", "2026-12-11", "Semester"),
    ("Fall", "bad", "2026-12-11", "Start date"),
    ("Fall", "2026-12-11", "2026-08-24", "after start"),
])
def test_generate_validates_input(catalog, semester, start, end, message):
    with pytest.raises(ValidationError, match=message):
        services.generate_schedule(semester, start, end)


def test_generate_requires_courses(app):
    with pytest.raises(ValidationError, match="at least one course"):
        services.generate_schedule("Fall", "2026-08-24", "2026-12-11")


def test_generate_reports_infeasible(catalog):
    services.create_course("BIG", "Huge class", 900, 1, 0)
    with pytest.raises(SchedulingError, match="900 seats"):
        services.generate_schedule("Fall", "2026-08-24", "2026-12-11")


# --- Manual edits ----------------------------------------------------------

def _session(schedule, course):
    return next(s for s in schedule.sessions if s.course_id == course.id)


def test_move_session_to_free_slot(published, catalog):
    s = _session(published, catalog["db"])
    moved = services.move_session(published.id, s.id, s.room_id, 4, 17)
    assert (moved.day, moved.hour) == (4, 17)


def test_move_session_rejects_hard_conflict(published, catalog):
    se1, se2 = [s for s in published.sessions if s.course_id == catalog["se"].id]
    with pytest.raises(ConflictError, match="already has a session"):
        services.move_session(published.id, se2.id, se2.room_id, se1.day, se1.hour)


def test_move_session_rejects_small_room(published, catalog):
    se = _session(published, catalog["se"])
    small = next(r for r in services.build_problem().rooms if r.capacity == 30
                 and r.room_type == "small_room")
    with pytest.raises(ConflictError, match="seats 30"):
        services.move_session(published.id, se.id, small.id, se.day, se.hour)


def test_move_session_rejects_wrong_room_type(published, catalog):
    lab_session = _session(published, catalog["ml"])
    lecture_room = next(r for r in services.build_problem().rooms
                        if r.room_type == "lecture_hall")
    with pytest.raises(ConflictError, match="lab room"):
        services.move_session(published.id, lab_session.id, lecture_room.id,
                              lab_session.day, lab_session.hour)


def test_move_session_rejects_no_overlap_conflict(published, catalog):
    services.add_no_overlap(catalog["se"].id, catalog["db"].id)
    se_session = _session(published, catalog["se"])
    db_session = _session(published, catalog["db"])
    occupied_at_target = {session.room_id for session in published.sessions
                          if (session.day, session.hour) == (se_session.day, se_session.hour)}
    available_room = next(room for room in services.build_problem().rooms
                          if room.id not in occupied_at_target
                          and room.room_type != "lab"
                          and room.capacity >= catalog["db"].enrollment)

    with pytest.raises(ConflictError, match="must not overlap"):
        services.move_session(published.id, db_session.id, available_room.id,
                              se_session.day, se_session.hour)


def test_move_session_rejects_session_from_another_schedule(catalog):
    first = services.generate_schedule("Fall 2026", "2026-08-24", "2026-12-11")
    second = services.generate_schedule("Spring 2027", "2027-01-11", "2027-05-14")
    session = first.sessions[0]

    with pytest.raises(NotFoundError, match="not in this schedule"):
        services.move_session(second.id, session.id, session.room_id, session.day, session.hour)


def test_move_session_updates_soft_penalty(published, catalog, instructor):
    services.save_preference(instructor, catalog["db"].id, {**PREFS, "preferred_days": ["0"]})
    s = _session(published, catalog["db"])
    services.move_session(published.id, s.id, s.room_id, 4, 16)
    assert published.soft_penalty >= 1
    assert s.id in services.soft_report(published)


def test_move_session_invalid_input(published, catalog):
    s = _session(published, catalog["db"])
    with pytest.raises(ValidationError, match="Day"):
        services.move_session(published.id, s.id, s.room_id, 5, 9)
    with pytest.raises(ValidationError, match="Hour"):
        services.move_session(published.id, s.id, s.room_id, 0, 20)
    with pytest.raises(NotFoundError):
        services.move_session(published.id, 9999, s.room_id, 0, 9)


def test_publish_archives_previous(published):
    newer = services.generate_schedule("Fall 2026 v2", "2026-08-24", "2026-12-11")
    services.publish_schedule(newer.id)
    assert services.published_schedule() == newer
    assert published.status == ARCHIVED


def test_delete_schedule(catalog):
    draft = services.generate_schedule("Draft", "2026-08-24", "2026-12-11")
    services.delete_schedule(draft.id)
    assert ScheduledSession.query.count() == 0


def test_cannot_delete_published_schedule(published):
    with pytest.raises(ValidationError, match="published"):
        services.delete_schedule(published.id)


# --- Change requests -------------------------------------------------------

def test_change_request_flow(published, catalog, instructor):
    s = _session(published, catalog["se"])
    req = services.create_change_request(instructor, s.id, "Please move to Thursday")
    assert req.status == "pending" and req.session == s
    services.respond_change_request(req.id, accept=True, response="Done")
    assert req.status == ACCEPTED and req.response == "Done"
    with pytest.raises(ValidationError, match="already been answered"):
        services.respond_change_request(req.id, accept=False)


def test_change_request_rejected(published, instructor):
    req = services.create_change_request(instructor, "", "General comment")
    assert req.session is None
    assert services.respond_change_request(req.id, accept=False).status == REJECTED


def test_change_request_rules(catalog, instructor):
    with pytest.raises(ValidationError, match="no published schedule"):
        services.create_change_request(instructor, None, "Hello")
    schedule = services.publish_schedule(
        services.generate_schedule("Fall", "2026-08-24", "2026-12-11").id)
    others = _session(schedule, catalog["ml"])
    with pytest.raises(PermissionDenied):
        services.create_change_request(instructor, others.id, "Move it")
    with pytest.raises(ValidationError, match="Message"):
        services.create_change_request(instructor, None, "   ")
    assert schedule.status == PUBLISHED


# --- Calendar export -------------------------------------------------------

def test_instructor_calendar(published, catalog, instructor):
    ics = services.instructor_calendar(instructor, published)
    assert ics.startswith("BEGIN:VCALENDAR\r\n") and ics.endswith("END:VCALENDAR\r\n")
    # smith teaches SE (2 lectures) + DB (1 lecture); ML belongs to jones
    assert ics.count("BEGIN:VEVENT") == 3
    assert "CS5590" not in ics
    assert "RRULE:FREQ=WEEKLY;UNTIL=20261211T235959" in ics


def test_calendar_text_cannot_add_lines(published, catalog, instructor):
    catalog["db"].title = "Databases\r\nATTENDEE:evil@example.com"
    ics = services.instructor_calendar(instructor, published)
    assert "\r\nATTENDEE" not in ics


def test_calendar_first_occurrence_on_correct_weekday(published, catalog, instructor):
    s = _session(published, catalog["db"])
    services.move_session(published.id, s.id, s.room_id, 2, 10)  # Wednesday 10:00
    ics = services.instructor_calendar(instructor, published)
    assert "DTSTART:20260826T100000" in ics  # semester starts Mon 24 Aug -> Wed 26 Aug
