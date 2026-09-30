# CS 5551 Team Project — Sprint #1 Report

**Project 2: Event Scheduling App (Course Scheduler)**
**GitHub:** `<add repository URL>` *(if the repo is private, invite `sudiptac`)*

> **Team:** replace every `TBD` below with real names, estimates and dates. Re-estimate the effort hours together as a team, because the instructions require the whole team to take part in estimation. Delete this note before you submit.

| Student name | Specific contributions to this sprint |
|---|---|
| TBD | |
| TBD | |
| TBD | |
| TBD | |

---

## 0. Requirements clarification

The project description is intentionally vague. The team resolved the ambiguities as follows. **Confirm these with the instructor.**

| # | Ambiguity in the brief | Decision |
|---|---|---|
| A1 | Who may become a coordinator? | Anyone can register as an instructor. Registering as a coordinator requires an access code set by the department (`COORDINATOR_CODE`). |
| A2 | What is a "time slot"? | One-hour blocks, Monday–Friday, starting 08:00–17:00, which gives 50 slots per week. Each lecture hour or lab hour is one session. |
| A3 | Which constraints are hard? | Room capacity, room type (labs in lab rooms), no double-booking of rooms or instructors, no two sessions of one course at once, and coordinator-defined *no-overlap* course pairs. |
| A4 | Which constraints are soft? | Instructor-preferred days, time of day (morning/afternoon) and venue type, plus spreading a course's sessions over different days. |
| A5 | Are "lecture hours/week" preferences or requirements? | The instructor's submitted hours replace the coordinator's defaults and are always honoured (they are a requirement). Day, time and venue are soft preferences. |
| A6 | What happens to #midterms and final-exam information? | It is recorded and shown to coordinators. Exam scheduling is a may-have for a later sprint (US-14). |
| A7 | How does linking to Google Calendar work? | The app exports a standard iCalendar (.ics) file with weekly recurring events, which Google Calendar, Outlook and Apple Calendar all import. Direct OAuth sync is a may-have (US-12). |
| A8 | "Instructors should not modify the schedule." | Instructors see a read-only timetable. They can file change requests, which coordinators accept or reject; only coordinators move sessions. |

---

## I. User Stories

Priority: **Must** = must-have (required for the primitive functions); **May** = implement if time allows.

| ID | User Story Name | User Story Description | Priority | Est. effort (h) | Actual effort | Status | Developer names |
|---|---|---|---|---|---|---|---|
| 1 | Accounts & roles | As a **user**, I want to register and log in as a coordinator or an instructor, so that I only see the functions for my role. | Must | 6 | | completed | TBD |
| 2 | Manage rooms | As a **coordinator**, I want to add and remove rooms with their capacity and type, so that the scheduler knows which venues exist. | Must | 4 | | completed | TBD |
| 3 | Manage courses | As a **coordinator**, I want to add courses with enrollment, default lecture/lab hours and an instructor, so that they can be scheduled. | Must | 6 | | completed | TBD |
| 4 | No-overlap constraints | As a **coordinator**, I want to mark pairs of courses that must never run at the same time, so that students in the same cohort can take both. | Must | 4 | | completed | TBD |
| 5 | Instructor preferences | As an **instructor**, I want to submit my lecture hours, lab hours, number of midterms, final exam, preferred venue, days and time of day, so that the schedule suits my teaching without emailing the coordinator. | Must | 6 | | completed | TBD |
| 6 | Generate schedule | As a **coordinator**, I want to generate a semester timetable automatically that satisfies all hard constraints, so that I don't have to build it by hand. | Must | 16 | | completed | TBD |
| 7 | Honour preferences | As a **coordinator**, I want the generator to satisfy as many instructor preferences as possible and show me the ones it could not meet, so that the schedule is fair and I can explain trade-offs. | Must | 8 | | completed | TBD |
| 8 | Adjust schedule | As a **coordinator**, I want to move a session to another room or time and be told if that breaks a hard constraint, so that I can fine-tune the result safely. | Must | 6 | | completed | TBD |
| 9 | Publish & view | As a **coordinator**, I want to publish a schedule so that instructors can view it, and as an **instructor** I want a read-only timetable with my sessions highlighted. | Must | 5 | | completed | TBD |
| 10 | Change requests | As an **instructor**, I want to suggest a change to one of my sessions, and as a **coordinator** I want to accept or reject it with a reply, so that we can communicate without email. | Must | 6 | | completed | TBD |
| 11 | Calendar export | As an **instructor**, I want to add my teaching schedule to my personal calendar (e.g. Google Calendar), so that I see my classes alongside my other events. | May | 4 | | completed | TBD |
| 12 | Google Calendar sync | As an **instructor**, I want my Google Calendar updated automatically when the schedule changes, so that I never have an outdated copy. | May | 12 | | toDo | |
| 13 | Notifications | As an **instructor**, I want to be notified when a schedule is published or my request is answered, so that I don't have to keep checking. | May | 6 | | toDo | |
| 14 | Exam scheduling | As a **coordinator**, I want midterm and final exam slots generated from instructors' exam preferences, so that exams don't clash. | May | 12 | | toDo | |
| 15 | Instructor unavailability | As an **instructor**, I want to mark times I am unavailable as a hard constraint, so that I am never scheduled then. | May | 5 | | toDo | |

