"""Integration tests through the Flask test client (HTTP -> service -> DB)."""
from app.models import ChangeRequest, Course, Room, Schedule
from tests.conftest import login


# --- Authentication & roles ------------------------------------------------

def test_home_redirects_to_login(client):
    assert "/login" in client.get("/").headers["Location"]


def test_register_instructor(client, app):
    resp = client.post("/register", data={"username": "amy", "password": "secret123",
                                          "full_name": "Dr. Amy", "role": "instructor"},
                       follow_redirects=True)
    assert b"My courses" in resp.data


def test_register_coordinator_requires_code(client, app):
    data = {"username": "boss", "password": "secret123", "role": "coordinator"}
    resp = client.post("/register", data={**data, "coordinator_code": "wrong"})
    assert b"Invalid coordinator access code" in resp.data
    resp = client.post("/register", data={**data, "coordinator_code": "letmein"},
                       follow_redirects=True)
    assert b"Generate a semester schedule" in resp.data


def test_register_shows_validation_error(client, app):
    resp = client.post("/register", data={"username": "a", "password": "secret123",
                                          "role": "instructor"})
    assert b"at least 3 characters" in resp.data


def test_bad_login(client, instructor):
    resp = client.post("/login", data={"username": "smith", "password": "nope"})
    assert b"Invalid username or password" in resp.data


def test_logout(instructor_client):
    instructor_client.post("/logout")
    assert instructor_client.get("/instructor/").status_code == 302


def test_instructor_cannot_access_coordinator_pages(instructor_client):
    assert instructor_client.get("/coordinator/").status_code == 403
    assert instructor_client.post("/coordinator/rooms", data={}).status_code == 403


def test_coordinator_cannot_access_instructor_pages(coord_client):
    assert coord_client.get("/instructor/").status_code == 403


def test_anonymous_redirected(client):
    assert client.get("/coordinator/").status_code == 302
    assert client.get("/instructor/schedule").status_code == 302


# --- Coordinator -----------------------------------------------------------

def test_coordinator_manages_rooms(coord_client):
    resp = coord_client.post("/coordinator/rooms", data={
        "name": "Hall A", "capacity": "80", "room_type": "lecture_hall"}, follow_redirects=True)
    assert b"Room added" in resp.data and b"Hall A" in resp.data
    resp = coord_client.post("/coordinator/rooms", data={
        "name": "Bad", "capacity": "-1", "room_type": "lecture_hall"}, follow_redirects=True)
    assert b"Capacity must be between" in resp.data
    room = Room.query.one()
    coord_client.post(f"/coordinator/rooms/{room.id}/delete")
    assert Room.query.count() == 0


def test_coordinator_manages_courses_and_rules(coord_client, instructor):
    for code in ("CS1", "CS2"):
        coord_client.post("/coordinator/courses", data={
            "code": code, "title": "T", "enrollment": "20", "lecture_hours": "2",
            "lab_hours": "0", "instructor_id": str(instructor.id)})
    a, b = Course.query.order_by(Course.code).all()
    resp = coord_client.post("/coordinator/rules", data={
        "course_a_id": a.id, "course_b_id": b.id}, follow_redirects=True)
    assert b"CS1 \xe2\x9c\x95 CS2" in resp.data  # "CS1 ✕ CS2"
    coord_client.post(f"/coordinator/courses/{a.id}/instructor", data={"instructor_id": ""})
    assert a.instructor is None
    coord_client.post(f"/coordinator/courses/{b.id}/delete")
    assert Course.query.count() == 1


def test_generate_view_publish_schedule(coord_client, catalog):
    resp = coord_client.post("/coordinator/schedules", data={
        "semester": "Fall 2026", "start_date": "2026-08-24", "end_date": "2026-12-11"},
        follow_redirects=True)
    assert b"Schedule generated" in resp.data
    assert b"all hard constraints satisfied" in resp.data
    schedule = Schedule.query.one()
    resp = coord_client.post(f"/coordinator/schedules/{schedule.id}/publish",
                             follow_redirects=True)
    assert b"Schedule published" in resp.data
    assert schedule.status == "published"


def test_generate_shows_scheduling_error(coord_client, catalog):
    coord_client.post("/coordinator/courses", data={
        "code": "BIG", "title": "Huge", "enrollment": "900", "lecture_hours": "1",
        "lab_hours": "0"})
    resp = coord_client.post("/coordinator/schedules", data={
        "semester": "Fall", "start_date": "2026-08-24", "end_date": "2026-12-11"},
        follow_redirects=True)
    assert b"900 seats" in resp.data
    assert Schedule.query.count() == 0


