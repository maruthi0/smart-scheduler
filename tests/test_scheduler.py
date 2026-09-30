"""Unit tests for the timetabling algorithm (no database or Flask involved)."""
import pytest

from app.scheduler import (
    HOURS, Placement, Problem, RoomSpec, SchedulingError, SessionSpec, Timetable, generate,
    room_suits,
)

HALL = RoomSpec(1, "Hall", 100, "lecture_hall")
SMALL = RoomSpec(2, "Small", 20, "small_room")
LAB = RoomSpec(3, "Lab", 30, "lab")
THEATER = RoomSpec(4, "Theater", 300, "theater")


def lecture(course_id, index=0, enrollment=20, instructor=None, **prefs):
    return SessionSpec(course_id, f"C{course_id}", "lecture", index, enrollment, instructor, **prefs)


def lab(course_id, index=0, enrollment=20, instructor=None):
    return SessionSpec(course_id, f"C{course_id}", "lab", index, enrollment, instructor)


def slots(result):
    return [(p.day, p.hour) for p in result.placements]


def hard_ok(result, no_overlap=()):
    """Re-check every placement of a result against all the others."""
    tt = Timetable(no_overlap)
    for p in result.placements:
        tt.add(p)
    for p in result.placements:
        tt.remove(p)
        assert tt.hard_violations(p.session, p.room, p.day, p.hour) == [], p
        tt.add(p)
    return True


# --- Static room suitability (H1, H2) --------------------------------------

@pytest.mark.parametrize("session,room,expected", [
    (lecture(1, enrollment=100), HALL, True),       # exactly fits
    (lecture(1, enrollment=101), HALL, False),      # one too many
    (lecture(1), LAB, False),                       # lecture in lab
    (lab(1), LAB, True),
    (lab(1), SMALL, False),                         # lab outside a lab room
])
def test_room_suits(session, room, expected):
    assert room_suits(session, room) is expected


# --- Hard constraints -------------------------------------------------------

def test_every_session_is_placed_once():
    sessions = [lecture(1, i) for i in range(3)] + [lab(1)]
    result = generate(Problem([HALL, LAB], sessions))
    placed = [p.session for p in result.placements]
    assert len(placed) == len(sessions) and set(placed) == set(sessions)
    assert hard_ok(result)


def test_capacity_is_respected():
    big = lecture(1, enrollment=80)
    result = generate(Problem([SMALL, HALL], [big]))
    assert result.placements[0].room == HALL


def test_labs_go_to_lab_rooms():
    result = generate(Problem([HALL, LAB], [lab(1), lecture(2)]))
    rooms = {p.session.kind: p.room for p in result.placements}
    assert rooms == {"lab": LAB, "lecture": HALL}


def test_room_never_double_booked():
    # 1 room, 50 weekly slots, 50 sessions -> every slot used exactly once
    sessions = [lecture(c) for c in range(50)]
    result = generate(Problem([HALL], sessions))
    assert len(set(slots(result))) == 50


def test_instructor_never_double_booked():
    sessions = [lecture(1, instructor=7), lecture(2, instructor=7)]
    result = generate(Problem([HALL, SMALL], sessions))
    assert len(set(slots(result))) == 2


def test_same_course_sessions_never_share_a_slot():
    sessions = [lecture(1, 0), lecture(1, 1)]
    result = generate(Problem([HALL, SMALL], sessions))
    assert len(set(slots(result))) == 2


def test_no_overlap_rule_is_respected():
    rule = {frozenset((1, 2))}
    sessions = [lecture(1, i) for i in range(3)] + [lecture(2, i) for i in range(3)]
    result = generate(Problem([HALL, SMALL], sessions, rule))
    by_course = {1: set(), 2: set()}
    for p in result.placements:
        by_course[p.session.course_id].add((p.day, p.hour))
    assert not by_course[1] & by_course[2]
    assert hard_ok(result, rule)


