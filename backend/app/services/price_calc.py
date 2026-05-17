"""Annex One §10 Total Effective Price calculator.

Computes ``P_effective`` for a firm + user intake:

    P_estimated      = anchor_fee + Σ applicable_modifiers + Σ applicable_additional_costs
    P_legal_effective = P_estimated × (1 + c)   if Estimated price card  (c = 0.075)
                      = P_estimated             if Verified price card
    P_effective      = P_legal_effective + (P_legal_effective × 0.20)
                       + P_included_disbursements   (searches incl. VAT)

For combined Sale & Purchase, the pricer is run twice (once per side) and
the two quotes are summed into a single result.

The trigger conditions for modifiers / additional costs aren't documented in
the Master Export workbook, so they're encoded here based on the published
field names (`Purchase - Acting for lender` etc.) and reasonable inference;
see plan file for the trigger table.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from app.models.price_card import PriceType

# Annex One constants
CONFIDENCE_UPLIFT_C = Decimal("0.075")  # §10 — Estimated-price uplift
VAT_RATE = Decimal("0.20")
PENNY = Decimal("0.01")

# CML-defined anchor points on the Price tab.
ANCHORS: tuple[int, ...] = (150_000, 250_000, 500_000, 750_000, 1_000_000, 1_250_000, 1_500_000)

# Canonical names of the rows on the Master Export Price tab. The ingestion
# script keeps these exact strings on each pricing JSONB entry; we resolve via
# whitespace-normalised lookup to tolerate small variations.
MODIFIER_NEW_BUILD_FREEHOLD = "Purchase - New build (freehold)"
MODIFIER_NEW_LEASE_LEASEHOLD = "Purchase - New lease (leasehold)"
MODIFIER_ACTING_FOR_LENDER = "Purchase - Acting for lender"
MODIFIER_SHARED_OWNERSHIP_OR_HTB = "Purchase - Shared ownership/Help to Buy"
MODIFIER_GIFTED_DEPOSIT = "Purchase - Gifted deposit"
MODIFIER_UNREGISTERED_PURCHASE = "Purchase - Unregistered title"
MODIFIER_UNREGISTERED_SALE = "Sale - Unregistered title"
MODIFIER_ADDITIONAL_MORTGAGE_REDEMPTION = "Sale - Additional mortgage redemption"

ADDITIONAL_ID_VERIFICATION = "Additional - ID verification"
ADDITIONAL_ONBOARDING = "Additional - onboarding fee"
ADDITIONAL_TRANSFER_ADMIN = "Additional - transfer admin fee"
ADDITIONAL_SDLT_ADMIN = "SDLT admin fee"
ADDITIONAL_LEASEHOLD_ADMIN = "Leasehold admin fee"

DISBURSEMENT_SEARCHES = "Disb - searches (CML standard pack)"


# ── Helpers ──────────────────────────────────────────────────────────────────


def _q(value: Decimal) -> Decimal:
    return value.quantize(PENNY, rounding=ROUND_HALF_UP)


def _as_decimal(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0")


def _norm(name: str) -> str:
    return " ".join(name.lower().split())


def _lookup_named_amount(items: list[dict] | None, name: str) -> Decimal:
    """Find a named item in a list of {name, amount} entries, whitespace-tolerant."""
    if not items:
        return Decimal("0")
    target = _norm(name)
    for item in items:
        if _norm(str(item.get("name", ""))) == target:
            return _as_decimal(item.get("amount"))
    return Decimal("0")


def _nearest_anchor(purchase_price: int) -> int:
    """Pick the closest of the seven CML anchor points to the user's price."""
    return min(ANCHORS, key=lambda a: abs(a - purchase_price))


def _anchor_fee(pricing: dict, tenure: str, side: str, value: int) -> Decimal | None:
    """Look up the firm's fee at the nearest anchor for the given tenure/side."""
    anchors = pricing.get(tenure, {}).get(side, {}) or {}
    if not anchors:
        return None
    chosen = _nearest_anchor(value)
    raw = anchors.get(chosen, anchors.get(str(chosen)))
    if raw is None:
        return None
    return _as_decimal(raw)


# ── Applicable modifier / additional-cost resolution ─────────────────────────


def _applicable_modifiers(flags: dict, side: str) -> list[tuple[str, dict]]:
    """Return (name, {flag_key, requires_tenure?}) pairs for the modifier rows
    that apply to the given side of the transaction.
    """
    out: list[tuple[str, dict]] = []
    if side == "purchase":
        tenure = flags.get("purchase_tenure_type")
        if flags.get("new_build") and tenure == "freehold":
            out.append((MODIFIER_NEW_BUILD_FREEHOLD, {}))
        if flags.get("new_lease") and tenure == "leasehold":
            out.append((MODIFIER_NEW_LEASE_LEASEHOLD, {}))
        if flags.get("mortgage_required"):
            out.append((MODIFIER_ACTING_FOR_LENDER, {}))
        if flags.get("shared_ownership_or_help_to_buy"):
            out.append((MODIFIER_SHARED_OWNERSHIP_OR_HTB, {}))
        if flags.get("gifted_deposit"):
            out.append((MODIFIER_GIFTED_DEPOSIT, {}))
        if flags.get("unregistered_title_purchase"):
            out.append((MODIFIER_UNREGISTERED_PURCHASE, {}))
    else:  # sale
        if flags.get("unregistered_title_sale"):
            out.append((MODIFIER_UNREGISTERED_SALE, {}))
        if flags.get("additional_mortgage_redemption"):
            out.append((MODIFIER_ADDITIONAL_MORTGAGE_REDEMPTION, {}))
    return out