---

## II. Acceptance Criteria (Given-When-Then)

| User Story | AC ID | Description of Acceptance Criterion | Status | Developer |
|---|---|---|---|---|
| **1 Accounts & roles** | 1.1 | **Register as instructor.** *Given* I am on the registration page, *when* I submit a new username (≥ 3 characters), a password (≥ 6 characters) and the role "instructor", *then* my account is created and I land on "My courses". | completed | TBD |
| | 1.2 | **Coordinator code required.** *Given* I choose the role "coordinator", *when* I submit a wrong access code, *then* registration is refused with "Invalid coordinator access code"; *when* the code is correct, *then* I land on the coordinator dashboard. | completed | TBD |
| | 1.3 | **Invalid registration.** *Given* the username is too short, the password is too short, or the username is already taken, *when* I submit, *then* I see an error and no account is created. | completed | TBD |
| | 1.4 | **Login/logout.** *Given* a registered user, *when* they enter the correct password, *then* they are signed in; *when* the password is wrong, *then* they see "Invalid username or password"; *when* they log out, *then* protected pages redirect to login. | completed | TBD |
| | 1.5 | **Role separation.** *Given* I am logged in as an instructor, *when* I open any coordinator page, *then* I get HTTP 403 (and vice versa). *Given* I am not logged in, *then* I am redirected to login. | completed | TBD |
| **2 Manage rooms** | 2.1 | **Add room.** *Given* I am a coordinator, *when* I add a room with a unique name, capacity 1–2000 and a type (theater, lecture hall, small room, lab), *then* it appears in the room list. | completed | TBD |
| | 2.2 | **Invalid room.** *Given* a duplicate name, a capacity outside 1–2000, or an unknown type, *when* I submit, *then* I see an error and nothing is saved. | completed | TBD |
| | 2.3 | **Delete room.** *Given* a room not used by any schedule, *when* I delete it, *then* it is removed; *given* it is used by a schedule, *then* deletion is refused with an explanation. | completed | TBD |
| **3 Manage courses** | 3.1 | **Add course.** *Given* I am a coordinator, *when* I add a course with a unique code, a title, enrollment, lecture/lab hours and an optional instructor, *then* it appears in the course list (with the code upper-cased). | completed | TBD |
| | 3.2 | **Invalid course.** *Given* a duplicate code, zero total hours, non-numeric enrollment, or a non-instructor chosen as instructor, *when* I submit, *then* I see an error. | completed | TBD |
| | 3.3 | **Assign instructor.** *Given* a course, *when* I pick a different instructor or "unassigned", *then* the course's instructor is updated. | completed | TBD |
| | 3.4 | **Delete course.** *Given* a course not used by a schedule, *when* I delete it, *then* it and its no-overlap rules are removed; if it is used by a schedule, deletion is refused. | completed | TBD |
| **4 No-overlap** | 4.1 | **Add rule.** *Given* two different courses, *when* I mark them "must not overlap", *then* the rule is listed. | completed | TBD |
| | 4.2 | **Invalid rule.** *Given* the same course twice or a pair that already has a rule (in either order), *when* I submit, *then* I see an error. | completed | TBD |
| | 4.3 | **Rule enforced.** *Given* a no-overlap rule between A and B, *when* a schedule is generated, *then* no session of A shares a time slot with a session of B. | completed | TBD |
| **5 Preferences** | 5.1 | **Submit preferences.** *Given* I teach a course, *when* I submit lecture hours, lab hours, midterms, final exam, venue, preferred days and period, *then* they are saved, and submitting again updates them. | completed | TBD |
| | 5.2 | **Hours override defaults.** *Given* I submitted 4 lecture hours for a course whose default is 2, *when* a schedule is generated, *then* the course gets 4 lecture sessions. | completed | TBD |
| | 5.3 | **Only my courses.** *Given* a course taught by someone else, *when* I open or submit its preferences, *then* I get HTTP 403. | completed | TBD |
| | 5.4 | **Invalid preferences.** *Given* 0 total hours, more than 10 hours, "lab" as the lecture venue, an unknown period or an invalid day, *when* I submit, *then* I see an error. | completed | TBD |
| **6 Generate** | 6.1 | **All sessions placed.** *Given* rooms and courses exist, *when* I generate a schedule for a semester with valid dates, *then* a draft schedule is created with exactly one session per lecture hour and lab hour. | completed | TBD |
| | 6.2 | **Room constraints.** *Given* a generated schedule, *then* every session's room seats at least the course enrollment, labs are in lab rooms, lectures are never in lab rooms, and no room holds two sessions at once. | completed | TBD |
| | 6.3 | **People constraints.** *Given* a generated schedule, *then* no instructor teaches two sessions at once and no course has two sessions at once. | completed | TBD |
| | 6.4 | **Infeasible input.** *Given* a course with no room big enough, an overloaded instructor, too few rooms, or conflicting no-overlap rules, *when* I generate, *then* no schedule is saved and I see a message explaining why. | completed | TBD |
| | 6.5 | **Invalid input.** *Given* a missing semester name, an invalid date, an end date before the start date, or no courses, *when* I generate, *then* I see an error. | completed | TBD |
| **7 Preferences honoured** | 7.1 | **Preferences met when possible.** *Given* an instructor prefers certain days, a time of day and a venue type, and there is room for it, *when* I generate, *then* their sessions are placed accordingly. | completed | TBD |
| | 7.2 | **Spread over days.** *Given* a course with several weekly sessions, *when* I generate, *then* they are placed on different days when possible. | completed | TBD |
| | 7.3 | **Hard over soft.** *Given* preferences that cannot all be met, *when* I generate, *then* a schedule is still produced, all hard constraints hold, and every unmet preference is listed with a reason (⚠ in the timetable, with the count shown). | completed | TBD |
| **8 Adjust** | 8.1 | **Valid move.** *Given* a schedule, *when* I move a session to a free room and slot, *then* it is saved and the unmet-preference count is recalculated. | completed | TBD |
| | 8.2 | **Invalid move.** *Given* the target slot would double-book the room, instructor or course, break a no-overlap rule, or the room is too small or of the wrong type, *when* I move, *then* the move is refused with the reason. | completed | TBD |
| | 8.3 | **Bad values.** *Given* a day or hour outside the week grid, or a session not in this schedule, *when* I move, *then* I see an error or 404. | completed | TBD |
| **9 Publish & view** | 9.1 | **Publish.** *Given* a draft schedule, *when* I publish it, *then* it becomes the one visible to instructors and any previously published schedule is archived. | completed | TBD |
| | 9.2 | **Read-only view.** *Given* a published schedule, *when* an instructor opens "Timetable", *then* they see the full grid with their sessions highlighted and no edit controls. *Given* nothing is published, *then* they see "not published yet". | completed | TBD |
| | 9.3 | **Draft deletion.** *Given* a draft schedule, *when* I delete it, *then* it is removed; a published schedule cannot be deleted. | completed | TBD |
| **10 Change requests** | 10.1 | **Send request.** *Given* a published schedule, *when* I (an instructor) send a message about one of my sessions or a general comment, *then* it is saved as "pending" and shown in "My change requests". | completed | TBD |
| | 10.2 | **Request rules.** *Given* no published schedule, an empty message, or a session belonging to another instructor, *when* I send, *then* the request is refused. | completed | TBD |
| | 10.3 | **Respond.** *Given* a pending request, *when* a coordinator accepts or rejects it with an optional reply, *then* its status and reply are visible to the instructor, and it cannot be answered twice. The dashboard shows the number of pending requests. | completed | TBD |
| **11 Calendar export** | 11.1 | **Download .ics.** *Given* a published schedule, *when* I click "Add to my calendar", *then* I download a `text/calendar` file containing only my sessions as weekly events repeating until the semester's last day. | completed | TBD |
| | 11.2 | **Correct first date.** *Given* the semester starts on Monday 24 Aug 2026 and my session is on Wednesdays at 10:00, *then* the first event is on 26 Aug 2026 at 10:00. | completed | TBD |
| | 11.3 | **Import into Google Calendar.** *Given* the downloaded file, *when* I import it in Google Calendar (Settings → Import & export), *then* the classes appear on the correct weekdays and times. | completed (manual) | TBD |

