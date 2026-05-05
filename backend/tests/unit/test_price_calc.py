"""Unit tests for app.services.price_calc.calculate_total_effective_price.

Covers Annex One §10 (Quoted-only Total Effective Price) for residential
conveyancing: purchase-price band lookup, conditional adjustments,
fees-VAT, and per-disbursement VAT.
"""

import pytest

from app.services.price_calc import calculate_total_effective_price

# Standard conveyancing answers (after `get_intake_flags` normalisation):
# £275k purchase, freehold, no mortgage / new-build / HtB / shared-ownership.
BASE_ANSWERS = {
    "purchase_price": 275_000,
    "tenure": "freehold",
    "mortgage": False,
    "new_build": False,
    "help_to_buy_isa": False,
    "shared_ownership": False,
}

BAND_CARD = {
    "practice_area": "residential_conveyancing",
    "matter_types": ["purchase", "sale", "purchase_and_sale", "remortgage"],
    "pricing_model": "band",
    "bands": [
        {"purchase_price_min": 0, "purchase_price_max": 250_000, "fee": 950},
        {"purchase_price_min": 250_000, "purchase_price_max": 500_000, "fee": 1_250},
        {"purchase_price_min": 500_000, "purchase_price_max": None, "fee": 1_750},
    ],
    "adjustments": [],
    "included_disbursements": [],
    "vat_applies_to_fees": True,
}


# ── Band lookup ──────────────────────────────────────────────────────────────


def test_band_matched_for_low_value_purchase():
    """£200k → first band, fee £950."""
    answers = {**BASE_ANSWERS, "purchase_price": 200_000}
    result = calculate_total_effective_price(BAND_CARD, answers)
    assert result is not None
    assert result["base_fee"] == 950.0


def test_band_matched_for_mid_value_purchase():
    """£275k → middle band, fee £1,250."""
    result = calculate_total_effective_price(BAND_CARD, BASE_ANSWERS)
    assert result is not None
    assert result["base_fee"] == 1_250.0


def test_band_matched_for_high_value_open_band():
    """£800k → open-ended band, fee £1,750."""
    answers = {**BASE_ANSWERS, "purchase_price": 800_000}
    result = calculate_total_effective_price(BAND_CARD, answers)
    assert result is not None
    assert result["base_fee"] == 1_750.0


def test_no_matching_band_returns_none():
    card = {
        **BAND_CARD,
        "bands": [{"purchase_price_min": 500_000, "purchase_price_max": 1_000_000, "fee": 2_000}],
    }
    answers = {**BASE_ANSWERS, "purchase_price": 100_000}
    assert calculate_total_effective_price(card, answers) is None


# ── Conditional adjustments ──────────────────────────────────────────────────


def test_leasehold_adjustment_applied_when_tenure_leasehold():
    card = {
        **BAND_CARD,
        "adjustments": [
            {"name": "Leasehold supplement", "amount": 250, "condition": "tenure==leasehold"},
        ],
    }
    answers = {**BASE_ANSWERS, "tenure": "leasehold"}
    result = calculate_total_effective_price(card, answers)
    assert result is not None
    assert result["adjustments"] == [{"name": "Leasehold supplement", "amount": 250.0}]
    assert result["fees_subtotal"] == pytest.approx(1_500.0)


def test_leasehold_adjustment_skipped_when_tenure_freehold():
    card = {
        **BAND_CARD,
        "adjustments": [
            {"name": "Leasehold supplement", "amount": 250, "condition": "tenure==leasehold"},
        ],
    }
    result = calculate_total_effective_price(card, BASE_ANSWERS)
    assert result is not None
    assert result["adjustments"] == []
    assert result["fees_subtotal"] == pytest.approx(1_250.0)


def test_multiple_boolean_adjustments_combine():
    """Mortgage + new-build + HtB ISA + shared-ownership → all four supplements applied."""
    card = {
        **BAND_CARD,
        "adjustments": [
            {"name": "Mortgage handling", "amount": 150, "condition": "mortgage==true"},
            {"name": "New build supplement", "amount": 200, "condition": "new_build==true"},
            {"name": "Help to Buy ISA admin", "amount": 75, "condition": "help_to_buy_isa==true"},
            {
                "name": "Shared ownership supplement",
                "amount": 250,
                "condition": "shared_ownership==true",
            },
        ],
    }
    answers = {
        **BASE_ANSWERS,
        "mortgage": True,
        "new_build": True,
        "help_to_buy_isa": True,
        "shared_ownership": True,
    }
    result = calculate_total_effective_price(card, answers)
    assert result is not None
    assert {a["name"] for a in result["adjustments"]} == {
        "Mortgage handling",
        "New build supplement",
        "Help to Buy ISA admin",
        "Shared ownership supplement",
    }
    # 1250 + 150 + 200 + 75 + 250 = 1925
    assert result["fees_subtotal"] == pytest.approx(1_925.0)


