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
| A1 | Who may use the portal? | Only pre-assigned instructors and coordinators. There is no public registration. Accounts come from a git-ignored file loaded with `flask --app run load-accounts`. |
| A2 | What is a "time slot"? | One-hour blocks, Monday–Friday, starting 08:00–17:00, which gives 50 slots per week. Each lecture hour or lab hour is one session. |
| A3 | Which constraints are hard? | Room capacity, room type (labs in lab rooms), no double-booking of rooms or instructors, no two sessions of one course at once, coordinator-defined *no-overlap* course pairs, and times an instructor marked unavailable. |
| A4 | Which constraints are soft? | Instructor-preferred days, time of day (morning/afternoon) and venue type, plus spreading a course's sessions over different days. |
| A5 | Are "lecture hours/week" preferences or requirements? | Coordinators set each course's hours and they are always honoured (they are a requirement). Instructors cannot change them. Day, time and venue are soft preferences. |
| A6 | What happens to #midterms and final-exam information? | It is recorded and shown to coordinators. Exam scheduling is a may-have for a later sprint (US-14). |
| A7 | How does linking to Google Calendar work? | The app exports a standard iCalendar (.ics) file with weekly recurring events, which Google Calendar, Outlook and Apple Calendar all import. Direct OAuth sync is a may-have (US-12). |
| A8 | "Instructors should not modify the schedule." | Instructors see a read-only timetable. They can file change requests, which coordinators accept or reject; only coordinators move sessions. |

---

## I. User Stories

Priority: **Must** = must-have (required for the primitive functions); **May** = implement if time allows.

| ID | User Story Name | User Story Description | Priority | Est. effort (h) | Actual effort | Status | Developer names |
|---|---|---|---|---|---|---|---|
| 1 | Accounts & roles | As a **user**, I want to log in with my pre-assigned coordinator or instructor account, so that only department staff can enter and I only see the functions for my role. | Must | 6 | | completed | TBD |
| 2 | Manage rooms | As a **coordinator**, I want to add and remove rooms with their capacity and type, so that the scheduler knows which venues exist. | Must | 4 | | completed | TBD |
| 3 | Manage courses | As a **coordinator**, I want to add courses with enrollment, lecture/lab hours and an instructor, and change their hours later, so that they can be scheduled. | Must | 6 | | completed | TBD |
| 4 | No-overlap constraints | As a **coordinator**, I want to mark pairs of courses that must never run at the same time, so that students in the same cohort can take both. | Must | 4 | | completed | TBD |
| 5 | Instructor preferences | As an **instructor**, I want to submit my number of midterms, final exam, preferred venue, days and time of day, so that the schedule suits my teaching without emailing the coordinator. | Must | 6 | | completed | TBD |
| 6 | Generate schedule | As a **coordinator**, I want to generate a semester timetable automatically that satisfies all hard constraints, so that I don't have to build it by hand. | Must | 16 | | completed | TBD |
| 7 | Honour preferences | As a **coordinator**, I want the generator to satisfy as many instructor preferences as possible and show me the ones it could not meet, so that the schedule is fair and I can explain trade-offs. | Must | 8 | | completed | TBD |
| 8 | Adjust schedule | As a **coordinator**, I want to move a session to another room or time and be told if that breaks a hard constraint, so that I can fine-tune the result safely. | Must | 6 | | completed | TBD |
| 9 | Publish & view | As a **coordinator**, I want to publish a schedule so that instructors can view it, and as an **instructor** I want a read-only timetable with my sessions highlighted. | Must | 5 | | completed | TBD |
| 10 | Change requests | As an **instructor**, I want to suggest a change to one of my sessions, and as a **coordinator** I want to accept or reject it with a reply, so that we can communicate without email. | Must | 6 | | completed | TBD |
| 11 | Calendar export | As an **instructor**, I want to add my teaching schedule to my personal calendar (e.g. Google Calendar), so that I see my classes alongside my other events. | May | 4 | | completed | TBD |
| 12 | Google Calendar sync | As an **instructor**, I want my Google Calendar updated automatically when the schedule changes, so that I never have an outdated copy. | May | 12 | | toDo | |
| 13 | Notifications | As an **instructor**, I want to be notified when a schedule is published or my request is answered, so that I don't have to keep checking. | May | 6 | | toDo | |
| 14 | Exam scheduling | As a **coordinator**, I want midterm and final exam slots generated from instructors' exam preferences, so that exams don't clash. | May | 12 | | toDo | |
| 15 | Instructor unavailability | As an **instructor**, I want to mark times I am unavailable as a hard constraint, so that I am never scheduled then. | May | 5 | | completed | TBD |
| 16 | Secure configuration | As a **coordinator**, I want the app's secrets kept out of the source code and every form protected against forged requests, so that nobody can impersonate me or change schedules without my action. | Must | 4 | | completed | TBD |
| 17 | Instructor workload | As an **instructor**, I want to see each instructor's hour limit, assigned hours and hours left, and as a **coordinator** I want to set those limits and be warned when I exceed them, so that teaching load is visible to everyone. | Must | 4 | | completed | TBD |
| 18 | Account security | As a **user**, I want to choose my own password, be protected from password guessing and have my sessions end when my password changes, and as a **coordinator** I want to reset a forgotten password, so that only the right people can use an account. | Must | 6 | | completed | TBD |

