"""Unit tests for follow-up scheduler helpers and jobs."""

from datetime import date

from app.tasks.followups import working_days_ago


# ── working_days_ago ─────────────────────────────────────────────────────────


def test_working_days_ago_skips_weekend():
    """Monday minus 1 working day is Friday, not Sunday."""
    monday = date(2026, 5, 4)  # Mon
    assert working_days_ago(1, monday) == date(2026, 5, 1)  # Fri


def test_working_days_ago_five_back_from_friday():
    """Friday minus 5 working days is the previous Friday."""
    friday = date(2026, 5, 8)
    assert working_days_ago(5, friday) == date(2026, 5, 1)


def test_working_days_ago_from_weekend_walks_through_friday():
    saturday = date(2026, 5, 9)
    # 1 working day before Saturday is Friday May 8
    assert working_days_ago(1, saturday) == date(2026, 5, 8)


def test_working_days_ago_zero_returns_today():
    today = date(2026, 5, 7)
    assert working_days_ago(0, today) == today
