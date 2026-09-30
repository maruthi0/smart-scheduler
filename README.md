# Course Scheduler

A university course-scheduling web app for the CS 5551 team project (Project 2: Event Scheduling App).

- **Coordinators** manage rooms, courses and "no-overlap" rules. They **generate a semester timetable automatically**, adjust it, publish it, and answer instructors' change requests.
- **Instructors** submit teaching preferences (lecture/lab hours, midterms, final exam, venue, days, time of day). They view the published timetable read-only, request changes, and export their schedule to Google Calendar, Outlook or Apple Calendar (.ics).
- The generator **always satisfies the hard constraints** (room capacity and type, no double-booking, no-overlap rules). It **satisfies as many soft constraints (preferences) as it can** and lists the ones it could not meet.

## Run it

```powershell
python -m venv .venv
.\.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
flask --app run seed              # optional: demo rooms, courses and users
python run.py
```

Open <http://127.0.0.1:5000>. The demo logins are `coord` (coordinator) and `smith`, `jones`, `lee` (instructors). The password for all of them is `password`.

To register a new coordinator you need the access code (default `coordinator-demo`, set with `COORDINATOR_CODE`).

To reset the data, delete `instance/scheduler.db`.

## Test

```powershell
pytest --cov=app --cov-report=term-missing
```

## Project structure

```
app/
  scheduler.py      constraint-based timetable generator (pure Python)
  services.py       business rules, validation, permissions
  models.py         SQLAlchemy models
  auth.py           register / login / role checks
  coordinator.py    coordinator pages
  instructor.py     instructor pages + .ics export
  seed.py           demo data (flask --app run seed)
  templates/, static/
tests/              unit + integration tests
docs/
  sprint1_report.md user stories, Given-When-Then acceptance criteria, test mapping
  design.md         architecture, UML, algorithm
.github/workflows/ci.yml
```

## Configuration

| Env var | Default |
|---|---|
| `SECRET_KEY` | `dev-change-me` (**change this in production**) |
| `DATABASE_URL` | `sqlite:///instance/scheduler.db` |
| `COORDINATOR_CODE` | `coordinator-demo` |
