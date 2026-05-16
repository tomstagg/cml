"""Unit tests for app/services/price_calc — Annex One §10 Total Effective Price."""

import pytest

from app.models.price_card import PriceType
from app.services.price_calc import calculate_total_effective_price

# Flags shape mirrors get_intake_flags()'s output.
BASE_FLAGS = {
    "pathway": "purchase",
    "purchase_tenure_type": "freehold",
    "purchase_property_value": 275_000.0,
    "sale_tenure_type": None,
    "sale_property_value": 0.0,
    "mortgage_required": False,
    "new_build": False,
    "new_lease": False,
    "shared_ownership_or_help_to_buy": False,
    "gifted_deposit": False,
    "unregistered_title_purchase": False,
    "unregistered_title_sale": False,
    "additional_mortgage_redemption": False,
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
    "modifiers": [
        {"name": "Purchase - New build (freehold)", "amount": 0},
        {"name": "Purchase - New lease (leasehold)", "amount": 0},
        {"name": "Purchase - Acting for lender", "amount": 100},
        {"name": "Purchase - Shared ownership/Help to Buy", "amount": 250},
        {"name": "Purchase - Gifted deposit", "amount": 75},
        {"name": "Purchase - Unregistered title", "amount": 150},
        {"name": "Sale - Unregistered title", "amount": 150},
        {"name": "Sale - Additional mortgage redemption", "amount": 100},
    ],
    "additional_costs": [
        {"name": "Additional - ID verification", "amount": 8},
        {"name": "Additional - onboarding fee", "amount": 0},
        {"name": "Additional - transfer admin fee", "amount": 40},
        {"name": "SDLT admin fee", "amount": 80},
        {"name": "Leasehold admin fee", "amount": 250},
    ],
    "disbursements": [
        {"name": "Disb - searches (CML standard pack)", "amount": 350},
    ],
}


# ── Anchor lookup ────────────────────────────────────────────────────────────


def test_nearest_anchor_picked_for_freehold_purchase():
    """£275k freehold purchase → nearest anchor £250k → base £1100."""
    result = calculate_total_effective_price(ANCHOR_CARD, BASE_FLAGS, PriceType.verified)
    assert result is not None
    assert result["base_fee"] == 1100.0


def test_zero_purchase_value_returns_none():
    flags = {**BASE_FLAGS, "purchase_property_value": 0}
    assert calculate_total_effective_price(ANCHOR_CARD, flags, PriceType.verified) is None


def test_leasehold_path_picks_leasehold_anchors():
    flags = {**BASE_FLAGS, "purchase_tenure_type": "leasehold", "purchase_property_value": 250_000}
    result = calculate_total_effective_price(ANCHOR_CARD, flags, PriceType.verified)
    assert result is not None
    assert result["base_fee"] == 1250.0


def test_unknown_tenure_returns_none():
    flags = {**BASE_FLAGS, "purchase_tenure_type": "unsure"}
    assert calculate_total_effective_price(ANCHOR_CARD, flags, PriceType.verified) is None


# ── Full Annex One worked example ────────────────────────────────────────────


def test_full_annex_example_for_estimated_card():
    """£300k freehold purchase with mortgage on an Estimated card.

    Per the plan's worked example for Talbots Law (CML-001):
    - Base: nearest anchor £250k → £900 (uses Talbots' actual values)
    - + Acting for lender £100
    - + Additional costs: ID £8 + transfer £40 + SDLT £80 = £128
    - P_estimated = £1,128
    - × 1.075 (c uplift) = £1,212.60
    - + 20% VAT on fees = £1,455.12
    - + searches £350 × 1.20 = £420
    - Total = £1,875.12
    """
    talbots_pricing = {
        "freehold": {
            "purchase": {
                150000: 750,
                250000: 900,
                500000: 1000,
                750000: 1100,
                1000000: 1250,
                1250000: 1350,
                1500000: 1450,
            },
        },
        "modifiers": [
            {"name": "Purchase - Acting for lender", "amount": 100},
        ],
        "additional_costs": [
            {"name": "Additional - ID verification", "amount": 8},
            {"name": "Additional - transfer admin fee", "amount": 40},
            {"name": "SDLT admin fee", "amount": 80},
        ],
        "disbursements": [
            {"name": "Disb - searches (CML standard pack)", "amount": 350},
        ],
    }
    flags = {**BASE_FLAGS, "purchase_property_value": 300_000, "mortgage_required": True}
    result = calculate_total_effective_price(talbots_pricing, flags, PriceType.estimated)
    assert result is not None
    assert result["base_fee"] == 900.0
    assert result["fees_subtotal"] == pytest.approx(1128.0)
    assert result["vat"] == pytest.approx(242.52, abs=0.01)
    assert result["disbursements_total"] == pytest.approx(420.0)
    assert result["total"] == pytest.approx(1875.12, abs=0.05)


