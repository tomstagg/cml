"""Unit tests for app/services/chat.py — pathway-aware intake flow."""

from app.services.chat import (
    dynamic_options,
    first_question,
    get_intake_flags,
    get_pathway,
    is_flow_complete,
    next_question,
    validate_answer,
    visible_questions,
)
from tests.conftest import CONVEYANCING_ANSWERS


# ── Pathway routing ──────────────────────────────────────────────────────────


def test_first_question_is_transaction_type():
    q = first_question()
    assert q["id"] == "transaction_type"
    assert q["step"] == 1


def test_pathway_resolves_buying_to_purchase():
    assert get_pathway({"transaction_type": "buying"}) == "purchase"


def test_pathway_resolves_selling_to_sale():
    assert get_pathway({"transaction_type": "selling"}) == "sale"


def test_pathway_resolves_combined():
    assert get_pathway({"transaction_type": "selling_and_buying"}) == "combined"


def test_visible_questions_for_purchase_pathway():
    qs = [q["id"] for q in visible_questions("purchase")]
    assert qs == [
        "transaction_type",
        "purchase_tenure_type",
        "purchase_property_value",
        "transaction_details",
        "distance_preference",
    ]


def test_visible_questions_for_sale_pathway():
    qs = [q["id"] for q in visible_questions("sale")]
    assert qs == [
        "transaction_type",
        "sale_tenure_type",
        "sale_property_value",
        "transaction_details",
        "distance_preference",
    ]


def test_visible_questions_for_combined_pathway():
    qs = [q["id"] for q in visible_questions("combined")]
    assert qs == [
        "transaction_type",
        "combined_property_details",
        "transaction_details",
        "distance_preference",
    ]


# ── Next-question advancement ────────────────────────────────────────────────


def test_next_question_starts_at_q1():
    assert next_question({})["id"] == "transaction_type"


def test_next_question_purchase_pathway_walks_5_steps():
    answers = {"transaction_type": "buying"}
    assert next_question(answers)["id"] == "purchase_tenure_type"
    answers["purchase_tenure_type"] = "freehold"
    assert next_question(answers)["id"] == "purchase_property_value"
    answers["purchase_property_value"] = 275_000
    assert next_question(answers)["id"] == "transaction_details"
    answers["transaction_details"] = []
    assert next_question(answers)["id"] == "distance_preference"
    answers["distance_preference"] = ""
    assert next_question(answers) is None


def test_next_question_combined_pathway_walks_4_steps():
    answers = {"transaction_type": "selling_and_buying"}
    assert next_question(answers)["id"] == "combined_property_details"
    answers["combined_property_details"] = {
        "purchase_tenure_type": "freehold",
        "purchase_property_value": 300_000,
        "sale_tenure_type": "leasehold",
        "sale_property_value": 200_000,
    }
    assert next_question(answers)["id"] == "transaction_details"
    answers["transaction_details"] = []
    assert next_question(answers)["id"] == "distance_preference"
    answers["distance_preference"] = ""
    assert next_question(answers) is None


def test_unsure_tenure_does_not_progress():
    """Selecting 'I'm not sure' keeps the user on the tenure question."""
    answers = {"transaction_type": "buying", "purchase_tenure_type": "unsure"}
    assert next_question(answers)["id"] == "purchase_tenure_type"


# ── Flow completion ──────────────────────────────────────────────────────────


def test_is_flow_complete_empty_answers():
    assert is_flow_complete({}) is False


def test_is_flow_complete_after_canonical_answers():
    assert is_flow_complete(CONVEYANCING_ANSWERS) is True


# ── Validation ───────────────────────────────────────────────────────────────


def test_validate_currency_accepts_positive_number():
    ok, _ = validate_answer("purchase_property_value", 275_000, {"transaction_type": "buying"})
    assert ok


def test_validate_currency_rejects_zero():
    ok, _ = validate_answer("purchase_property_value", 0, {"transaction_type": "buying"})
    assert ok is False


def test_validate_tenure_accepts_unsure():
    ok, _ = validate_answer("purchase_tenure_type", "unsure", {"transaction_type": "buying"})
    assert ok


def test_validate_tenure_rejects_bogus_option():
    ok, _ = validate_answer("purchase_tenure_type", "haunted_house", {"transaction_type": "buying"})
    assert ok is False


def test_validate_optional_postcode_accepts_blank():
    ok, _ = validate_answer("distance_preference", "", {"transaction_type": "buying"})
    assert ok


def test_validate_optional_postcode_accepts_valid_uk_postcode():
    ok, _ = validate_answer("distance_preference", "B1 1AA", {"transaction_type": "buying"})
    assert ok


