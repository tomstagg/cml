"""Unit tests for app/services/price_calc.py — no DB required."""

import pytest

from app.services.price_calc import calculate_quote

BASE_COMPLEXITY = {
    "service_type": "full_administration",
    "estate_value": 212500,
    "has_iht400": False,
    "has_overseas_assets": False,
    "has_complex_investments": False,
}

BAND_PRICING = {
    "practice_area": "probate",
    "matter_types": ["grant_only", "full_administration"],
    "pricing_model": "band",
    "bands": [
        {"estate_value_min": 0, "estate_value_max": 325000, "fee": 1500},
        {"estate_value_min": 325000, "estate_value_max": 650000, "fee": 2500},
        {"estate_value_min": 650000, "estate_value_max": None, "fee": 3500},
    ],
    "adjustments": [],
    "disbursements": [],
    "vat_applies_to_fees": True,
}

FIXED_PRICING = {
    "practice_area": "probate",
    "matter_types": ["full_administration"],
    "pricing_model": "fixed",
    "bands": [{"estate_value_min": 0, "estate_value_max": None, "fee": 2000}],
    "adjustments": [],
    "disbursements": [],
    "vat_applies_to_fees": True,
}

PERCENTAGE_PRICING = {
    "practice_area": "probate",
    "matter_types": ["full_administration"],
    "pricing_model": "percentage",
    "percentage_rate": 1.5,
    "adjustments": [],
    "disbursements": [],
    "vat_applies_to_fees": False,
}


# ── Band model ───────────────────────────────────────────────────────────────


def test_band_model_matches_correct_band():
    """Estate value 212,500 falls in the 0–325,000 band → fee = £1,500."""
    result = calculate_quote(BAND_PRICING, BASE_COMPLEXITY)
    assert result is not None
    assert result["base_fee"] == 1500.0


def test_band_model_upper_band():
    """Estate value 500,000 falls in 325k–650k band → fee = £2,500."""
    complexity = {**BASE_COMPLEXITY, "estate_value": 500000}
    result = calculate_quote(BAND_PRICING, complexity)
    assert result is not None
    assert result["base_fee"] == 2500.0


def test_band_model_open_upper_band():
    """Estate value 800,000 falls in the open-ended band → fee = £3,500."""
    complexity = {**BASE_COMPLEXITY, "estate_value": 800000}
    result = calculate_quote(BAND_PRICING, complexity)
    assert result is not None
    assert result["base_fee"] == 3500.0


def test_band_model_no_matching_band_returns_none():
    """A pricing dict with no bands matching the estate value → None."""
    pricing = {
        **BAND_PRICING,
        "bands": [{"estate_value_min": 500000, "estate_value_max": 650000, "fee": 2500}],
    }
    complexity = {**BASE_COMPLEXITY, "estate_value": 100000}
    result = calculate_quote(pricing, complexity)
    assert result is None


# ── Fixed model ──────────────────────────────────────────────────────────────


def test_fixed_model_returns_single_fee():
    result = calculate_quote(FIXED_PRICING, BASE_COMPLEXITY)
    assert result is not None
    assert result["base_fee"] == 2000.0
    assert result["pricing_model"] == "fixed"


# ── Percentage model ─────────────────────────────────────────────────────────


def test_percentage_model_1_5_pct_of_300k():
    """1.5% of £300,000 = £4,500."""
    complexity = {**BASE_COMPLEXITY, "estate_value": 300000}
    result = calculate_quote(PERCENTAGE_PRICING, complexity)
    assert result is not None
    assert result["base_fee"] == pytest.approx(4500.0)
    assert result["pricing_model"] == "percentage"


# ── Adjustments ──────────────────────────────────────────────────────────────


def test_iht400_adjustment_applied_when_flag_true():
    pricing = {
        **BAND_PRICING,
        "adjustments": [{"name": "IHT400", "amount": 500, "condition": "iht400"}],
    }
    complexity = {**BASE_COMPLEXITY, "has_iht400": True}
    result = calculate_quote(pricing, complexity)
    assert result is not None
    adj_names = [a["name"] for a in result["adjustments"]]
    assert "IHT400" in adj_names
    assert result["fees_subtotal"] == pytest.approx(2000.0)  # 1500 + 500


def test_iht400_adjustment_skipped_when_flag_false():
    pricing = {
        **BAND_PRICING,
        "adjustments": [{"name": "IHT400", "amount": 500, "condition": "iht400"}],
    }
    result = calculate_quote(pricing, BASE_COMPLEXITY)
    assert result is not None
    assert result["adjustments"] == []
    assert result["fees_subtotal"] == pytest.approx(1500.0)


def test_overseas_assets_adjustment_applied():
    pricing = {
        **BAND_PRICING,
        "adjustments": [{"name": "Overseas assets", "amount": 750, "condition": "overseas_assets"}],
    }
    complexity = {**BASE_COMPLEXITY, "has_overseas_assets": True}
    result = calculate_quote(pricing, complexity)
    assert result is not None
    assert len(result["adjustments"]) == 1
    assert result["adjustments"][0]["amount"] == 750.0


# ── VAT ──────────────────────────────────────────────────────────────────────


def test_vat_applied_to_fees_when_flag_true():
    """1500 * 20% = £300 VAT."""
    result = calculate_quote(BAND_PRICING, BASE_COMPLEXITY)
    assert result is not None
    assert result["vat"] == pytest.approx(300.0)


def test_no_vat_when_flag_false():
    result = calculate_quote(PERCENTAGE_PRICING, {**BASE_COMPLEXITY, "estate_value": 300000})
    assert result is not None
    assert result["vat"] == 0.0


# ── Disbursements ─────────────────────────────────────────────────────────────


def test_disbursements_summed_separately():
    pricing = {
        **BAND_PRICING,
        "disbursements": [
            {"name": "Probate Registry fee", "amount": 273, "estimated": False},
            {"name": "Death certificates (est.)", "amount": 50, "estimated": True},
        ],
    }
    result = calculate_quote(pricing, BASE_COMPLEXITY)
    assert result is not None
    assert result["disbursements_total"] == pytest.approx(323.0)
    assert len(result["disbursements"]) == 2


# ── Total ─────────────────────────────────────────────────────────────────────


def test_total_equals_fees_plus_vat_plus_disbursements():
    pricing = {
        **BAND_PRICING,
        "disbursements": [{"name": "Court fee", "amount": 273, "estimated": False}],
    }
    result = calculate_quote(pricing, BASE_COMPLEXITY)
    assert result is not None
    # fee=1500, vat=300, disb=273 → total=2073
    assert result["total"] == pytest.approx(2073.0)


# ── Service type mismatch ─────────────────────────────────────────────────────


def test_service_type_mismatch_returns_none():
    """A grant_only-only card should not match a full_administration session."""
    pricing = {**BAND_PRICING, "matter_types": ["grant_only"]}
    complexity = {**BASE_COMPLEXITY, "service_type": "full_administration"}
    result = calculate_quote(pricing, complexity)
    assert result is None


# ── Edge cases ────────────────────────────────────────────────────────────────


def test_empty_pricing_returns_none():
    assert calculate_quote({}, BASE_COMPLEXITY) is None


def test_none_pricing_returns_none():
    assert calculate_quote(None, BASE_COMPLEXITY) is None
