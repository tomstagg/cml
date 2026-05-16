"""Six-factor ranking engine — Annex One §5–9.

Each public function is a pure scorer for a single factor, so they can be
exercised in isolation by `tests/unit/test_ranking.py`. The orchestration
(load all WMCA firms, score them, weight them, rank) lives in
`app.services.search` and consumes these primitives.

Reputation, Complaints and Regulatory factor inputs arrive pre-computed
from the Master Export workbook (Annex One: "all ingestion / cleansing /
normalisation must complete prior to runtime"). The runtime ranker only
normalises across the results set and applies factor weights.

Conventions:
    - All factor scores are floats on a 0–100 scale, retained at full
      numerical precision (no rounding) so the weighted scorecard sum
      remains stable and tie-breaks behave deterministically.
    - Edge cases follow Annex One: when normalisation would divide by zero
      (max == min) every firm receives a neutral 50.
    - Reputation, Price and Distance are *relative* (min–max across the
      results set). Complaints, Regulatory and Offices are *absolute*.
"""


# ── Reputation (Factor 1, §5) ────────────────────────────────────────────────


def normalise_reputation(arvs: dict[str, float]) -> dict[str, float]:
    """Min–max normalise adjusted reputation values across the results set.

    Per §5.6 edge case: if highest == lowest, every firm scores 50. Firms
    with no upstream ARV (`None`) are passed in as 0.0 by the caller.
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
