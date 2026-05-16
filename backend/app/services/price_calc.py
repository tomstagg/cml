"""Conveyancing price calculator (Master Export anchor-point edition).

The Master Export workbook supplies per-firm anchor prices at seven CML-defined
purchase-price points (£150k → £1.5m) for each of four matter combinations
(freehold/leasehold × purchase/sale). The runtime ranker only needs a
deterministic Total Effective Price per firm to feed the price factor; this
calculator picks the *nearest* anchor to the user's purchase price.

Out of scope for this pass (tracked in the plan, follow-up needed):
    - Linear interpolation between adjacent anchors
    - Modifier application (new build, shared ownership, etc.)
    - Additional cost application (ID verification, SDLT admin fee, etc.)
    - VAT and confidence uplift `c = 0.075` for Estimated prices (Annex One §10)
"""

from decimal import ROUND_HALF_UP, Decimal

VAT_RATE = Decimal("0.20")
PENNY = Decimal("0.01")

# CML-defined anchor points on the Master Export "Price" tab.
ANCHORS = (150_000, 250_000, 500_000, 750_000, 1_000_000, 1_250_000, 1_500_000)


def _q(value: Decimal) -> Decimal:
    return value.quantize(PENNY, rounding=ROUND_HALF_UP)


def _nearest_anchor(purchase_price: int) -> int:
    """Pick the closest of the seven CML anchor points to the user's price."""
    return min(ANCHORS, key=lambda a: abs(a - purchase_price))


def _matter_path(answers: dict) -> tuple[str, str] | None:
    """Resolve (tenure, transaction) tuple from intake flags, or None."""
    tenure = (answers.get("tenure") or "").lower()
    if tenure not in ("freehold", "leasehold"):
        return None
    txn = (answers.get("transaction_type") or "").lower()
    if txn not in ("purchase", "sale"):
        return None
    return tenure, txn


def calculate_total_effective_price(price_card: dict, answers: dict) -> dict | None:
    """Return an itemised quote dict, or None if no anchor price is available.

    Output shape preserved from the previous calculator for compatibility:
        {
          "base_fee": float,
          "adjustments": [],
          "fees_subtotal": float,
          "vat": float,
          "disbursements": [],
          "disbursements_total": float,
          "total": float,
          "currency": "GBP",
          "pricing_model": "anchor",
        }
    """
    if not price_card:
        return None

    path = _matter_path(answers)
    if path is None:
        return None
    tenure, txn = path

    purchase_price = int(answers.get("purchase_price", 0) or 0)
    if purchase_price <= 0:
        return None

    anchors = price_card.get(tenure, {}).get(txn, {}) or {}
    if not anchors:
        return None

    chosen = _nearest_anchor(purchase_price)
    # Anchor keys may be ints or strings depending on JSON serialisation.
    raw = anchors.get(chosen, anchors.get(str(chosen)))
    if raw is None:
        return None

    base_fee = Decimal(str(raw))
    fees_subtotal = base_fee
    vat_amount = _q(fees_subtotal * VAT_RATE)
    total = fees_subtotal + vat_amount

    return {
        "base_fee": float(base_fee),
        "adjustments": [],
        "fees_subtotal": float(fees_subtotal),
        "vat": float(vat_amount),
        "disbursements": [],
        "disbursements_total": 0.0,
        "total": float(_q(total)),
        "currency": "GBP",
        "pricing_model": "anchor",
    }