def test_no_suitable_room_raises_clear_error():
    with pytest.raises(SchedulingError, match="at least 500 seats"):
        generate(Problem([HALL], [lecture(1, enrollment=500)]))
    with pytest.raises(SchedulingError, match="lab room"):
        generate(Problem([HALL], [lab(1)]))


def test_overloaded_instructor_fails_fast():
    # One instructor, 51 sessions, only 50 weekly slots.
    sessions = [lecture(c, instructor=1) for c in range(51)]
    with pytest.raises(SchedulingError, match="51 weekly sessions"):
        generate(Problem([HALL, SMALL], sessions))


def test_too_few_rooms_fails_fast():
    sessions = [lecture(c) for c in range(51)]
    with pytest.raises(SchedulingError, match="51 lecture sessions do not fit"):
        generate(Problem([HALL], sessions))


def test_infeasible_combination_found_by_search():
    # Two slots; A-B and B-C and A-C must not overlap -> three courses need 3 slots.
    rules = {frozenset((1, 2)), frozenset((2, 3)), frozenset((1, 3))}
    sessions = [lecture(1), lecture(2), lecture(3)]
    with pytest.raises(SchedulingError, match="hard constraints"):
        generate(Problem([HALL, SMALL, THEATER], sessions, rules, days=1, hours=(9, 10)))


def test_search_limit_raises():
    sessions = [lecture(c) for c in range(3)]
    with pytest.raises(SchedulingError, match="Search limit"):
        generate(Problem([HALL], sessions), max_steps=1)


def test_hard_violation_messages():
    tt = Timetable({frozenset((1, 2))})
    tt.add(Placement(lecture(1, instructor=9), HALL, 0, 9))
    reasons = tt.hard_violations(lecture(2, instructor=9), HALL, 0, 9)
    assert any("already booked" in r for r in reasons)
    assert any("already teaches" in r for r in reasons)
    assert any("must not overlap" in r for r in reasons)
    assert tt.hard_violations(lecture(2, instructor=9), HALL, 0, 10) == []


# --- Soft constraints -------------------------------------------------------

def test_preferred_days_are_honoured_when_possible():
    s = lecture(1, preferred_days=frozenset({2}))
    result = generate(Problem([HALL], [s]))
    assert result.placements[0].day == 2
    assert result.penalty == 0


def test_preferred_period_morning_and_afternoon():
    am = lecture(1, preferred_period="morning")
    pm = lecture(2, preferred_period="afternoon")
    result = generate(Problem([HALL], [am, pm]))
    hours = {p.session.course_id: p.hour for p in result.placements}
    assert hours[1] < 12 <= hours[2]


def test_preferred_venue_is_honoured():
    s = lecture(1, venue_pref="theater")
    result = generate(Problem([HALL, THEATER], [s]))
    assert result.placements[0].room == THEATER


def test_sessions_spread_over_different_days():
    sessions = [lecture(1, i) for i in range(3)]
    result = generate(Problem([HALL], sessions))
    assert len({p.day for p in result.placements}) == 3


def test_unmeetable_preference_is_reported_not_fatal():
    # Only Monday preferred, but three lectures -> at least two soft violations.
    sessions = [lecture(1, i, preferred_days=frozenset({0})) for i in range(3)]
    result = generate(Problem([HALL], sessions))
    assert len(result.placements) == 3
    assert result.penalty >= 2
    assert any("Mon" in r or "not a preferred day" in r
               for reasons in result.soft_violations.values() for r in reasons)


def test_hard_constraints_beat_soft_preferences():
    # Both want Monday 08:00-11:00 in the only room; one must accept worse.
    a = lecture(1, preferred_days=frozenset({0}), preferred_period="morning")
    b = lecture(2, preferred_days=frozenset({0}), preferred_period="morning")
    result = generate(Problem([HALL], [a, b]))
    assert len(set(slots(result))) == 2
    assert all(p.day == 0 and p.hour < 12 for p in result.placements)


def test_slot_range():
    result = generate(Problem([HALL], [lecture(1)]))
    assert result.placements[0].hour in HOURS
