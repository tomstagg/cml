# Pricing engine — open questions for the data steward

**Audience**: data steward + founder
**Status**: pending sign-off before MVP launch (1 June 2026)
**Owner**: backend (price_calc.py implementation)

---

## Context

The Master Export workbook supplies firm-specific **prices** for a fixed set of conveyancing line-items, but does not specify the **conditions** under which each line-item should be added to a particular user's quote. The runtime pricing engine has to make those condition rules itself.

This document lists the conditions we've assumed, the alternatives, and the questions we need answered to be confident the quotes we surface are correct.

It covers three areas:

1. **Anchor lookup strategy** — how we pick a fee from the seven anchor prices when the user's property value falls between anchors.
2. **Modifier trigger conditions** — when each conditional supplement (e.g. "Purchase - Acting for lender") is added.
3. **Additional-cost trigger conditions** — when each standing admin fee (e.g. "Additional - ID verification") is added.

Once these are settled, the engine becomes deterministic and defensible. Until then, the live quotes for combined Sale & Purchase matters, and any matter involving the open-to-interpretation modifiers, are best-effort.

---

## 1. Anchor lookup strategy

The Price tab supplies fees at **seven anchor purchase prices** per matter combination (Freehold Purchase, Freehold Sale, Leasehold Purchase, Leasehold Sale):

| Anchor | £150k | £250k | £500k | £750k | £1m | £1.25m | £1.5m |

The user's actual property value will almost always fall between two anchors. There are three plausible strategies for picking a fee:

| Strategy | Worked example: user has £300k freehold purchase, Talbots Law (£900 at £250k, £1000 at £500k) | Argument for |
|---|---|---|
| **A — Nearest anchor** | £300k is closer to £250k than to £500k → pick **£900** | Simplest. Currently implemented. |
| **B — Step-up** | £300k is above £250k → falls in the "up to £500k" band → pick **£1,000** | Matches how most conveyancers actually quote ("up to £X"). Defensive — never under-prices the firm. |
| **C — Linear interpolation** | £300k is 1/5 of the way from £250k to £500k → £900 + 1/5 × (£1000 − £900) = **£920** | Most mathematically "fair" — every £ adjusts the fee proportionally. |

**Currently implemented**: A (nearest anchor).
**My recommendation**: B (step-up) — matches conveyancing convention and avoids any risk of presenting a firm at a fee lower than they'd actually charge.

> ❓ **Question 1**: Should the engine use Nearest, Step-up, or Linear interpolation when the user's value falls between anchors?

---

## 2. Master Export Price tab — what the data supplies

For each firm, the Price tab supplies **one £ amount** for each of 13 line-items. Below is Talbots Law (CML-001) as a worked example.

| # | Row name on Price tab | Talbots' amount | What the data says about *when* to apply it |
|---|---|---|---|
| 1 | Purchase - New build (freehold) | £0 | Nothing — row name only |
| 2 | Purchase - New lease (leasehold) | £0 | Nothing — row name only |
| 3 | Purchase - Acting for lender | £100 | Nothing — row name only |
| 4 | Purchase - Shared ownership/Help to Buy | £250 | Nothing — row name only |
| 5 | Purchase - Gifted deposit | £75 | Nothing — row name only |
| 6 | Purchase - Unregistered title | £150 | Nothing — row name only |
| 7 | Sale - Unregistered title | £150 | Nothing — row name only |
| 8 | Sale - Additional mortgage redemption | £100 | Nothing — row name only |
| 9 | Additional - ID verification | £8 | Nothing — row name only |
| 10 | Additional - onboarding fee | £0 | Nothing — row name only |
| 11 | Additional - transfer admin fee | £40 | Nothing — row name only |
| 12 | SDLT admin fee | £80 | Nothing — row name only |
| 13 | Leasehold admin fee | £250 | Nothing — row name only |

The Data catalogue tab on the workbook describes these as *"Transaction-specific factors that modify the price"* and *"Standing additional fees some firms charge for specific tasks"* — but doesn't list the trigger conditions per row.

---