---

## III. Implementation Tasks

### Summary of production code

| User Story | AC ID | Class / module | Method(s) | Developer | Status |
|---|---|---|---|---|---|
| 1 | 1.1–1.4 | `services`, `auth` | `register_user`, `authenticate`, `auth.register`, `auth.login`, `auth.logout` | TBD | completed |
| 1 | 1.5 | `auth` | `require_role`, `coordinator.only_coordinators`, `instructor.only_instructors` | TBD | completed |
| 2 | 2.1–2.3 | `services`, `coordinator` | `create_room`, `delete_room`, `coordinator.add_room`, `coordinator.delete_room` | TBD | completed |
| 3 | 3.1–3.4 | `services`, `coordinator` | `create_course`, `assign_instructor`, `delete_course` and the matching routes | TBD | completed |
| 4 | 4.1–4.2 | `services`, `coordinator` | `add_no_overlap`, `delete_no_overlap`, `coordinator.add_rule` | TBD | completed |
| 4 | 4.3 | `scheduler.Timetable` | `hard_violations` (H6) | TBD | completed |
| 5 | 5.1–5.4 | `services`, `instructor`, `models.Course` | `save_preference`, `instructor_course`, `instructor.preferences`, `effective_lecture_hours`/`effective_lab_hours` | TBD | completed |
| 6 | 6.1–6.5 | `scheduler`, `services` | `generate`, `check_capacity`, `room_suits`, `Timetable.hard_violations`, `build_problem`, `generate_schedule` | TBD | completed |
| 7 | 7.1–7.3 | `scheduler`, `services` | `Timetable.soft_violations`, `evaluate_soft`, `soft_report` | TBD | completed |
| 8 | 8.1–8.3 | `services`, `coordinator` | `move_session`, `coordinator.move_session` | TBD | completed |
| 9 | 9.1–9.3 | `services`, `coordinator`, `instructor` | `publish_schedule`, `delete_schedule`, `published_schedule`, `instructor.schedule`, `_timetable.html` macro | TBD | completed |
| 10 | 10.1–10.3 | `services`, `instructor`, `coordinator` | `create_change_request`, `respond_change_request`, `instructor.create_request`, `coordinator.respond` | TBD | completed |
| 11 | 11.1–11.3 | `services`, `instructor` | `instructor_calendar`, `instructor.calendar` | TBD | completed |