def _applicable_additional_costs(side: str, tenure: str) -> list[str]:
    """Return the additional-cost row names that always-or-conditionally apply
    to this side of the transaction.
    """
    out = [ADDITIONAL_ID_VERIFICATION, ADDITIONAL_ONBOARDING, ADDITIONAL_TRANSFER_ADMIN]
    if side == "purchase":
        out.append(ADDITIONAL_SDLT_ADMIN)
    if tenure == "leasehold":
        out.append(ADDITIONAL_LEASEHOLD_ADMIN)
    return out


# ── Single-side calculator ───────────────────────────────────────────────────


def _calculate_side(
    pricing: dict,
    flags: dict,
    side: str,
    price_type: PriceType,
) -> dict | None:
    """Annex One §10 calculation for one side (purchase or sale)."""
    tenure = flags.get(f"{side}_tenure_type")
    raw_value = flags.get(f"{side}_property_value", 0)
    try:
        value = int(float(raw_value))
    except (TypeError, ValueError):
        return None

    if tenure not in ("freehold", "leasehold") or value <= 0:
        return None

    anchor_fee = _anchor_fee(pricing, tenure, side, value)
    if anchor_fee is None:
        return None

    # Adjustments (modifiers).
    adjustments: list[dict] = []
    adjustment_total = Decimal("0")
    for name, _ in _applicable_modifiers(flags, side):
        amount = _lookup_named_amount(pricing.get("modifiers"), name)
        if amount == 0:
            continue  # Don't display zero-value lines.
        adjustments.append({"name": name, "amount": float(amount)})
        adjustment_total += amount

    # Additional costs.
    additional: list[dict] = []
    additional_total = Decimal("0")
    for name in _applicable_additional_costs(side, tenure):
        amount = _lookup_named_amount(pricing.get("additional_costs"), name)
        if amount == 0:
            continue
        additional.append({"name": name, "amount": float(amount)})
        additional_total += amount

    p_estimated = anchor_fee + adjustment_total + additional_total

    if price_type == PriceType.estimated:
        p_legal_effective = p_estimated * (Decimal("1") + CONFIDENCE_UPLIFT_C)
    else:
        p_legal_effective = p_estimated

    vat = p_legal_effective * VAT_RATE
    fees_with_vat = p_legal_effective + vat

    # Disbursements — searches £350 with VAT (per UK conveyancing convention).
    searches_net = _lookup_named_amount(pricing.get("disbursements"), DISBURSEMENT_SEARCHES)
    searches_gross = searches_net * (Decimal("1") + VAT_RATE)
    disbursements_lines = [{"name": DISBURSEMENT_SEARCHES, "amount": float(_q(searches_gross))}]

    total = fees_with_vat + searches_gross

    return {
        "side": side,
        "base_fee": float(_q(anchor_fee)),
        "adjustments": adjustments,
        "additional_costs": additional,
        "fees_subtotal": float(_q(p_estimated)),
        "estimated_uplift": float(_q(p_legal_effective - p_estimated)),
        "vat": float(_q(vat)),
        "disbursements": disbursements_lines,
        "disbursements_total": float(_q(searches_gross)),
        "total": float(_q(total)),
        "currency": "GBP",
    }


# ── Public entry point ───────────────────────────────────────────────────────


def calculate_total_effective_price(
    pricing: dict,
    flags: dict,
    price_type: PriceType = PriceType.estimated,
) -> dict | None:
    """Compute the Total Effective Price for the user's pathway.

    For Buying or Selling only, returns one-sided quote.
    For Sale & Purchase combined, returns the sum-of-two-sides quote with both
    breakdowns kept in `sides`.
    """
    if not pricing:
        return None

    pathway = flags.get("pathway") or "purchase"

    if pathway == "combined":
        purchase = _calculate_side(pricing, flags, "purchase", price_type)
        sale = _calculate_side(pricing, flags, "sale", price_type)
        if not purchase or not sale:
            return None
        combined_total = purchase["total"] + sale["total"]
        return {
            "pathway": "combined",
            "sides": [purchase, sale],
            "base_fee": purchase["base_fee"] + sale["base_fee"],
            "adjustments": purchase["adjustments"] + sale["adjustments"],
            "fees_subtotal": purchase["fees_subtotal"] + sale["fees_subtotal"],
            "vat": purchase["vat"] + sale["vat"],
            "disbursements": purchase["disbursements"] + sale["disbursements"],
            "disbursements_total": purchase["disbursements_total"] + sale["disbursements_total"],
            "total": float(_q(_as_decimal(combined_total))),
            "currency": "GBP",
            "pricing_model": "anchor",
            "price_type": price_type.value,
        }

    side = pathway  # "purchase" or "sale"
    quote = _calculate_side(pricing, flags, side, price_type)
    if quote is None:
        return None
    return {
        "pathway": pathway,
        "base_fee": quote["base_fee"],
        "adjustments": quote["adjustments"] + quote["additional_costs"],
        "fees_subtotal": quote["fees_subtotal"],
        "vat": quote["vat"],
        "disbursements": quote["disbursements"],
        "disbursements_total": quote["disbursements_total"],
        "total": quote["total"],
        "currency": "GBP",
        "pricing_model": "anchor",
        "price_type": price_type.value,
    }