## 3. Modifier trigger conditions (rows 1-8)

These are conditional supplements — they should only be added to a user's quote in specific circumstances.

| Row | My implemented trigger | Confidence | Risk if wrong |
|---|---|---|---|
| Purchase - New build (freehold) | `new_build` checkbox AND `purchase_tenure = freehold` AND purchase side | **High** — row name pins tenure | Low |
| Purchase - New lease (leasehold) | `new_lease` checkbox AND `purchase_tenure = leasehold` AND purchase side | **High** — row name pins tenure | Low |
| Purchase - Acting for lender | `mortgage_required` checkbox AND purchase side | **Medium** — "lender" implies mortgage but isn't stated | Mis-applied on every mortgage-purchase quote |
| Purchase - Shared ownership/Help to Buy | `shared_ownership_or_help_to_buy` checkbox AND purchase side | **High** — direct label match | Low |
| Purchase - Gifted deposit | `gifted_deposit` checkbox AND purchase side | **High** — direct label match | Low |
| Purchase - Unregistered title | `unregistered_title_purchase` checkbox AND purchase side | **High** — direct label match | Low |
| Sale - Unregistered title | `unregistered_title_sale` checkbox AND sale side | **High** — direct label match | Low |
| Sale - Additional mortgage redemption | `additional_mortgage_redemption` checkbox AND sale side | **High** — direct label match | Low |

> ❓ **Question 2**: Confirm "Purchase - Acting for lender" fires when the user has indicated a mortgage on the purchase side, and never otherwise.

> ❓ **Question 3**: Confirm none of these modifiers have hidden conditions beyond what's in the row name (e.g. a firm price applying only above a certain property value).

---

## 4. Additional-cost trigger conditions (rows 9-13)

These are described in the catalogue as "Standing additional fees some firms charge for specific tasks, usually administrative".

| Row | My implemented trigger | Rationale |
|---|---|---|
| Additional - ID verification | **Always apply** | Every conveyancer does AML/KYC ID checks per client. |
| Additional - onboarding fee | **Always apply** | Assumed always charged for a new instruction. |
| Additional - transfer admin fee | **Always apply** | Conveyancing inherently involves a transfer registration. |
| SDLT admin fee | Apply only on **purchase side** | SDLT (Stamp Duty Land Tax) is payable only by buyers under UK law. |
| Leasehold admin fee | Apply only when that side's `tenure = leasehold` | Row name pins tenure. |

The first three are coded as "always apply". This is the **biggest unresolved question** in this engine.

For a Buying-only matter, the user's quote includes a single dose of each. For a Combined Sale & Purchase, my current code applies them **once per side** — i.e. ID verification is added twice, onboarding twice, transfer admin twice. Total impact for Talbots: £48 × 2 = £96 of admin fees rather than £48.

This may or may not match what the firm intended. Some firms onboard a client once and then handle both sides under the same retainer (£48 total); others treat each transaction as a discrete instruction with its own admin overhead (£96 total).

> ❓ **Question 4**: For a Combined Sale & Purchase, do the always-apply admin fees (ID verification, onboarding fee, transfer admin fee) apply:
>
> - **(a)** once total per matter, or
> - **(b)** once per side (so a combined matter sees them twice)?

> ❓ **Question 5**: Are there any always-apply additional costs that should *not* apply in a particular scenario (e.g. is "Transfer admin fee" ever skipped)?

---

## 5. Other assumptions worth confirming

### Disbursements

The Price tab supplies one disbursement: "Disb - searches (CML standard pack) £350". The Data catalogue says searches are *"held constant for the purposes of achieving comparability"* (i.e. £350 across all firms, not firm-specific).

| Sub-question | My implementation | Risk if wrong |
|---|---|---|
| Does VAT apply to the £350 searches figure? | **Yes — £350 × 1.20 = £420** included in `P_effective`. UK convention is that search packs from companies like SearchFlow attract VAT. | If wrong, quotes are over-stated by ~£70 per matter. |
| Does the `d = 0.02` confidence factor on estimated disbursements apply? | **No** — searches is a standardised constant per the catalogue, not estimated firm data. | Marginal — £420 × 0.02 ≈ £8 per matter. |