### Summary of automated test code (corresponding to acceptance criteria)

| User Story | AC ID | Test class (file) | Test method(s) | Description (input → expected output) | Status | Developer |
|---|---|---|---|---|---|---|
| 1 | 1.1 | test_routes.py | `test_register_instructor` | Valid instructor form → redirected to "My courses" | pass | TBD |
| 1 | 1.2 | test_routes.py | `test_register_coordinator_requires_code` | Wrong code → error; correct code → coordinator dashboard | pass | TBD |
| 1 | 1.3 | test_services.py, test_routes.py | `test_register_rejects_bad_input`, `test_register_rejects_duplicate`, `test_register_shows_validation_error` | Short username/password, bad role, duplicate → `ValidationError` / message on page | pass | TBD |
| 1 | 1.4 | test_services.py, test_routes.py | `test_register_and_authenticate`, `test_bad_login`, `test_logout` | Correct/incorrect password; logout → redirect | pass | TBD |
| 1 | 1.5 | test_routes.py | `test_instructor_cannot_access_coordinator_pages`, `test_coordinator_cannot_access_instructor_pages`, `test_anonymous_redirected`, `test_home_redirects_to_login` | Wrong role → 403; anonymous → 302 to login | pass | TBD |
| 2 | 2.1–2.2 | test_services.py, test_routes.py | `test_create_room_validation`, `test_coordinator_manages_rooms` | Duplicate/0 capacity/bad type → error; valid → listed | pass | TBD |
| 2 | 2.3 | test_services.py, test_routes.py | `test_cannot_delete_room_or_course_used_by_schedule`, `test_coordinator_manages_rooms` | Used room → refused; unused → deleted | pass | TBD |
| 3 | 3.1–3.2 | test_services.py | `test_create_course_validation` | "cs101" → "CS101"; duplicate/0 hours/non-instructor/"lots" → error | pass | TBD |
| 3 | 3.3 | test_services.py, test_routes.py | `test_assign_instructor`, `test_coordinator_manages_courses_and_rules` | Reassign / unassign → updated | pass | TBD |
| 3 | 3.4 | test_services.py | `test_delete_course_removes_its_rules`, `test_cannot_delete_room_or_course_used_by_schedule` | Rules removed with course; used course → refused | pass | TBD |
| 4 | 4.1–4.2 | test_services.py | `test_no_overlap_rules` | Stored in sorted order; duplicate (either order) / same course → error | pass | TBD |
| 4 | 4.3 | test_scheduler.py | `test_no_overlap_rule_is_respected`, `test_hard_violation_messages` | 3+3 sessions with rule → disjoint slots | pass | TBD |
| 5 | 5.1 | test_services.py, test_routes.py | `test_save_preference`, `test_instructor_submits_preferences` | Days [1,3], final exam on → saved; resubmit updates same record | pass | TBD |
| 5 | 5.2 | test_services.py | `test_preference_hours_override_course_defaults` | Pref 4 h, default 2 h → effective 4 | pass | TBD |
| 5 | 5.3 | test_services.py, test_routes.py | `test_instructor_cannot_set_preferences_for_others_course`, `test_instructor_cannot_edit_others_preferences` | Other's course → `PermissionDenied` / 403 | pass | TBD |
| 5 | 5.4 | test_services.py, test_routes.py | `test_preference_validation` (5 cases), `test_instructor_preference_validation_shown` | Invalid values → error message | pass | TBD |
| 6 | 6.1 | test_scheduler.py, test_services.py, test_routes.py | `test_every_session_is_placed_once`, `test_generate_schedule_places_every_session`, `test_generate_view_publish_schedule`, `test_seed_command_creates_schedulable_demo` | 3 courses → 6 sessions, 1 lab; demo data → 19 sessions | pass | TBD |
| 6 | 6.2 | test_scheduler.py | `test_room_suits` (5 boundary cases), `test_capacity_is_respected`, `test_labs_go_to_lab_rooms`, `test_room_never_double_booked` | Enrollment 100 vs 101 in a 100-seat room; 50 sessions in 1 room → 50 distinct slots | pass | TBD |
| 6 | 6.3 | test_scheduler.py | `test_instructor_never_double_booked`, `test_same_course_sessions_never_share_a_slot` | Same instructor/course → distinct slots | pass | TBD |
| 6 | 6.4 | test_scheduler.py, test_services.py, test_routes.py | `test_no_suitable_room_raises_clear_error`, `test_overloaded_instructor_fails_fast`, `test_too_few_rooms_fails_fast`, `test_infeasible_combination_found_by_search`, `test_search_limit_raises`, `test_generate_reports_infeasible`, `test_generate_shows_scheduling_error` | 900 students → "900 seats" error and nothing saved | pass | TBD |
| 6 | 6.5 | test_services.py | `test_generate_validates_input` (3 cases), `test_generate_requires_courses` | Empty name, bad date, end < start, no courses → error | pass | TBD |
| 7 | 7.1 | test_scheduler.py, test_services.py | `test_preferred_days_are_honoured_when_possible`, `test_preferred_period_morning_and_afternoon`, `test_preferred_venue_is_honoured`, `test_generate_uses_preferences` | Prefers Tue/Thu afternoon → placed Tue/Thu ≥ 12:00 | pass | TBD |
| 7 | 7.2 | test_scheduler.py | `test_sessions_spread_over_different_days` | 3 lectures → 3 different days | pass | TBD |
| 7 | 7.3 | test_scheduler.py | `test_unmeetable_preference_is_reported_not_fatal`, `test_hard_constraints_beat_soft_preferences` | 3 lectures, Monday only → schedule produced, penalty ≥ 2 | pass | TBD |
| 8 | 8.1 | test_services.py | `test_move_session_to_free_slot`, `test_move_session_updates_soft_penalty` | Move to Fri 17:00 → saved; penalty recalculated | pass | TBD |
| 8 | 8.2 | test_services.py, test_routes.py | `test_move_session_rejects_hard_conflict`, `test_move_session_rejects_small_room`, `test_move_session_conflict_is_shown` | Same slot as sibling session / 30-seat room for 60 → refused with reason | pass | TBD |
| 8 | 8.3 | test_services.py, test_routes.py | `test_move_session_invalid_input`, `test_missing_schedule_404` | Day 5, hour 20, unknown id → error / 404 | pass | TBD |
| 9 | 9.1 | test_services.py, test_routes.py | `test_publish_archives_previous`, `test_generate_view_publish_schedule` | Publish v2 → v1 archived | pass | TBD |
| 9 | 9.2 | test_routes.py | `test_instructor_sees_published_schedule_readonly`, `test_instructor_dashboard_without_schedule` | No "Move" controls; unpublished → message | pass | TBD |
| 9 | 9.3 | test_services.py, test_routes.py | `test_delete_schedule`, `test_cannot_delete_published_schedule`, `test_delete_draft_schedule` | Draft deleted; published refused | pass | TBD |
| 10 | 10.1 | test_services.py, test_routes.py | `test_change_request_flow`, `test_change_request_rejected`, `test_instructor_sends_change_request` | Request → "pending" | pass | TBD |
| 10 | 10.2 | test_services.py, test_routes.py | `test_change_request_rules`, `test_instructor_sends_change_request` | No schedule / other's session / blank → refused | pass | TBD |
| 10 | 10.3 | test_services.py, test_routes.py | `test_change_request_flow`, `test_coordinator_responds_to_request` | Accept/reject with reply; second answer refused; "1 change request waiting" | pass | TBD |
| 11 | 11.1 | test_services.py, test_routes.py | `test_instructor_calendar`, `test_instructor_downloads_calendar` | 3 own sessions → 3 VEVENTs, weekly RRULE, other's course absent | pass | TBD |
| 11 | 11.2 | test_services.py | `test_calendar_first_occurrence_on_correct_weekday` | Start Mon 24 Aug, Wed 10:00 → `DTSTART:20260826T100000` | pass | TBD |

