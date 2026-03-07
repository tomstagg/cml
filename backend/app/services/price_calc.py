"""Price calculator: probate answers → itemised quote from a price card."""

from decimal import ROUND_HALF_UP, Decimal

VAT_RATE = Decimal("0.20")


def calculate_quote(pricing: dict, complexity: dict) -> dict | None:
    """
    Given a price card's pricing JSONB and complexity flags from chat answers,
    return an itemised quote dict or None if no matching band found.

    pricing schema:
    {
      "practice_area": "probate",
      "matter_types": ["grant_only", "full_administration"],
      "pricing_model": "fixed|band|percentage",
      "bands": [{"estate_value_min": 0, "estate_value_max": 325000, "fee": 1500, "currency": "GBP"}],
      "adjustments": [{"name": "...", "amount": 500}],
      "disbursements": [{"name": "...", "amount": 273, "estimated": false}],
      "vat_applies_to_fees": true
    }
    """
    if not pricing:
        return None

    matter_types = pricing.get("matter_types", ["full_administration"])
    service_type = complexity.get("service_type", "full_administration")
    if service_type not in matter_types:
        return None

    estate_value = Decimal(str(complexity.get("estate_value", 212500)))
    pricing_model = pricing.get("pricing_model", "band")

    # --- Base fee ---
    base_fee = Decimal("0")
    if pricing_model in ("fixed", "band"):
        bands = pricing.get("bands", [])
        matched_band = None
        for band in bands:
            min_val = Decimal(str(band.get("estate_value_min", 0)))
            max_val = band.get("estate_value_max")
            if max_val is None:
                if estate_value >= min_val:
                    matched_band = band
                    break
            else:
                if min_val <= estate_value <= Decimal(str(max_val)):
                    matched_band = band
                    break

        if matched_band is None:
            return None
        base_fee = Decimal(str(matched_band.get("fee", 0)))

    elif pricing_model == "percentage":
        pct = Decimal(str(pricing.get("percentage_rate", 1.5))) / 100
        base_fee = (estate_value * pct).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # --- Adjustments ---
    adjustments = []
    adjustment_total = Decimal("0")

    for adj in pricing.get("adjustments", []):
        applies = True
        condition = adj.get("condition")
        if condition == "iht400" and not complexity.get("has_iht400"):
            applies = False
        if condition == "overseas_assets" and not complexity.get("has_overseas_assets"):
            applies = False
        if condition == "complex_investments" and not complexity.get("has_complex_investments"):
            applies = False

        if applies:
            amount = Decimal(str(adj.get("amount", 0)))
            adjustments.append({"name": adj["name"], "amount": float(amount)})
            adjustment_total += amount

    fees_subtotal = base_fee + adjustment_total

    # --- VAT ---
    vat_applies = pricing.get("vat_applies_to_fees", True)
    vat_amount = (
        (fees_subtotal * VAT_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if vat_applies
        else Decimal("0")
    )

    # --- Disbursements (no VAT) ---
    disbursements = []
    disbursement_total = Decimal("0")
    for disb in pricing.get("disbursements", []):
        amount = Decimal(str(disb.get("amount", 0)))
        disbursements.append(
            {
                "name": disb["name"],
                "amount": float(amount),
                "estimated": disb.get("estimated", False),
            }
        )
        disbursement_total += amount

    total = fees_subtotal + vat_amount + disbursement_total

    return {
        "base_fee": float(base_fee),
        "adjustments": adjustments,
        "fees_subtotal": float(fees_subtotal),
        "vat": float(vat_amount),
        "disbursements": disbursements,
        "disbursements_total": float(disbursement_total),
        "total": float(total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        "currency": "GBP",
        "pricing_model": pricing_model,
    }