def test_validate_optional_postcode_rejects_garbage():
    ok, _ = validate_answer("distance_preference", "ZZ", {"transaction_type": "buying"})
    assert ok is False


def test_validate_checkbox_group_accepts_known_flags():
    answers = {"transaction_type": "buying", "purchase_tenure_type": "leasehold"}
    ok, _ = validate_answer(
        "transaction_details",
        ["mortgage_required", "shared_ownership_or_help_to_buy"],
        answers,
    )
    assert ok


def test_validate_checkbox_group_rejects_unknown_flag():
    answers = {"transaction_type": "buying", "purchase_tenure_type": "freehold"}
    ok, _ = validate_answer("transaction_details", ["not_a_real_flag"], answers)
    assert ok is False


def test_validate_dual_block_accepts_well_formed_payload():
    ok, _ = validate_answer(
        "combined_property_details",
        {
            "purchase_tenure_type": "freehold",
            "purchase_property_value": 300_000,
            "sale_tenure_type": "leasehold",
            "sale_property_value": 200_000,
        },
        {"transaction_type": "selling_and_buying"},
    )
    assert ok


# ── Dynamic modifier options ─────────────────────────────────────────────────


def test_dynamic_modifiers_visible_for_buying_freehold():
    answers = {"transaction_type": "buying", "purchase_tenure_type": "freehold"}
    ids = [opt["value"] for opt in dynamic_options("transaction_details", answers)]
    assert "mortgage_required" in ids
    assert "new_build" in ids
    assert "new_lease" not in ids  # leasehold-only
    assert "additional_mortgage_redemption" not in ids  # sale-only


def test_dynamic_modifiers_visible_for_buying_leasehold():
    answers = {"transaction_type": "buying", "purchase_tenure_type": "leasehold"}
    ids = [opt["value"] for opt in dynamic_options("transaction_details", answers)]
    assert "new_lease" in ids
    assert "new_build" not in ids


def test_dynamic_modifiers_for_selling():
    answers = {"transaction_type": "selling", "sale_tenure_type": "freehold"}
    ids = [opt["value"] for opt in dynamic_options("transaction_details", answers)]
    assert "additional_mortgage_redemption" in ids
    assert "unregistered_title_sale" in ids
    assert "mortgage_required" not in ids  # buying-only


def test_dynamic_modifiers_for_combined_show_both_sides():
    answers = {
        "transaction_type": "selling_and_buying",
        "combined_property_details": {
            "purchase_tenure_type": "freehold",
            "sale_tenure_type": "leasehold",
            "purchase_property_value": 300_000,
            "sale_property_value": 200_000,
        },
    }
    ids = [opt["value"] for opt in dynamic_options("transaction_details", answers)]
    assert "mortgage_required" in ids  # buying side
    assert "additional_mortgage_redemption" in ids  # selling side


# ── Intake flags ─────────────────────────────────────────────────────────────


def test_intake_flags_for_buying_extracts_values():
    flags = get_intake_flags(CONVEYANCING_ANSWERS)
    assert flags["pathway"] == "purchase"
    assert flags["purchase_tenure_type"] == "leasehold"
    assert flags["purchase_property_value"] == 275_000.0
    assert flags["mortgage_required"] is True
    assert flags["shared_ownership_or_help_to_buy"] is True
    assert flags["new_build"] is False
    assert flags["user_postcode"] == "B1 1AA"
    assert flags["distance_included"] is True


def test_intake_flags_for_combined_flattens_dual_block():
    answers = {
        "transaction_type": "selling_and_buying",
        "combined_property_details": {
            "purchase_tenure_type": "freehold",
            "purchase_property_value": 350_000,
            "sale_tenure_type": "leasehold",
            "sale_property_value": 220_000,
        },
        "transaction_details": ["mortgage_required", "additional_mortgage_redemption"],
        "distance_preference": "",
    }
    flags = get_intake_flags(answers)
    assert flags["pathway"] == "combined"
    assert flags["purchase_tenure_type"] == "freehold"
    assert flags["purchase_property_value"] == 350_000.0
    assert flags["sale_tenure_type"] == "leasehold"
    assert flags["sale_property_value"] == 220_000.0
    assert flags["mortgage_required"] is True
    assert flags["additional_mortgage_redemption"] is True
    assert flags["distance_included"] is False


def test_intake_flags_empty_defaults_to_purchase():
    flags = get_intake_flags({})
    assert flags["pathway"] == "purchase"
    assert flags["purchase_property_value"] == 0.0
    assert flags["distance_included"] is False