def test_move_session_conflict_is_shown(coord_client, published, catalog):
    se1, se2 = [s for s in published.sessions if s.course_id == catalog["se"].id]
    resp = coord_client.post(
        f"/coordinator/schedules/{published.id}/sessions/{se2.id}/move",
        data={"room_id": se2.room_id, "day": se1.day, "hour": se1.hour}, follow_redirects=True)
    assert b"already has a session" in resp.data


def test_delete_draft_schedule(coord_client, catalog):
    coord_client.post("/coordinator/schedules", data={
        "semester": "Draft", "start_date": "2026-08-24", "end_date": "2026-12-11"})
    schedule = Schedule.query.one()
    resp = coord_client.post(f"/coordinator/schedules/{schedule.id}/delete",
                             follow_redirects=True)
    assert b"Schedule deleted" in resp.data


def test_published_schedule_cannot_be_deleted(coord_client, published):
    resp = coord_client.post(f"/coordinator/schedules/{published.id}/delete",
                             follow_redirects=True)
    assert b"published schedule cannot be deleted" in resp.data
    assert Schedule.query.filter_by(id=published.id).one().status == "published"


def test_missing_schedule_404(coord_client):
    assert coord_client.get("/coordinator/schedules/999").status_code == 404


def test_coordinator_responds_to_request(client, published, catalog, coordinator):
    login(client, "smith")
    client.post("/instructor/requests", data={"session_id": "", "message": "Hi"})
    client.post("/logout")
    login(client, "coord")
    assert b"1 change request waiting" in client.get("/coordinator/").data
    req = ChangeRequest.query.one()
    resp = client.post(f"/coordinator/requests/{req.id}/respond",
                       data={"decision": "reject", "response": "Room unavailable"},
                       follow_redirects=True)
    assert b"Request rejected" in resp.data and b"Room unavailable" in resp.data


def test_instructor_cannot_request_change_to_others_session(instructor_client, published,
                                                            catalog):
    other_session = next(session for session in published.sessions
                         if session.course_id == catalog["ml"].id)
    resp = instructor_client.post("/instructor/requests", data={
        "session_id": other_session.id, "message": "Move this session"},
        follow_redirects=True)
    assert resp.status_code == 403
    assert b"only request changes to your own sessions" in resp.data
    assert ChangeRequest.query.count() == 0


# --- Instructor ------------------------------------------------------------

def test_instructor_dashboard_without_schedule(instructor_client, catalog):
    resp = instructor_client.get("/instructor/")
    assert b"CS5551" in resp.data and b"CS5590" not in resp.data
    assert b"not published a schedule yet" in resp.data
    assert b"not published" in instructor_client.get("/instructor/schedule").data
    resp = instructor_client.get("/instructor/calendar.ics", follow_redirects=True)
    assert b"no published schedule" in resp.data


def test_instructor_submits_preferences(instructor_client, catalog):
    url = f"/instructor/courses/{catalog['se'].id}/preferences"
    assert instructor_client.get(url).status_code == 200
    resp = instructor_client.post(url, data={
        "lecture_hours": "3", "lab_hours": "0", "midterms": "2", "final_exam": "on",
        "venue_type": "theater", "preferred_days": ["0", "2"], "preferred_period": "morning",
    }, follow_redirects=True)
    assert b"Preferences for CS5551 saved" in resp.data
    assert catalog["se"].preference.days == [0, 2]


def test_instructor_preference_validation_shown(instructor_client, catalog):
    resp = instructor_client.post(f"/instructor/courses/{catalog['se'].id}/preferences",
                                  data={"lecture_hours": "0", "lab_hours": "0"})
    assert b"at least one lecture or lab hour" in resp.data


def test_instructor_cannot_edit_others_preferences(instructor_client, catalog):
    url = f"/instructor/courses/{catalog['ml'].id}/preferences"
    assert instructor_client.get(url).status_code == 403


def test_instructor_sees_published_schedule_readonly(instructor_client, published):
    resp = instructor_client.get("/instructor/schedule")
    assert b"Fall 2026 timetable" in resp.data and b"read-only" in resp.data
    assert b"Move" not in resp.data


def test_instructor_sends_change_request(instructor_client, published, catalog):
    s = next(x for x in published.sessions if x.course_id == catalog["se"].id)
    resp = instructor_client.post("/instructor/requests", data={
        "session_id": s.id, "message": "Can this move to the afternoon?"},
        follow_redirects=True)
    assert b"Change request sent" in resp.data and b"pending" in resp.data
    resp = instructor_client.post("/instructor/requests", data={"message": ""},
                                  follow_redirects=True)
    assert b"Message is required" in resp.data


def test_instructor_downloads_calendar(instructor_client, published):
    resp = instructor_client.get("/instructor/calendar.ics")
    assert resp.mimetype == "text/calendar"
    assert "attachment" in resp.headers["Content-Disposition"]
    assert b"BEGIN:VEVENT" in resp.data