def test_verified_card_skips_c_uplift():
    """A Verified price card uses P_estimated unchanged (no 7.5% uplift)."""
    flags = {**BASE_FLAGS, "purchase_property_value": 250_000}
    result = calculate_total_effective_price(ANCHOR_CARD, flags, PriceType.verified)
    # Base £1100 + ID£8 + transfer£40 + SDLT£80 = £1228; ×1.20 = £1473.60; + £420 = £1893.60
    assert result["fees_subtotal"] == pytest.approx(1228.0)
    assert result["total"] == pytest.approx(1893.60, abs=0.05)


def test_estimated_card_applies_c_uplift():
    """Same intake on an Estimated card multiplies P_estimated by 1.075."""
    flags = {**BASE_FLAGS, "purchase_property_value": 250_000}
    result = calculate_total_effective_price(ANCHOR_CARD, flags, PriceType.estimated)
    # P_legal_effective = 1228 × 1.075 = 1320.10; VAT = 264.02; fees+VAT = 1584.12; + 420 = 2004.12
    assert result["total"] == pytest.approx(2004.12, abs=0.10)


# ── Modifier + additional-cost triggers ──────────────────────────────────────


def test_acting_for_lender_only_fires_when_mortgage_required():
    flags_no_mortgage = {**BASE_FLAGS, "mortgage_required": False}
    flags_with_mortgage = {**BASE_FLAGS, "mortgage_required": True}
    no = calculate_total_effective_price(ANCHOR_CARD, flags_no_mortgage, PriceType.verified)
    yes = calculate_total_effective_price(ANCHOR_CARD, flags_with_mortgage, PriceType.verified)
    assert no["fees_subtotal"] + 100 == pytest.approx(yes["fees_subtotal"])


def test_leasehold_admin_fee_only_on_leasehold():
    flags_fh = {**BASE_FLAGS, "purchase_tenure_type": "freehold"}
    flags_lh = {**BASE_FLAGS, "purchase_tenure_type": "leasehold"}
    fh = calculate_total_effective_price(ANCHOR_CARD, flags_fh, PriceType.verified)
    lh = calculate_total_effective_price(ANCHOR_CARD, flags_lh, PriceType.verified)
    # Different anchor + leasehold admin fee
    fh_lines = {a["name"] for a in fh["adjustments"]}
    lh_lines = {a["name"] for a in lh["adjustments"]}
    assert "Leasehold admin fee" not in fh_lines
    assert "Leasehold admin fee" in lh_lines


def test_sdlt_admin_only_on_purchase_side():
    """For sale-only matters, SDLT admin fee must not fire."""
    sale_flags = {
        **BASE_FLAGS,
        "pathway": "sale",
        "purchase_tenure_type": None,
        "purchase_property_value": 0,
        "sale_tenure_type": "freehold",
        "sale_property_value": 150_000,
    }
    result = calculate_total_effective_price(ANCHOR_CARD, sale_flags, PriceType.verified)
    assert result is not None
    names = {a["name"] for a in result["adjustments"]}
    assert "SDLT admin fee" not in names


# ── Combined Sale & Purchase pathway ─────────────────────────────────────────


def test_combined_pathway_sums_two_sides():
    combined_flags = {
        **BASE_FLAGS,
        "pathway": "combined",
        "purchase_tenure_type": "freehold",
        "purchase_property_value": 250_000,
        "sale_tenure_type": "freehold",
        "sale_property_value": 150_000,
        "mortgage_required": True,
        "additional_mortgage_redemption": True,
    }
    result = calculate_total_effective_price(ANCHOR_CARD, combined_flags, PriceType.verified)
    assert result is not None
    assert result["pathway"] == "combined"
    assert len(result["sides"]) == 2
    # Total should be the sum of the two sides' totals
    assert result["total"] == pytest.approx(
        result["sides"][0]["total"] + result["sides"][1]["total"], abs=0.01
    )


# ── Edge cases ───────────────────────────────────────────────────────────────


def test_empty_card_returns_none():
    assert calculate_total_effective_price({}, BASE_FLAGS, PriceType.verified) is None


def test_none_card_returns_none():
    assert calculate_total_effective_price(None, BASE_FLAGS, PriceType.verified) is None


def test_no_anchors_for_matter_returns_none():
    """Leasehold sale has empty anchors in ANCHOR_CARD → None."""
    flags = {
        **BASE_FLAGS,
        "pathway": "sale",
        "sale_tenure_type": "leasehold",
        "sale_property_value": 250_000,
        "purchase_property_value": 0,
    }
    assert calculate_total_effective_price(ANCHOR_CARD, flags, PriceType.verified) is None
