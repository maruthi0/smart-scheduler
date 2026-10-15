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
copy .env.example .env            # macOS/Linux: cp .env.example .env, then fill in the values
flask --app run seed              # optional: demo rooms, courses and users
python run.py
```

The app will not start until `SECRET_KEY` and `COORDINATOR_CODE` are set in `.env` (see [Configuration](#configuration)).

Open <http://127.0.0.1:5000>. The demo logins are `coord` (coordinator) and `smith`, `jones`, `lee` (instructors). Their password is `DEMO_PASSWORD` from `.env` (`password` by default).

To register a new coordinator you need the access code `COORDINATOR_CODE` from `.env`.

To reset the data, drop and recreate the database (PostgreSQL) or delete `instance/scheduler.db` (SQLite).

## Test

```powershell
pytest --cov=app --cov-report=term-missing
```

## Project structure

The app is a **monolith**: one Flask application, deployed and run as a single process. Inside it, the code is split into a backend and a frontend package.

```
app/
  __init__.py       application factory: wires backend + frontend together
  config.py         settings from environment variables (.env)
  backend/          data, business rules, algorithm (no routes or templates)
    models.py       SQLAlchemy models
    services.py     business rules, validation, permissions
    scheduler.py    constraint-based timetable generator (pure Python)
    seed.py         demo data (flask --app run seed)
  frontend/         what the user sees (no business rules)
    auth.py         register / login / role checks
    coordinator.py  coordinator pages
    instructor.py   instructor pages + .ics export
    templates/      Jinja HTML templates
    static/         CSS
tests/              unit + integration tests
.env.example        template for .env (the real .env is git-ignored)
docs/
  sprint1_report.md user stories, Given-When-Then acceptance criteria, test mapping
  design.md         architecture, UML, algorithm
.github/workflows/ci.yml
```

## Configuration

All settings come from environment variables. `run.py` loads them from `.env`. Copy `.env.example` to `.env`; never commit `.env`.

| Env var | Required | Purpose | Default |
|---|---|---|---|
| `SECRET_KEY` | yes | Signs the login session cookie. Generate with `python -c "import secrets; print(secrets.token_hex(32))"` | none |
| `COORDINATOR_CODE` | yes | Access code for registering a coordinator | none |
| `FLASK_DEBUG` | no | `1` for auto-reload and debugger (local only) | `0` |
| `DATABASE_URL` | no | Database connection string, e.g. `postgresql://scheduler:PASSWORD@localhost:5432/scheduler` | SQLite file `instance/scheduler.db` |
| `DEMO_PASSWORD` | no | Password of the seeded demo accounts | `password` |
| `SESSION_COOKIE_SECURE` | no | `1` when served over HTTPS | `0` |

All forms are protected against CSRF (Flask-WTF), and the session cookie uses `SameSite=Lax`.

## Database

The app uses **PostgreSQL** when `DATABASE_URL` is set, and falls back to a local **SQLite** file when it is empty. Tables are created automatically on start-up.

**Set up PostgreSQL once** (any PostgreSQL 14+ server, local or hosted):

```sql
-- run as the postgres superuser, e.g. psql -U postgres
CREATE ROLE scheduler LOGIN PASSWORD 'choose-a-strong-password';
CREATE DATABASE scheduler OWNER scheduler;
CREATE DATABASE scheduler_test OWNER scheduler;   -- optional, for tests
```

Then put the URL in `.env`:

```
DATABASE_URL=postgresql://scheduler:choose-a-strong-password@localhost:5432/scheduler
```

`postgres://` and `postgresql://` URLs are both accepted; the app uses the psycopg 3 driver automatically. If the password contains `@`, `:` or `/`, URL-encode it.

**Tests** use an in-memory SQLite database by default. To run them against PostgreSQL:

```powershell
$env:TEST_DATABASE_URL = "postgresql://scheduler:PASSWORD@localhost:5432/scheduler_test"
pytest
```

CI runs the suite on SQLite (Python 3.11–3.13) and on PostgreSQL 18.
