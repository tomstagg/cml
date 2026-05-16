"""Unit tests for app.services.price_calc.calculate_total_effective_price.

Master Export edition: anchor-point pricing per matter type, VAT on legal fees.
Modifiers / additional_costs / interpolation between anchors are out of scope
for this first pass and will be added when the full pricing engine lands.
"""

import pytest

from app.services.price_calc import calculate_total_effective_price

BASE_ANSWERS = {
    "purchase_price": 275_000,
    "tenure": "freehold",
    "transaction_type": "purchase",
}

ANCHOR_CARD = {
    "freehold": {
        "purchase": {
            150000: 950,
            250000: 1100,
            500000: 1400,
            750000: 1700,
            1000000: 2000,
            1250000: 2300,
            1500000: 2600,
        },
        "sale": {
            150000: 900,
            250000: 1050,
        },
    },
    "leasehold": {
        "purchase": {
            150000: 1100,
            250000: 1250,
            500000: 1500,
        },
        "sale": {},
    },
}


# ── Anchor lookup ────────────────────────────────────────────────────────────


def test_nearest_anchor_picked_for_freehold_purchase():
    """£275k freehold purchase → nearest anchor is £250k (price 1100)."""
    result = calculate_total_effective_price(ANCHOR_CARD, BASE_ANSWERS)
    assert result is not None
    assert result["base_fee"] == 1100.0


def test_high_value_picks_top_anchor():
    """£900k freehold purchase → nearest anchor £1m (price 2000)."""
    answers = {**BASE_ANSWERS, "purchase_price": 900_000}
    result = calculate_total_effective_price(ANCHOR_CARD, answers)
    assert result is not None
    assert result["base_fee"] == 2000.0


def test_below_lowest_anchor_picks_150k():
    answers = {**BASE_ANSWERS, "purchase_price": 100_000}
    result = calculate_total_effective_price(ANCHOR_CARD, answers)
    assert result is not None
    assert result["base_fee"] == 950.0


def test_leasehold_purchase_path():
    answers = {**BASE_ANSWERS, "tenure": "leasehold", "purchase_price": 250_000}
    result = calculate_total_effective_price(ANCHOR_CARD, answers)
    assert result is not None
    assert result["base_fee"] == 1250.0


def test_sale_transaction_path():
    answers = {**BASE_ANSWERS, "transaction_type": "sale", "purchase_price": 150_000}
    result = calculate_total_effective_price(ANCHOR_CARD, answers)
    assert result is not None
    assert result["base_fee"] == 900.0


# ── VAT on legal fees ────────────────────────────────────────────────────────


def test_vat_applied_to_base_fee():
    """£1100 × 20% = £220 VAT, total £1320."""
    result = calculate_total_effective_price(ANCHOR_CARD, BASE_ANSWERS)
    assert result is not None
    assert result["vat"] == pytest.approx(220.0)
    assert result["total"] == pytest.approx(1320.0)


# ── Edge cases ───────────────────────────────────────────────────────────────


def test_empty_card_returns_none():
    assert calculate_total_effective_price({}, BASE_ANSWERS) is None


def test_none_card_returns_none():
    assert calculate_total_effective_price(None, BASE_ANSWERS) is None


def test_no_matter_path_returns_none():
    """Missing transaction_type or tenure → None (caller must supply)."""
    bad_answers = {"purchase_price": 275_000, "tenure": "unknown", "transaction_type": "purchase"}
    assert calculate_total_effective_price(ANCHOR_CARD, bad_answers) is None


def test_no_anchors_for_matter_path_returns_none():
    answers = {**BASE_ANSWERS, "tenure": "leasehold", "transaction_type": "sale"}
    assert calculate_total_effective_price(ANCHOR_CARD, answers) is None


def test_zero_purchase_price_returns_none():
    answers = {**BASE_ANSWERS, "purchase_price": 0}
    assert calculate_total_effective_price(ANCHOR_CARD, answers) is None