---

## II. Acceptance Criteria (Given-When-Then)

| User Story | AC ID | Description of Acceptance Criterion | Status | Developer |
|---|---|---|---|---|
| **1 Accounts & roles** | 1.1 | **No public registration.** *Given* I have no account, *when* I open or post to `/register`, *then* I get HTTP 404, no account is created, and the login page offers no way to register. | completed | TBD |
| | 1.2 | **Pre-assigned accounts.** *Given* an accounts file, *when* it is loaded, *then* every listed person can log in with their listed password and role, and an account not listed can no longer log in but keeps its courses. | completed | TBD |
| | 1.3 | **Invalid accounts file.** *Given* a username or password that is too short, an unknown role, or an empty file, *when* it is loaded, *then* I see an error and no account changes. | completed | TBD |
| | 1.4 | **Login/logout.** *Given* a registered user, *when* they enter the correct password, *then* they are signed in; *when* the password is wrong, *then* they see "Invalid username or password"; *when* they log out, *then* protected pages redirect to login. | completed | TBD |
| | 1.5 | **Role separation.** *Given* I am logged in as an instructor, *when* I open any coordinator page, *then* I get HTTP 403 (and vice versa). *Given* I am not logged in, *then* I am redirected to login. | completed | TBD |
| **2 Manage rooms** | 2.1 | **Add room.** *Given* I am a coordinator, *when* I add a room with a unique name, capacity 1–2000 and a type (theater, lecture hall, small room, lab), *then* it appears in the room list. | completed | TBD |
| | 2.2 | **Invalid room.** *Given* a duplicate name, a capacity outside 1–2000, or an unknown type, *when* I submit, *then* I see an error and nothing is saved. | completed | TBD |
| | 2.3 | **Delete room.** *Given* a room not used by any schedule, *when* I delete it, *then* it is removed; *given* it is used by a schedule, *then* deletion is refused with an explanation. | completed | TBD |
| **3 Manage courses** | 3.1 | **Add course.** *Given* I am a coordinator, *when* I add a course with a unique code, a title, enrollment, lecture/lab hours and an optional instructor, *then* it appears in the course list (with the code upper-cased). | completed | TBD |
| | 3.2 | **Invalid course.** *Given* a duplicate code, zero total hours, non-numeric enrollment, or a non-instructor chosen as instructor, *when* I submit, *then* I see an error. | completed | TBD |
| | 3.3 | **Edit hours.** *Given* I am a coordinator, *when* I change a course's lecture or lab hours to valid values, *then* the next generated schedule uses them; invalid values show an error and change nothing. Instructors get HTTP 403. | completed | TBD |
| | 3.3 | **Assign instructor.** *Given* a course, *when* I pick a different instructor or "unassigned", *then* the course's instructor is updated. | completed | TBD |
| | 3.4 | **Delete course.** *Given* a course not used by a schedule, *when* I delete it, *then* it and its no-overlap rules are removed; if it is used by a schedule, deletion is refused. | completed | TBD |
| **4 No-overlap** | 4.1 | **Add rule.** *Given* two different courses, *when* I mark them "must not overlap", *then* the rule is listed. | completed | TBD |
| | 4.2 | **Invalid rule.** *Given* the same course twice or a pair that already has a rule (in either order), *when* I submit, *then* I see an error. | completed | TBD |
| | 4.3 | **Rule enforced.** *Given* a no-overlap rule between A and B, *when* a schedule is generated, *then* no session of A shares a time slot with a session of B. | completed | TBD |
| **5 Preferences** | 5.1 | **Submit preferences.** *Given* I teach a course, *when* I submit midterms, final exam, venue, preferred days and period, *then* they are saved, and submitting again updates them. | completed | TBD |
| | 5.2 | **Hours stay with the coordinator.** *Given* a course set to 2 lecture hours, *when* I submit preferences with 4 lecture hours and a schedule is generated, *then* the course still gets 2 lecture sessions. | completed | TBD |
| | 5.3 | **Only my courses.** *Given* a course taught by someone else, *when* I open or submit its preferences, *then* I get HTTP 403. | completed | TBD |
| | 5.4 | **Invalid preferences.** *Given* "lab" as the lecture venue, an unknown period or an invalid day, *when* I submit, *then* I see an error. | completed | TBD |
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
| **16 Secure configuration** | 16.1 | **Secrets from the environment.** *Given* `SECRET_KEY` is not set, *when* the app starts, *then* it refuses to start and names the missing setting; *given* it is set in `.env`, *then* the app uses that value. | completed | TBD |
| | 16.2 | **CSRF protection.** *Given* any form, *when* it is submitted without a valid CSRF token, *then* the request is rejected with HTTP 400 and nothing changes; *when* the token is present, *then* the form works as before. | completed | TBD |
| | 16.3 | **Safe defaults.** *Given* the default settings, *then* the session cookie is `SameSite=Lax`, it is `Secure` when `SESSION_COOKIE_SECURE=1`, and debug mode is on only when `FLASK_DEBUG=1`. | completed | TBD |
| **17 Instructor workload** | 17.1 | **See workload.** *Given* I am logged in, *when* I open my dashboard, *then* I see every instructor's hour limit, assigned lecture and lab hours, and hours left, with "over by N" when assigned hours exceed the limit. | completed | TBD |
| | 17.2 | **Set limit.** *Given* I am a coordinator, *when* I set an instructor's limit to 0–60, *then* it is saved; other values show an error and change nothing. Instructors see no edit field and get HTTP 403. | completed | TBD |
| | 17.3 | **Over-limit warning.** *Given* I am a coordinator, *when* I choose an instructor, *then* the list shows their hours left; *when* a save puts them over their limit, *then* it is saved and I see a warning. | completed | TBD |
| **15 Instructor unavailability** | 15.1 | **Mark times.** *Given* I am an instructor, *when* I save the times I cannot teach, *then* they replace my previous choices; invalid slots show an error, and at least as many slots as I teach must stay free. | completed | TBD |
| | 15.2 | **Hard constraint.** *Given* I marked a time unavailable, *when* a schedule is generated, *then* none of my sessions are placed there, and a coordinator who tries to move one there is refused. | completed | TBD |
| **18 Account security** | 18.1 | **First-login change.** *Given* my password was assigned, *when* I log in, *then* I can only change my password or log out until I choose a new one of 10–128 characters. | completed | TBD |
| | 18.2 | **Login throttling.** *Given* 5 failed logins for a username, *when* anyone tries again within 15 minutes, *then* they see "Too many failed attempts" (HTTP 429), even with the right password. | completed | TBD |
| | 18.3 | **Sessions.** *Given* my password changes or my account is locked, *then* my other sessions end. *Given* 2 idle hours, *then* my session has expired. | completed | TBD |
| | 18.4 | **Reset.** *Given* I am a coordinator, *when* I reset another active account's password, *then* a temporary password is shown once and must be changed at login. Instructors get HTTP 403. | completed | TBD |
| | 18.5 | **Hardening.** *Given* any response, *then* it carries security headers and no template contains inline scripts; `seed` refuses to run when the site is served over HTTPS; `pip-audit` runs in CI. | completed | TBD |

