"""The demo data used in the sprint video must always produce a valid schedule."""
from app import services
from app.models import User


def test_seed_command_creates_schedulable_demo(app):
    result = app.test_cli_runner().invoke(args=["seed"])
    assert "Demo data created" in result.output
    assert User.query.count() == 4

    schedule = services.generate_schedule("Fall 2026", "2026-08-24", "2026-12-11")
    assert len(schedule.sessions) == 19
    assert schedule.soft_penalty <= 2


def test_seed_refuses_non_empty_database(app, instructor):
    result = app.test_cli_runner().invoke(args=["seed"])
    assert result.exit_code != 0
