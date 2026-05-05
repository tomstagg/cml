"""Unit tests for app/services/chat.py — no DB required."""

from app.services.chat import (
    CONVEYANCING_QUESTIONS,
    get_first_question,
    get_intake_flags,
    get_next_question,
    is_flow_complete,
    validate_answer,
)
from tests.conftest import CONVEYANCING_ANSWERS


def test_get_first_question_returns_step_1_purchase_price():
    q = get_first_question()
    assert q["step"] == 1
    assert q["id"] == "purchase_price"
    assert q["type"] == "currency"


def test_get_next_question_advances_sequentially():
    q = get_first_question()
    for i in range(1, len(CONVEYANCING_QUESTIONS)):
        nxt = get_next_question(q["id"], {})
        assert nxt is not None
        assert nxt["step"] == i + 1
        q = nxt


def test_get_next_question_after_last_returns_none():
    last = CONVEYANCING_QUESTIONS[-1]
    assert get_next_question(last["id"], CONVEYANCING_ANSWERS) is None


def test_get_next_question_unknown_id_returns_none():
    assert get_next_question("nonexistent_question", {}) is None


def test_is_flow_complete_empty_answers():
    assert is_flow_complete({}) is False


def test_is_flow_complete_partial_answers():
    partial = {"purchase_price": "275000", "tenure": "leasehold"}
    assert is_flow_complete(partial) is False


def test_is_flow_complete_all_answers():
    assert is_flow_complete(CONVEYANCING_ANSWERS) is True


# ── Validation ────────────────────────────────────────────────────────────────
def test_validate_currency_accepts_plain_number():
    ok, _ = validate_answer("purchase_price", "275000")
    assert ok


def test_validate_currency_accepts_formatted_number():
    ok, _ = validate_answer("purchase_price", "£275,000")
    assert ok


def test_validate_currency_rejects_non_numeric():
    ok, error = validate_answer("purchase_price", "not a number")
    assert ok is False
    assert error is not None


def test_validate_currency_rejects_zero_or_negative():
    ok, _ = validate_answer("purchase_price", "0")
    assert ok is False


def test_validate_postcode_accepts_uk_postcode():
    ok, _ = validate_answer("property_postcode", "B1 1AA")
    assert ok


def test_validate_postcode_accepts_lowercase_no_space():
    ok, _ = validate_answer("property_postcode", "b11aa")
    assert ok


def test_validate_postcode_rejects_garbage():
    ok, _ = validate_answer("property_postcode", "ZZ")
    assert ok is False


def test_validate_email_accepts_valid_address():
    ok, _ = validate_answer("email", "jane@example.com")
    assert ok


def test_validate_email_rejects_invalid_address():
    ok, _ = validate_answer("email", "not-an-email")
    assert ok is False


def test_validate_phone_accepts_uk_mobile():
    ok, _ = validate_answer("phone", "07700900123")
    assert ok


def test_validate_phone_rejects_too_short():
    ok, _ = validate_answer("phone", "12345")
    assert ok is False


def test_validate_single_choice_rejects_invalid_option():
    ok, _ = validate_answer("tenure", "haunted_house")
    assert ok is False


def test_validate_single_choice_accepts_valid_option():
    ok, _ = validate_answer("tenure", "leasehold")
    assert ok


def test_validate_unknown_question_rejected():
    ok, _ = validate_answer("does_not_exist", "anything")
    assert ok is False


# ── Intake flags ──────────────────────────────────────────────────────────────
def test_get_intake_flags_coerces_purchase_price():
    flags = get_intake_flags({"purchase_price": "£275,000"})
    assert flags["purchase_price"] == 275_000.0


def test_get_intake_flags_coerces_yes_no_to_bool():
    flags = get_intake_flags(
        {
            "mortgage": "yes",
            "new_build": "no",
            "help_to_buy_isa": "yes",
            "shared_ownership": "no",
        }
    )
    assert flags["mortgage"] is True
    assert flags["new_build"] is False
    assert flags["help_to_buy_isa"] is True
    assert flags["shared_ownership"] is False


def test_get_intake_flags_defaults_on_empty():
    flags = get_intake_flags({})
    assert flags["purchase_price"] == 0.0
    assert flags["tenure"] == "freehold"
    assert flags["scorecard_preference"] == "balanced"
    assert flags["include_distance"] is False


def test_get_intake_flags_extracts_all_conveyancing_fields():
    flags = get_intake_flags(CONVEYANCING_ANSWERS)
    assert flags["purchase_price"] == 275_000.0
    assert flags["tenure"] == "leasehold"
    assert flags["property_postcode"] == "B1 1AA"
    assert flags["mortgage"] is True
    assert flags["help_to_buy_isa"] is True
    assert flags["scorecard_preference"] == "balanced"
    assert flags["email"] == "jane@example.com"