---

## III. Implementation Tasks

### Summary of production code

| User Story | AC ID | Class / module | Method(s) | Developer | Status |
|---|---|---|---|---|---|
| 1 | 1.1–1.4 | `services`, `auth` | `register_user`, `sync_accounts`, `load-accounts` command, `authenticate`, `auth.login`, `auth.logout` | TBD | completed |
| 1 | 1.5 | `auth` | `require_role`, `coordinator.only_coordinators`, `instructor.only_instructors` | TBD | completed |
| 2 | 2.1–2.3 | `services`, `coordinator` | `create_room`, `delete_room`, `coordinator.add_room`, `coordinator.delete_room` | TBD | completed |
| 3 | 3.1–3.4 | `services`, `coordinator` | `create_course`, `assign_instructor`, `delete_course` and the matching routes | TBD | completed |
| 4 | 4.1–4.2 | `services`, `coordinator` | `add_no_overlap`, `delete_no_overlap`, `coordinator.add_rule` | TBD | completed |
| 4 | 4.3 | `scheduler.Timetable` | `hard_violations` (H6) | TBD | completed |
| 5 | 5.1–5.4 | `services`, `instructor` | `save_preference`, `instructor_course`, `instructor.preferences` | TBD | completed |
| 6 | 6.1–6.5 | `scheduler`, `services` | `generate`, `check_capacity`, `room_suits`, `Timetable.hard_violations`, `build_problem`, `generate_schedule` | TBD | completed |
| 7 | 7.1–7.3 | `scheduler`, `services` | `Timetable.soft_violations`, `evaluate_soft`, `soft_report` | TBD | completed |
| 8 | 8.1–8.3 | `services`, `coordinator` | `move_session`, `coordinator.move_session` | TBD | completed |
| 9 | 9.1–9.3 | `services`, `coordinator`, `instructor` | `publish_schedule`, `delete_schedule`, `published_schedule`, `instructor.schedule`, `_timetable.html` macro | TBD | completed |
| 10 | 10.1–10.3 | `services`, `instructor`, `coordinator` | `create_change_request`, `respond_change_request`, `instructor.create_request`, `coordinator.respond` | TBD | completed |
| 11 | 11.1–11.3 | `services`, `instructor` | `instructor_calendar`, `instructor.calendar` | TBD | completed |
| 16 | 16.1–16.3 | `config`, `app` (factory), templates | `load_config`, `create_app` (`CSRFProtect`), `csrf_token` field in every form | TBD | completed |
| 17 | 17.1–17.3 | `services`, `coordinator`, `instructor`, `app` (factory), `_workload.html` | `workloads`, `set_max_hours`, `coordinator.set_max_hours`, `_warn_if_over_limit`, `_add_missing_columns` | TBD | completed |
| 15 | 15.1–15.2 | `scheduler`, `services`, `instructor`, `models` | `Timetable.hard_violations`, `check_capacity`, `save_unavailability`, `instructor.availability`, `Unavailability` | TBD | completed |
| 18 | 18.1–18.5 | `services`, `auth`, `coordinator`, `app` (factory), `seed`, `static/app.js` | `change_password`, `reset_password`, `authenticate`, `load_current_user`, `_add_security_headers`, `seed_demo` | TBD | completed |

