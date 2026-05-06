"""Six-factor ranking engine — Annex One §5–9.

Each public function is a pure scorer for a single factor, so they can be
exercised in isolation by `tests/unit/test_ranking.py`. The orchestration
(load all WMCA firms, score them, weight them, rank) lives in
`app.services.search` and consumes these primitives.

Conventions:
    - All factor scores are floats on a 0–100 scale, retained at full
      numerical precision (no rounding) so the weighted scorecard sum
      remains stable and tie-breaks behave deterministically.
    - Edge cases follow Annex One: when normalisation would divide by zero
      (max == min) every firm receives a neutral 50.
    - Reputation, Price and Distance are *relative* (min–max across the
      results set). Complaints, Regulatory and Offices are *absolute*.
"""

import math
from collections.abc import Iterable

# Reputation confidence weighting — Annex One §5.7.1.
REPUTATION_K = 0.025

# Complaint handling penalty when LeO judged the firm's own handling
# unreasonable — Annex One §6.14.
COMPLAINT_HANDLING_PENALTY = 4.0


# ── Reputation (Factor 1, §5) ────────────────────────────────────────────────


def adjusted_reputation_value(rating: float | None, review_count: int | None) -> float:
    """ARV = rating × (1 + k × ln(review_count + 1)).

    Firms with no rating data score 0 ARV (will normalise to 0 unless every
    firm in the set is also unrated, in which case the §5.6 edge case
    assigns 50 to all).
    """
    if not rating:
        return 0.0
    count = review_count or 0
    return float(rating) * (1.0 + REPUTATION_K * math.log(count + 1))


def normalise_reputation(arvs: dict[str, float]) -> dict[str, float]:
    """Min–max normalise ARVs across the results set to 0–100.

    Per §5.6 edge case: if highest == lowest, every firm scores 50.
    """
    if not arvs:
        return {}
    values = list(arvs.values())
    lo, hi = min(values), max(values)
    if hi == lo:
        return {k: 50.0 for k in arvs}
    span = hi - lo
    return {k: (v - lo) / span * 100.0 for k, v in arvs.items()}


# ── Price (Factor 2, §6) ─────────────────────────────────────────────────────


def normalise_price(prices: dict[str, float]) -> dict[str, float]:
    """(P_max − P_effective) / (P_max − P_min) × 100 — Annex One §6.21.

    Lower price → higher score. Firms with no quote (`None`) are excluded
    upstream; this function only sees firms with a Total Effective Price.
    Per §6.21.4 edge case, all-equal prices → 50 for every firm.
    """
    if not prices:
        return {}
    values = list(prices.values())
    lo, hi = min(values), max(values)
    if hi == lo:
        return {k: 50.0 for k in prices}
    span = hi - lo
    return {k: (hi - v) / span * 100.0 for k, v in prices.items()}


# ── Complaints (Factor 3, §6) ────────────────────────────────────────────────


def score_complaints(decisions: Iterable) -> float:
    """Absolute, base 100. Per-decision deduction = (severity × remedy) +
    handling_penalty (4 if unreasonable handling, else 0). Aggregated
    additively across decisions — Annex One §6.16. No floor.
    """
    total_deduction = 0.0
    for d in decisions:
        per_decision = float(d.severity_score) * float(d.remedy_amount_score)
        if d.complaint_handling_penalty:
            per_decision += COMPLAINT_HANDLING_PENALTY
        total_deduction += per_decision
    return 100.0 - total_deduction


# ── Regulatory (Factor 4, §7) ────────────────────────────────────────────────


def score_regulatory(decisions: Iterable) -> float:
    """Absolute, base 100. Sum of per-decision deductions (pre-computed at
    ingest from the §7.3 SRA / §7.5 SDT tables). No floor — score may be
    negative. Intervention is a binary eligibility filter handled
    upstream in `search.py` and never reaches this scorer.
    """
    return 100.0 - sum(float(d.deduction) for d in decisions)


# ── Distance (Factor 5, §8) ──────────────────────────────────────────────────


def score_distance(distances: dict[str, float]) -> dict[str, float]:
    """(D_max − D_firm) / (D_max − D_min) × 100 — Annex One §8.3.9.

    Closer firms score higher. All-equal distances → 50 for every firm
    (§8.4 edge case).
    """
    if not distances:
        return {}
    values = list(distances.values())
    lo, hi = min(values), max(values)
    if hi == lo:
        return {k: 50.0 for k in distances}
    span = hi - lo
    return {k: (hi - v) / span * 100.0 for k, v in distances.items()}


# ── Offices (Factor 6, §9) ───────────────────────────────────────────────────


def score_offices(office_count: int) -> float:
    """Banded score — Annex One §9.4: 1→70, 2–3→78, 4–6→85, 7–10→90,
    11–20→95, 21+→100. Zero / missing offices fall to the 1-office band
    (firms are SRA-regulated and must have a registered address).
    """
    if office_count >= 21:
        return 100.0
    if office_count >= 11:
        return 95.0
    if office_count >= 7:
        return 90.0
    if office_count >= 4:
        return 85.0
    if office_count >= 2:
        return 78.0
    return 70.0