### Summary of manual test cases

| User Story | AC ID | Test case input | Test oracle (expected output) | Status | Developer |
|---|---|---|---|---|---|
| 6, 7 | 6.1, 7.3 | Run `flask --app run seed`, log in as `coord`, generate "Fall 2026" | Timetable grid shows 19 sessions; CS5590 shows ⚠ "Mon is not a preferred day" (3 lectures but only 2 preferred days) | TBD | TBD |
| 8 | 8.2 | On the schedule page, move a lecture into the room/slot of another session | Red message "… is already booked at …"; the grid is unchanged | TBD | TBD |
| 9 | 9.2 | Publish, then log in as `smith` → Timetable | Smith's sessions outlined in green; no Move/Publish buttons | TBD | TBD |
| 11 | 11.3 | As `smith`, download .ics and import it into Google Calendar | Weekly CS5551/CS5520 events on the correct weekdays and times until 11 Dec 2026 | TBD | TBD |
| — | UI | Open each page at 375 px width (phone) | No horizontal page scroll except inside the timetable | TBD | TBD |

### Summary of other automated tests (not tied to an AC)

| # | Test input | Expected result | Test file | Test method | Status |
|---|---|---|---|---|---|
| 1 | `seed` command on a non-empty DB | Non-zero exit, data untouched | test_seed.py | `test_seed_refuses_non_empty_database` | pass |
| 2 | Any single session | Placed within 08:00–17:00 | test_scheduler.py | `test_slot_range` | pass |

