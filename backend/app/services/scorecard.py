"""Scorecard weight tables + tie-broken ranking — Annex One §11, §16.

`SCORECARDS` carries the seven weight sets verbatim from the §16.6 table
(Balanced default + six prioritised variants). `apply()` blends per-firm
factor scores into a single overall score, then applies the §11 tie-break
order to produce a deterministic rank.
"""

from dataclasses import dataclass

# §16.6 — six factors × seven scorecards. Integer weights summing to 100.
SCORECARDS: dict[str, dict[str, int]] = {
    "balanced": {
        "reputation": 25,
        "price": 25,
        "complaints": 15,
        "regulatory": 15,
        "distance": 10,
        "offices": 10,
    },
    "reputation": {
        "reputation": 40,
        "price": 20,
        "complaints": 12,
        "regulatory": 12,
        "distance": 8,
        "offices": 8,
    },
    "price": {
        "reputation": 20,
        "price": 40,
        "complaints": 12,
        "regulatory": 12,
        "distance": 8,
        "offices": 8,
    },
    "complaints": {
        "reputation": 18,
        "price": 18,
        "complaints": 40,
        "regulatory": 10,
        "distance": 7,
        "offices": 7,
    },
    "distance": {
        "reputation": 17,
        "price": 17,
        "complaints": 10,
        "regulatory": 10,
        "distance": 40,
        "offices": 6,
    },
    "regulatory": {
        "reputation": 18,
        "price": 18,
        "complaints": 10,
        "regulatory": 40,
        "distance": 7,
        "offices": 7,
    },
    "offices": {
        "reputation": 17,
        "price": 17,
        "complaints": 10,
        "regulatory": 10,
        "distance": 6,
        "offices": 40,
    },
}

FACTORS = ("reputation", "price", "complaints", "regulatory", "distance", "offices")


@dataclass(frozen=True)
class FactorScores:
    """Per-firm scores out of 100, full precision (no rounding)."""

    reputation: float
    price: float
    complaints: float
    regulatory: float
    distance: float  # ignored when distance is excluded
    offices: float


@dataclass(frozen=True)
class RankableFirm:
    """Minimal identity carried through `apply()` so tie-break can
    fall back to alphabetical name order without re-reading the DB.
    """

    org_id: str
    name: str
    scores: FactorScores


def resolve_weights(preference: str, include_distance: bool) -> dict[str, float]:
    """Pick the appropriate weight set, then proportionately rescale to
    sum to 100 if the user opted out of distance — Annex One §8.2.

    Unknown preference falls back to `balanced` (defensive — the chat
    enum prevents this in practice but the ranker shouldn't crash).
    """
    base = SCORECARDS.get(preference, SCORECARDS["balanced"])
    weights: dict[str, float] = {f: float(base[f]) for f in FACTORS}
    if not include_distance:
        weights["distance"] = 0.0
        remaining = sum(w for k, w in weights.items() if k != "distance")
        if remaining > 0:
            scale = 100.0 / remaining
            weights = {k: (w * scale if k != "distance" else 0.0) for k, w in weights.items()}
    return weights


def overall_score(scores: FactorScores, weights: dict[str, float]) -> float:
    """Weighted sum: Σ (factor score × factor weight) / 100.

    Weights are out of 100, so the final overall score is also 0–100
    (or negative, for regulatory-weighted firms with severe deductions).
    """
    return (
        scores.reputation * weights["reputation"]
        + scores.price * weights["price"]
        + scores.complaints * weights["complaints"]
        + scores.regulatory * weights["regulatory"]
        + scores.distance * weights["distance"]
        + scores.offices * weights["offices"]
    ) / 100.0


def apply(
    firms: list[RankableFirm],
    preference: str = "balanced",
    include_distance: bool = False,
) -> list[tuple[RankableFirm, float]]:
    """Rank `firms` highest-first, applying the §11 tie-break order.

    Returns `[(firm, overall_score), ...]` in rank order.

    Tie-break (§11): higher reputation → complaints → regulatory →
    price → distance score (closer = higher) → offices → alphabetical
    by firm name.
    """
    weights = resolve_weights(preference, include_distance)

    def sort_key(f: RankableFirm) -> tuple:
        s = f.scores
        return (
            -overall_score(s, weights),
            -s.reputation,
            -s.complaints,
            -s.regulatory,
            -s.price,
            -s.distance,
            -s.offices,
            f.name.lower(),
        )

    sorted_firms = sorted(firms, key=sort_key)
    return [(f, overall_score(f.scores, weights)) for f in sorted_firms]