### Summary of automated test code (corresponding to acceptance criteria)

| User Story | AC ID | Test class (file) | Test method(s) | Description (input → expected output) | Status | Developer |
|---|---|---|---|---|---|---|
| 1 | 1.1 | test_routes.py | `test_registration_is_removed` | GET/POST `/register` → 404, no user created; login page has no Register link | pass | TBD |
| 1 | 1.2 | test_services.py | `test_sync_accounts_creates_updates_and_locks`, `test_load_accounts_command` | New and existing rows log in with the file's password; unlisted account locked, its courses kept | pass | TBD |
| 1 | 1.3 | test_services.py | `test_register_rejects_bad_input`, `test_register_rejects_duplicate`, `test_sync_accounts_rejects_bad_row_without_changes`, `test_sync_accounts_refuses_empty_list`, `test_load_accounts_command_reports_bad_file` | Short username/password, bad role, duplicate, empty file → `ValidationError`; nothing changes | pass | TBD |
| 1 | 1.4 | test_services.py, test_routes.py | `test_register_and_authenticate`, `test_bad_login`, `test_logout` | Correct/incorrect password; logout → redirect | pass | TBD |
| 1 | 1.5 | test_routes.py | `test_instructor_cannot_access_coordinator_pages`, `test_coordinator_cannot_access_instructor_pages`, `test_anonymous_redirected`, `test_home_redirects_to_login` | Wrong role → 403; anonymous → 302 to login | pass | TBD |
| 2 | 2.1–2.2 | test_services.py, test_routes.py | `test_create_room_validation`, `test_coordinator_manages_rooms` | Duplicate/0 capacity/bad type → error; valid → listed | pass | TBD |
| 2 | 2.3 | test_services.py, test_routes.py | `test_cannot_delete_room_or_course_used_by_schedule`, `test_coordinator_manages_rooms` | Used room → refused; unused → deleted | pass | TBD |
| 3 | 3.1–3.2 | test_services.py | `test_create_course_validation` | "cs101" → "CS101"; duplicate/0 hours/non-instructor/"lots" → error | pass | TBD |
| 3 | 3.3 | test_services.py, test_routes.py | `test_coordinator_sets_course_hours`, `test_set_course_hours_validation`, `test_coordinator_edits_course_hours`, `test_instructor_cannot_set_course_or_instructor` | 3 h → 3 sessions; 0 h/11 h/"many" → error; instructor → 403 | pass | TBD |
| 3 | 3.3 | test_services.py, test_routes.py | `test_assign_instructor`, `test_coordinator_manages_courses_and_rules` | Reassign / unassign → updated | pass | TBD |
| 3 | 3.4 | test_services.py | `test_delete_course_removes_its_rules`, `test_cannot_delete_room_or_course_used_by_schedule` | Rules removed with course; used course → refused | pass | TBD |
| 4 | 4.1–4.2 | test_services.py | `test_no_overlap_rules` | Stored in sorted order; duplicate (either order) / same course → error | pass | TBD |
| 4 | 4.3 | test_scheduler.py | `test_no_overlap_rule_is_respected`, `test_hard_violation_messages` | 3+3 sessions with rule → disjoint slots | pass | TBD |
| 5 | 5.1 | test_services.py, test_routes.py | `test_save_preference`, `test_instructor_submits_preferences` | Days [1,3], final exam on → saved; resubmit updates same record | pass | TBD |
| 5 | 5.2 | test_services.py | `test_instructor_cannot_change_course_hours` | Submitted 4 h, course 2 h → 2 sessions | pass | TBD |
| 5 | 5.3 | test_services.py, test_routes.py | `test_instructor_cannot_set_preferences_for_others_course`, `test_instructor_cannot_edit_others_preferences` | Other's course → `PermissionDenied` / 403 | pass | TBD |
| 5 | 5.4 | test_services.py, test_routes.py | `test_preference_validation` (3 cases), `test_instructor_preference_validation_shown` | Invalid values → error message | pass | TBD |
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
| 16 | 16.1 | test_security.py | `test_app_refuses_to_start_without_secret_key`, `test_settings_are_read_from_environment`, `test_demo_accounts_use_password_from_config` | Missing `SECRET_KEY` → `RuntimeError`; values from the environment → app config | pass | TBD |
| 16 | 16.2 | test_security.py | `test_post_without_csrf_token_is_rejected`, `test_post_with_csrf_token_is_accepted` | Login POST without token → 400; with token → 302 | pass | TBD |
| 16 | 16.3 | test_security.py | `test_settings_are_read_from_environment` | `SESSION_COOKIE_SECURE=1` → Secure cookie; SameSite is Lax | pass | TBD |
| 17 | 17.1 | test_services.py, test_routes.py, test_security.py | `test_workloads_show_limit_assigned_and_left`, `test_instructor_sees_every_workload_but_cannot_edit`, `test_existing_database_gains_hour_limit_and_keeps_users` | Limit 12, 3 assigned → 9 left; limit 2, 3 assigned → over by 1; old database gains the column and keeps its users | pass | TBD |
| 17 | 17.2 | test_services.py, test_routes.py | `test_coordinator_sets_hour_limit`, `test_set_max_hours_validation`, `test_set_max_hours_only_for_instructors`, `test_instructor_sees_every_workload_but_cannot_edit` | 2 → saved; 61/"many"/coordinator → error; instructor → 403 | pass | TBD |
| 17 | 17.3 | test_routes.py | `test_coordinator_warned_when_changes_exceed_limit`, `test_no_limit_warning_within_limit_or_on_failure` | Limit 3, 4 assigned → saved, "over their limit by 1"; within limit or failed save → no warning | pass | TBD |
| 15 | 15.1 | test_services.py, test_routes.py | `test_instructor_saves_availability`, `test_save_unavailability_replaces_previous_slots`, `test_save_unavailability_validation`, `test_save_unavailability_keeps_enough_free_slots` | Resave replaces; "5-9"/"0-18"/"junk" → error; all 50 blocked with 3 hours taught → error | pass | TBD |
| 15 | 15.2 | test_scheduler.py, test_services.py | `test_unavailable_slots_are_never_used`, `test_unavailable_slot_is_a_hard_violation`, `test_too_little_availability_fails_fast`, `test_generate_never_uses_unavailable_slots`, `test_move_session_rejects_unavailable_slot` | Mornings blocked → all sessions from 12:00; move to blocked slot → `ConflictError` | pass | TBD |
| 18 | 18.1 | test_security.py | `test_assigned_password_must_be_changed_before_anything_else`, `test_can_log_out_during_forced_password_change`, `test_change_password_validation`, `test_new_password_must_differ` | Other pages redirect to `/password`; short, mismatched or wrong current password → error | pass | TBD |
| 18 | 18.2 | test_security.py | `test_login_locked_after_repeated_failures`, `test_login_works_again_after_lockout_expires`, `test_successful_login_clears_failures`, `test_unknown_username_is_throttled_the_same_way`, `test_old_failed_logins_are_removed` | 5 failures → 429 even with the right password; expired → works | pass | TBD |
| 18 | 18.3 | test_security.py | `test_changing_password_ends_other_sessions`, `test_locked_account_loses_its_open_session`, `test_session_expires_after_idle_time` | Second session redirected to login; cookie has an expiry | pass | TBD |
| 18 | 18.4 | test_security.py | `test_coordinator_resets_a_password`, `test_coordinator_cannot_reset_own_or_locked_account`, `test_instructor_cannot_reset_passwords` | Temporary password works once set; own/locked → error; instructor → 403 | pass | TBD |
| 18 | 18.5 | test_security.py, test_seed.py | `test_security_headers`, `test_https_only_header_when_served_over_https`, `test_logged_in_pages_are_not_cached`, `test_templates_have_no_inline_scripts`, `test_delete_prompt_cannot_run_a_crafted_name`, `test_seed_refuses_deployed_site` | Headers present; no inline scripts; crafted room name stays escaped; `seed` over HTTPS → refused | pass | TBD |

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