def test_adjustment_with_no_condition_always_applies():
    card = {
        **BAND_CARD,
        "adjustments": [{"name": "Compliance fee", "amount": 50}],
    }
    result = calculate_total_effective_price(card, BASE_ANSWERS)
    assert result is not None
    assert result["adjustments"] == [{"name": "Compliance fee", "amount": 50.0}]


def test_unknown_condition_format_skipped():
    """A malformed condition is treated as not applying — defensive default."""
    card = {
        **BAND_CARD,
        "adjustments": [{"name": "Bad adj", "amount": 999, "condition": "??"}],
    }
    result = calculate_total_effective_price(card, BASE_ANSWERS)
    assert result is not None
    assert result["adjustments"] == []


# ── VAT on legal fees ────────────────────────────────────────────────────────


def test_vat_applied_to_fees_subtotal():
    """£1,250 × 20% = £250 VAT."""
    result = calculate_total_effective_price(BAND_CARD, BASE_ANSWERS)
    assert result is not None
    assert result["vat"] == pytest.approx(250.0)


def test_no_vat_when_flag_false():
    card = {**BAND_CARD, "vat_applies_to_fees": False}
    result = calculate_total_effective_price(card, BASE_ANSWERS)
    assert result is not None
    assert result["vat"] == 0.0


# ── Disbursements (per-row VAT) ──────────────────────────────────────────────


def test_disbursement_with_vat_applied_per_row():
    card = {
        **BAND_CARD,
        "included_disbursements": [
            {"name": "Local authority search", "amount": 180, "vat_applies": True},
            {"name": "Bankruptcy search", "amount": 6, "vat_applies": False},
        ],
    }
    result = calculate_total_effective_price(card, BASE_ANSWERS)
    assert result is not None
    # 180 × 1.20 = 216; 6 net; total = 222
    assert result["disbursements"][0]["amount"] == pytest.approx(216.0)
    assert result["disbursements"][1]["amount"] == pytest.approx(6.0)
    assert result["disbursements_total"] == pytest.approx(222.0)


# ── End-to-end total ─────────────────────────────────────────────────────────


def test_total_effective_price_full_example():
    """Leasehold + new-build + mortgage at £275k with two disbursements.

    Fees: 1250 base + 250 leasehold + 200 new-build + 150 mortgage = 1850.
    VAT on fees: 1850 × 0.20 = 370.
    Disbursements: (180 × 1.20) + 6 = 216 + 6 = 222.
    Total: 1850 + 370 + 222 = 2442.
    """
    card = {
        **BAND_CARD,
        "adjustments": [
            {"name": "Leasehold supplement", "amount": 250, "condition": "tenure==leasehold"},
            {"name": "New build supplement", "amount": 200, "condition": "new_build==true"},
            {"name": "Mortgage handling", "amount": 150, "condition": "mortgage==true"},
        ],
        "included_disbursements": [
            {"name": "Local authority search", "amount": 180, "vat_applies": True},
            {"name": "Bankruptcy search", "amount": 6, "vat_applies": False},
        ],
    }
    answers = {**BASE_ANSWERS, "tenure": "leasehold", "new_build": True, "mortgage": True}
    result = calculate_total_effective_price(card, answers)
    assert result is not None
    assert result["fees_subtotal"] == pytest.approx(1_850.0)
    assert result["vat"] == pytest.approx(370.0)
    assert result["disbursements_total"] == pytest.approx(222.0)
    assert result["total"] == pytest.approx(2_442.0)


# ── Edge cases ───────────────────────────────────────────────────────────────


def test_empty_card_returns_none():
    assert calculate_total_effective_price({}, BASE_ANSWERS) is None


def test_none_card_returns_none():
    assert calculate_total_effective_price(None, BASE_ANSWERS) is None
