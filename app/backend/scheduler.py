"""Constraint-based semester timetable generator.

Pure Python with no Flask or database imports, so the algorithm can be unit
tested in isolation. services.py converts database rows into these specs.

Hard constraints (must always hold):
  H1  room capacity >= course enrollment
  H2  lab sessions are held in lab rooms, and lectures never are
  H3  a room hosts at most one session per time slot
  H4  an instructor teaches at most one session per time slot
  H5  two sessions of the same course never share a time slot
  H6  courses marked "no overlap" never share a time slot

Soft constraints (each violation adds one penalty point):
  S1  session falls on one of the instructor's preferred days
  S2  session falls in the instructor's preferred period (morning/afternoon)
  S3  lecture is held in the instructor's preferred venue type
  S4  sessions of the same course are spread over different days
"""
from collections import defaultdict
from dataclasses import dataclass, field

DAYS = ("Mon", "Tue", "Wed", "Thu", "Fri")
HOURS = tuple(range(8, 18))  # one-hour sessions starting 08:00 .. 17:00
NOON = 12


@dataclass(frozen=True)
class RoomSpec:
    id: int
    name: str
    capacity: int
    room_type: str


@dataclass(frozen=True)
class SessionSpec:
    course_id: int
    course_code: str
    kind: str  # "lecture" or "lab"
    index: int
    enrollment: int
    instructor_id: int | None = None
    venue_pref: str | None = None
    preferred_days: frozenset = frozenset()
    preferred_period: str = "any"


@dataclass(frozen=True)
class Placement:
    session: SessionSpec
    room: RoomSpec
    day: int
    hour: int


@dataclass
class Problem:
    rooms: list
    sessions: list
    no_overlap: set = field(default_factory=set)  # frozensets of two course ids
    days: int = len(DAYS)
    hours: tuple = HOURS

    @property
    def slots(self):
        return [(d, h) for d in range(self.days) for h in self.hours]


@dataclass
class Result:
    placements: list
    soft_violations: dict  # Placement -> list of reasons

    @property
    def penalty(self):
        return sum(len(reasons) for reasons in self.soft_violations.values())


class SchedulingError(Exception):
    """No timetable satisfies the hard constraints."""


def slot_label(day, hour):
    return f"{DAYS[day]} {hour:02d}:00"


def room_suits(session, room):
    """Static hard constraints H1 and H2, which do not depend on other sessions."""
    return (room.capacity >= session.enrollment
            and (room.room_type == "lab") == (session.kind == "lab"))


class Timetable:
    """A partial or complete timetable, indexed for fast constraint checks."""

    def __init__(self, no_overlap=()):
        self.no_overlap = set(no_overlap)
        self.placements = []
        self._by_slot = defaultdict(list)
        self._by_course = defaultdict(list)

    def add(self, placement):
        self.placements.append(placement)
        self._by_slot[(placement.day, placement.hour)].append(placement)
        self._by_course[placement.session.course_id].append(placement)

    def remove(self, placement):
        self.placements.remove(placement)
        self._by_slot[(placement.day, placement.hour)].remove(placement)
        self._by_course[placement.session.course_id].remove(placement)

    def hard_violations(self, session, room, day, hour):
        """Reasons why placing `session` in `room` at (day, hour) is illegal."""
        reasons = []
        if room.capacity < session.enrollment:
            reasons.append(f"{room.name} seats {room.capacity} but {session.course_code} "
                           f"has {session.enrollment} students")
        if session.kind == "lab" and room.room_type != "lab":
            reasons.append("Labs must be held in a lab room")
        elif session.kind != "lab" and room.room_type == "lab":
            reasons.append("Lectures cannot be held in a lab room")

        when = slot_label(day, hour)
        for other in self._by_slot[(day, hour)]:
            o = other.session
            if other.room.id == room.id:
                reasons.append(f"{room.name} is already booked at {when} by {o.course_code}")
            if session.instructor_id is not None and o.instructor_id == session.instructor_id:
                reasons.append(f"The instructor already teaches {o.course_code} at {when}")
            if o.course_id == session.course_id:
                reasons.append(f"{session.course_code} already has a session at {when}")
            elif frozenset((o.course_id, session.course_id)) in self.no_overlap:
                reasons.append(f"{session.course_code} and {o.course_code} must not overlap")
        return reasons

    def soft_violations(self, session, room, day, hour):
        """Instructor preferences that placing `session` here would not honour."""
        reasons = []
        if session.preferred_days and day not in session.preferred_days:
            reasons.append(f"{DAYS[day]} is not a preferred day")
        if session.preferred_period == "morning" and hour >= NOON:
            reasons.append("Instructor prefers mornings")
        elif session.preferred_period == "afternoon" and hour < NOON:
            reasons.append("Instructor prefers afternoons")
        if (session.kind == "lecture" and session.venue_pref
                and room.room_type != session.venue_pref):
            reasons.append(f"Instructor prefers a {session.venue_pref.replace('_', ' ')}")
        if any(p.day == day for p in self._by_course[session.course_id]):
            reasons.append(f"{session.course_code} already meets on {DAYS[day]}")
        return reasons