> ❓ **Question 6**: Confirm searches £350 is VAT-able (i.e. add 20% to make £420 in the quote).

> ❓ **Question 7**: Confirm `d = 0.02` is not applied to searches (because it's a fixed standardised pack, not estimated).

### Estimated vs Verified

The `c = 0.075` confidence uplift in Annex One §10 is applied to legal fees from **Estimated** price cards but not Verified ones. Of the 22 pilot firms, 20 are Estimated (data team interpretation of transparency statements) and 2 are No-data (excluded).

The engine handles this correctly: Estimated cards multiply the legal-fee subtotal by 1.075 before VAT. No question needed here, but worth flagging.

---

## 6. Summary — questions for the data steward

| # | Question | Default if no answer |
|---|---|---|
| 1 | Anchor lookup strategy — Nearest, Step-up, or Linear interpolation? | Currently: Nearest. Recommend: Step-up. |
| 2 | "Purchase - Acting for lender" — is it triggered by the `mortgage_required` checkbox only? | Yes (assumed). |
| 3 | Any hidden conditions on modifiers beyond what's in the row name? | No (assumed). |
| 4 | Combined Sale & Purchase — do always-apply admin fees apply once total or once per side? | Once per side (assumed). |
| 5 | Any always-apply additional costs that should skip in some scenarios? | None (assumed). |
| 6 | Searches £350 — VAT-able? | Yes — adds VAT (assumed). |
| 7 | `d = 0.02` on searches? | No — fixed standard pack (assumed). |

A clear written answer to each, or an annotated copy of this doc back, is enough.

---

## 7. Worked example — Talbots Law CML-001, £300k freehold purchase with mortgage

For reference, here's a full end-to-end calculation as the engine currently runs it. Numbers will change once Questions 1, 2 and 6 are answered.

| Step | Value | Source |
|---|---|---|
| User picks pathway | Buying | Q1 transaction_type |
| Tenure | Freehold | Q2P |
| Purchase value | £300,000 | Q3P |
| Modifiers selected | Mortgage required | Q4 |
| **Anchor fee** (nearest = £250k) | **£900** | Talbots' Price tab |
| Modifier: Purchase - Acting for lender | +£100 | Q2 trigger |
| Additional: ID verification | +£8 | always-apply |
| Additional: onboarding fee | +£0 | always-apply |
| Additional: transfer admin fee | +£40 | always-apply |
| Additional: SDLT admin fee | +£80 | purchase-only |
| Additional: Leasehold admin fee | n/a | freehold → skipped |
| **P_estimated (legal fee subtotal)** | **£1,128** | sum above |
| × `c = 0.075` (Estimated firm) | × 1.075 | Annex One §10 |
| **P_legal_effective** | **£1,212.60** | |
| + 20% VAT on legal fees | + £242.52 | Annex One §10 |
| **Fees including VAT** | **£1,455.12** | |
| + Searches £350 × 1.20 (incl. VAT) | + £420.00 | disbursement |
| **P_effective (Total Effective Price)** | **£1,875.12** | shown to user |

This is the quote a user sees and the figure that feeds the ranking's price factor.

---

## 8. Where this is in the code

- **Anchor lookup**: `backend/app/services/price_calc.py::_nearest_anchor` — change here for Step-up / interpolation.
- **Modifier triggers**: `backend/app/services/price_calc.py::_applicable_modifiers` — one function, ~15 lines, easy to edit.
- **Additional-cost triggers**: `backend/app/services/price_calc.py::_applicable_additional_costs` — one function, ~10 lines.
- **VAT, c-uplift, disbursements**: `backend/app/services/price_calc.py::_calculate_side` — main flow.
- **Combined-pathway summation**: `backend/app/services/price_calc.py::calculate_total_effective_price` — handles dual-side matters.

Unit tests for the engine (`backend/tests/unit/test_price_calc.py`) include the worked example above as `test_full_annex_example_for_estimated_card` — any change in the rules will be picked up there.