**Totals:** 98 automated tests, all passing. Statement coverage is 98% (`pytest --cov=app`). CI runs on every push via GitHub Actions (Python 3.11–3.13 on SQLite, and on PostgreSQL 18, the production database).

---

## IV. Summary of Source Code

Lines are non-blank lines. **Fill in who wrote or integrated each file.** Each member needs **400 or more lines** credited to them.

| Production or test? | Source code file | # lines | Developer names and contributions (%) |
|---|---|---|---|
| Production (backend) | app/backend/scheduler.py (algorithm) | 207 | TBD |
| Production (backend) | app/backend/services.py (business logic) | 329 | TBD |
| Production (backend) | app/backend/models.py | 114 | TBD |
| Production (frontend) | app/frontend/coordinator.py | 128 | TBD |
| Production (frontend) | app/frontend/instructor.py | 68 | TBD |
| Production (frontend) | app/frontend/auth.py, app/frontend/errors.py | 76 | TBD |
| Production | app/\_\_init\_\_.py, app/config.py, app/backend/seed.py, package files | 120 | TBD |
| Production (frontend) | app/frontend/templates/ (11 files) | 475 | TBD |
| Production (frontend) | app/frontend/static/style.css | 205 | TBD |
| Test | tests/test_scheduler.py | 143 | TBD |
| Test | tests/test_services.py | 208 | TBD |
| Test | tests/test_routes.py | 156 | TBD |
| Test | tests/test_security.py | 61 | TBD |
| Test | tests/conftest.py, tests/test_seed.py | 68 | TBD |
| | **Total** | **2,357** (1,721 production + 636 test) | |

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
