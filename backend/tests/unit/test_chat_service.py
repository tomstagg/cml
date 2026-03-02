"""Unit tests for app/services/chat.py — no DB required."""

import pytest

from app.services.chat import (
    PROBATE_QUESTIONS,
    get_complexity_flags,
    get_estate_value_midpoint,
    get_first_question,
    get_next_question,
    is_flow_complete,
)

ALL_13_ANSWERS = {
    "service_type": "full_administration",
    "estate_value": "100k_325k",
    "has_will": "yes",
    "iht400": "no",
    "uk_domiciled": "yes",
    "uk_property_count": "1",
    "bank_account_count": "1_3",
    "investments_count": "simple",
    "overseas_assets": "no",
    "beneficiary_count": "1_2",
    "location": "SW1A 1AA",
    "location_preference": "local",
    "ranking_preference": "balanced",
}


def test_get_first_question_returns_step_1():
    q = get_first_question()
    assert q["step"] == 1
    assert q["id"] == "service_type"
    assert q["type"] == "single_choice"


def test_get_next_question_advances_sequentially():
    """Stepping through all questions returns each in order."""
    q = get_first_question()
    answers = {}
    for i in range(1, len(PROBATE_QUESTIONS)):
        nxt = get_next_question(q["id"], answers)
        assert nxt is not None
        assert nxt["step"] == i + 1
        q = nxt


def test_get_next_question_after_last_returns_none():
    last = PROBATE_QUESTIONS[-1]
    result = get_next_question(last["id"], ALL_13_ANSWERS)
    assert result is None


def test_get_next_question_unknown_id_returns_none():
    assert get_next_question("nonexistent_question", {}) is None


def test_is_flow_complete_empty_answers():
    assert is_flow_complete({}) is False


def test_is_flow_complete_partial_answers():
    partial = {"service_type": "grant_only", "estate_value": "100k_325k"}
    assert is_flow_complete(partial) is False


def test_is_flow_complete_all_13_answers():
    assert is_flow_complete(ALL_13_ANSWERS) is True


def test_estate_value_midpoints():
    assert get_estate_value_midpoint("under_100k") == 75_000
    assert get_estate_value_midpoint("100k_325k") == 212_500
    assert get_estate_value_midpoint("325k_650k") == 487_500
    assert get_estate_value_midpoint("650k_1m") == 825_000
    assert get_estate_value_midpoint("over_1m") == 1_500_000


def test_estate_value_midpoint_unknown_band_returns_default():
    assert get_estate_value_midpoint("invalid_band") == 212_500


def test_get_complexity_flags_extracts_all_fields():
    flags = get_complexity_flags(ALL_13_ANSWERS)
    assert flags["service_type"] == "full_administration"
    assert flags["estate_value"] == 212_500
    assert flags["estate_value_band"] == "100k_325k"
    assert flags["has_iht400"] is False
    assert flags["has_overseas_assets"] is False
    assert flags["has_complex_investments"] is False
    assert flags["postcode"] == "SW1A 1AA"
    assert flags["ranking_preference"] == "balanced"


def test_get_complexity_flags_iht400_yes():
    answers = {**ALL_13_ANSWERS, "iht400": "yes"}
    flags = get_complexity_flags(answers)
    assert flags["has_iht400"] is True


def test_get_complexity_flags_overseas_assets_yes():
    answers = {**ALL_13_ANSWERS, "overseas_assets": "yes"}
    flags = get_complexity_flags(answers)
    assert flags["has_overseas_assets"] is True


def test_get_complexity_flags_complex_investments():
    answers = {**ALL_13_ANSWERS, "investments_count": "complex"}
    flags = get_complexity_flags(answers)
    assert flags["has_complex_investments"] is True


def test_get_complexity_flags_defaults_on_empty():
    flags = get_complexity_flags({})
    assert flags["service_type"] == "full_administration"
    assert flags["ranking_preference"] == "balanced"
    assert flags["postcode"] == ""