**Totals:** 90 automated tests, all passing. Statement coverage is 98% (`pytest --cov=app`). CI runs on every push via GitHub Actions (Python 3.11–3.13).

---

## IV. Summary of Source Code

Lines are non-blank lines. **Fill in who wrote or integrated each file.** Each member needs **400 or more lines** credited to them.

| Production or test? | Source code file | # lines | Developer names and contributions (%) |
|---|---|---|---|
| Production | app/scheduler.py (algorithm) | 207 | TBD |
| Production | app/services.py (business logic) | 329 | TBD |
| Production | app/models.py | 114 | TBD |
| Production | app/coordinator.py | 128 | TBD |
| Production | app/instructor.py | 68 | TBD |
| Production | app/auth.py | 58 | TBD |
| Production | app/\_\_init\_\_.py, app/seed.py | 82 | TBD |
| Production | app/templates/ (10 files) | 420 | TBD |
| Production | app/static/style.css | 60 | TBD |
| Test | tests/test_scheduler.py | 143 | TBD |
| Test | tests/test_services.py | 208 | TBD |
| Test | tests/test_routes.py | 148 | TBD |
| Test | tests/conftest.py, tests/test_seed.py | 64 | TBD |
| | **Total** | **2,029** (1,466 production + 563 test) | |

**AI assistance:** Parts of this code were generated with an AI assistant (Claude Code). As the course requires, screenshots of the prompts and outputs are included in Appendix A. The team's changes to the AI output are described there: `TBD`.

---

## V. Meeting Minutes

| Date | Time and duration | Place | Participants | Purpose of the meeting | Specific action items |
|---|---|---|---|---|---|
| TBD | | | | Sprint 1 planning / effort estimation | |
| TBD | | | | Stand-up | |
| TBD | | | | Pair programming session | |
| TBD | | | | Sprint 1 retrospective | |

---

## VI. Buddy Ratings

| Rating giver ↓ / receiver → | TBD | TBD | TBD | TBD |
|---|---|---|---|---|
| TBD | X | | | |
| TBD | | X | | |
| TBD | | | X | |
| TBD | | | | X |
| *Average* | | | | |

---

## Appendix A — AI usage (required by the course)

*Paste screenshots of the prompts and outputs here, and describe how the team reviewed, tested and improved the generated code.*