def evaluate_soft(timetable):
    """Soft violations of every placement, judged against all the others."""
    report = {}
    for placement in list(timetable.placements):
        timetable.remove(placement)
        reasons = timetable.soft_violations(
            placement.session, placement.room, placement.day, placement.hour)
        timetable.add(placement)
        if reasons:
            report[placement] = reasons
    return report


def check_capacity(problem):
    """Cheap necessary conditions, so obviously impossible inputs fail fast with
    a useful message instead of making the search explore every combination."""
    for s in problem.sessions:
        if not any(room_suits(s, r) for r in problem.rooms):
            need = "a lab room" if s.kind == "lab" else "a non-lab room"
            raise SchedulingError(f"No room can host {s.course_code} {s.kind}: it needs "
                                  f"{need} with at least {s.enrollment} seats.")

    n_slots = len(problem.slots)
    per_instructor = defaultdict(int)
    per_course = defaultdict(list)
    for s in problem.sessions:
        if s.instructor_id is not None:
            per_instructor[s.instructor_id] += 1
        per_course[s.course_id].append(s)
    for instructor_id, count in per_instructor.items():
        if count > n_slots:
            raise SchedulingError(f"An instructor has {count} weekly sessions but the week "
                                  f"only has {n_slots} time slots.")
    for sessions in per_course.values():
        if len(sessions) > n_slots:
            raise SchedulingError(f"{sessions[0].course_code} has {len(sessions)} weekly "
                                  f"sessions but the week only has {n_slots} time slots.")

    for kind, is_lab in (("lab", True), ("lecture", False)):
        needed = sum(1 for s in problem.sessions if s.kind == kind)
        rooms = sum(1 for r in problem.rooms if (r.room_type == "lab") == is_lab)
        if needed > rooms * n_slots:
            raise SchedulingError(f"{needed} {kind} sessions do not fit: {rooms} suitable "
                                  f"room(s) x {n_slots} slots = {rooms * n_slots} bookings.")


def generate(problem, max_steps=100_000):
    """Return a Result satisfying every hard constraint, or raise SchedulingError.

    Backtracking search. Sessions are placed most-constrained first (fewest
    suitable rooms, then largest class). For each session, candidate slots are
    tried in order of fewest soft violations, then smallest room, which keeps
    big rooms free for big classes.
    """
    check_capacity(problem)

    suitable = {s: sorted((r for r in problem.rooms if room_suits(s, r)),
                          key=lambda r: (r.capacity, r.id))
                for s in problem.sessions}
    order = sorted(problem.sessions, key=lambda s: (
        len(suitable[s]), -s.enrollment, s.course_id, s.kind, s.index))
    slots = problem.slots
    timetable = Timetable(problem.no_overlap)
    steps = 0
    deepest = 0

    def candidates(session):
        options = []
        for room in suitable[session]:
            for day, hour in slots:
                if not timetable.hard_violations(session, room, day, hour):
                    penalty = len(timetable.soft_violations(session, room, day, hour))
                    options.append((penalty, room.capacity, day, hour, room))
        options.sort(key=lambda o: o[:4])
        return [Placement(session, room, day, hour) for _, _, day, hour, room in options]

    def place(i):
        nonlocal steps, deepest
        if i == len(order):
            return True
        deepest = max(deepest, i)
        for placement in candidates(order[i]):
            steps += 1
            if steps > max_steps:
                raise SchedulingError("Search limit reached. Try adding rooms or "
                                      "removing no-overlap rules.")
            timetable.add(placement)
            if place(i + 1):
                return True
            timetable.remove(placement)
        return False

    if not place(0):
        s = order[deepest]
        raise SchedulingError("No timetable satisfies all hard constraints "
                              f"(could not place {s.course_code} {s.kind}).")
    return Result(list(timetable.placements), evaluate_soft(timetable))
