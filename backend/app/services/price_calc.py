"""Conveyancing price calculator.

Implements Annex One §10 Total Effective Price for the Quoted Prices path:

    P_legal,effective = P_quoted                       (no `c` confidence uplift this pilot)
    P_effective       = P_legal,effective × (1 + VAT)
                      + Σ included_disbursements (each line's VAT applied per-row flag)

The calculator consumes a price-card JSONB (see `app.schemas.firm.PriceCardData`)
and the normalised conveyancing answers produced by
`app.services.chat.get_intake_flags`.
"""

from decimal import ROUND_HALF_UP, Decimal

VAT_RATE = Decimal("0.20")
PENNY = Decimal("0.01")


def _q(value: Decimal) -> Decimal:
    return value.quantize(PENNY, rounding=ROUND_HALF_UP)


def _condition_applies(condition: str | None, answers: dict) -> bool:
    """Evaluate a price-card adjustment condition against conveyancing answers.

    Supported expressions (case-insensitive on the RHS):
        tenure==leasehold | tenure==freehold
        mortgage==true    | mortgage==false
        new_build==true   | shared_ownership==true | help_to_buy_isa==true
    A None / empty condition always applies.
    """
    if not condition:
        return True

    if "==" not in condition:
        return False

    field, expected = (part.strip() for part in condition.split("==", 1))
    expected = expected.lower()
    actual = answers.get(field)

    if isinstance(actual, bool):
        return ("true" if actual else "false") == expected
    return str(actual).lower() == expected


def calculate_total_effective_price(price_card: dict, answers: dict) -> dict | None:
    """Return an itemised quote dict, or None if no band matches.

    Output shape:
        {
          "base_fee": float,
          "adjustments": [{"name": str, "amount": float}, ...],
          "fees_subtotal": float,
          "vat": float,                      # VAT on legal fees only
          "disbursements": [{"name": str, "amount": float, "vat_applies": bool}, ...],
          "disbursements_total": float,      # sum of disbursement amounts incl. each row's VAT
          "total": float,                    # P_effective
          "currency": "GBP",
          "pricing_model": "fixed" | "band",
        }
    """
    if not price_card:
        return None

    purchase_price = Decimal(str(answers.get("purchase_price", 0) or 0))
    pricing_model = price_card.get("pricing_model", "band")

    # ── Base fee from purchase-price band ──────────────────────────────────
    matched_fee: Decimal | None = None
    for band in price_card.get("bands", []):
        min_val = Decimal(str(band.get("purchase_price_min", 0)))
        max_val = band.get("purchase_price_max")
        if max_val is None:
            if purchase_price >= min_val:
                matched_fee = Decimal(str(band.get("fee", 0)))
                break
        else:
            if min_val <= purchase_price <= Decimal(str(max_val)):
                matched_fee = Decimal(str(band.get("fee", 0)))
                break

    if matched_fee is None:
        return None
    base_fee = matched_fee

    # ── Conditional adjustments ────────────────────────────────────────────
    adjustments: list[dict] = []
    adjustment_total = Decimal("0")
    for adj in price_card.get("adjustments", []):
        if not _condition_applies(adj.get("condition"), answers):
            continue
        amount = Decimal(str(adj.get("amount", 0)))
        adjustments.append({"name": adj["name"], "amount": float(amount)})
        adjustment_total += amount

    fees_subtotal = base_fee + adjustment_total

    # ── VAT on legal fees ──────────────────────────────────────────────────
    vat_amount = (
        _q(fees_subtotal * VAT_RATE)
        if price_card.get("vat_applies_to_fees", True)
        else Decimal("0")
    )

    # ── Included disbursements (each row carries its own VAT flag) ─────────
    disbursements: list[dict] = []
    disbursements_total = Decimal("0")
    for disb in price_card.get("included_disbursements", []):
        net = Decimal(str(disb.get("amount", 0)))
        vat_applies = bool(disb.get("vat_applies", False))
        gross = _q(net * (Decimal("1") + VAT_RATE)) if vat_applies else net
        disbursements.append(
            {
                "name": disb["name"],
                "amount": float(gross),
                "vat_applies": vat_applies,
            }
        )
        disbursements_total += gross

    total = fees_subtotal + vat_amount + disbursements_total

    return {
        "base_fee": float(base_fee),
        "adjustments": adjustments,
        "fees_subtotal": float(fees_subtotal),
        "vat": float(vat_amount),
        "disbursements": disbursements,
        "disbursements_total": float(_q(disbursements_total)),
        "total": float(_q(total)),
        "currency": "GBP",
        "pricing_model": pricing_model,
    }
