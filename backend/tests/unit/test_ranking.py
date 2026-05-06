"""Unit tests for app.services.ranking — the six factor scorers.

Each scorer covers an Annex One section:
    - score_offices                   §9.4
    - normalise_reputation / ARV      §5
    - normalise_price                 §6.21
    - score_complaints                §6.16
    - score_regulatory                §7.3 / §7.5
    - score_distance                  §8.3.9
"""

import math
import pytest

from app.services.ranking import (
    COMPLAINT_HANDLING_PENALTY,
    REPUTATION_K,
    adjusted_reputation_value,
    normalise_price,
    normalise_reputation,
    score_complaints,
    score_distance,
    score_offices,
    score_regulatory,
)


# ── Reputation (§5) ──────────────────────────────────────────────────────────


def test_arv_worked_example_from_annex_one():
    """Annex One §5.7 worked example: 4.6 × 200 reviews ≈ 5.21."""
    arv = adjusted_reputation_value(4.6, 200)
    assert arv == pytest.approx(4.6 * (1 + REPUTATION_K * math.log(201)))
    assert round(arv, 2) == pytest.approx(5.21, abs=0.01)


def test_arv_handles_zero_reviews_without_log_zero():
    """ln(0+1) = 0 → ARV equals the raw rating."""
    assert adjusted_reputation_value(5.0, 0) == pytest.approx(5.0)


def test_arv_treats_missing_rating_as_zero():
    assert adjusted_reputation_value(None, 100) == 0.0
    assert adjusted_reputation_value(0, 100) == 0.0


def test_normalise_reputation_min_max_spreads_to_0_and_100():
    arvs = {"a": 5.30, "b": 5.21, "c": 4.20}
    out = normalise_reputation(arvs)
    assert out["a"] == pytest.approx(100.0)
    assert out["c"] == pytest.approx(0.0)
    assert 0 < out["b"] < 100


def test_normalise_reputation_returns_50_when_all_equal():
    """§5.6 edge case: identical ARVs → neutral 50 for everyone."""
    out = normalise_reputation({"a": 4.0, "b": 4.0, "c": 4.0})
    assert out == {"a": 50.0, "b": 50.0, "c": 50.0}


def test_normalise_reputation_empty_input():
    assert normalise_reputation({}) == {}


# ── Price (§6) ───────────────────────────────────────────────────────────────


def test_normalise_price_lower_price_gets_higher_score():
    out = normalise_price({"cheap": 1000.0, "mid": 1500.0, "dear": 2000.0})
    assert out["cheap"] == pytest.approx(100.0)
    assert out["dear"] == pytest.approx(0.0)
    assert out["mid"] == pytest.approx(50.0)


def test_normalise_price_returns_50_when_all_equal():
    out = normalise_price({"a": 1500.0, "b": 1500.0})
    assert out == {"a": 50.0, "b": 50.0}


# ── Complaints (§6) ──────────────────────────────────────────────────────────


class _Decision:
    """Minimal stand-in for ComplaintsDecision / RegulatoryDecision used by
    the scorers — they only consume duck-typed attribute access."""

    def __init__(self, **kw):
        self.__dict__.update(kw)


def test_complaints_no_decisions_returns_full_100():
    assert score_complaints([]) == 100.0


def test_complaints_single_decision_severity_times_remedy():
    """Annex One §6.16 worked: financial compensation (1.00) × £1k–£5k (22)
    with no handling penalty = 22; from base 100 → 78."""
    d = _Decision(severity_score=1.0, remedy_amount_score=22, complaint_handling_penalty=False)
    assert score_complaints([d]) == pytest.approx(78.0)


def test_complaints_handling_penalty_adds_four_per_decision():
    """§6.14: +4 per decision where complaint handling was unreasonable."""
    d = _Decision(severity_score=1.0, remedy_amount_score=22, complaint_handling_penalty=True)
    assert score_complaints([d]) == pytest.approx(100.0 - 22.0 - COMPLAINT_HANDLING_PENALTY)


def test_complaints_decisions_aggregate_additively():
    """§6.17: multiple decisions sum without adjustment for repetition."""
    d1 = _Decision(severity_score=0.30, remedy_amount_score=10, complaint_handling_penalty=False)
    d2 = _Decision(severity_score=0.60, remedy_amount_score=15, complaint_handling_penalty=True)
    # d1 = 0.30 × 10 = 3; d2 = 0.60 × 15 + 4 = 13; total 16; from 100 → 84.
    assert score_complaints([d1, d2]) == pytest.approx(84.0)


def test_complaints_score_can_go_negative():
    """No floor — §6 specifies absolute aggregation, no minimum imposed."""
    d = _Decision(severity_score=1.0, remedy_amount_score=62, complaint_handling_penalty=True)
    # 62 + 4 = 66; from 100 → 34. Stack ten of them to test negative.
    assert score_complaints([d] * 10) == pytest.approx(100.0 - 10 * 66.0)


# ── Regulatory (§7) ──────────────────────────────────────────────────────────


def test_regulatory_no_decisions_returns_full_100():
    assert score_regulatory([]) == 100.0


def test_regulatory_aggregates_per_decision_deductions():
    """§7.3: rebuke (-5) + Band B (-15) + Conditions (-25) = -45 → 55."""
    decisions = [
        _Decision(deduction=5),
        _Decision(deduction=15),
        _Decision(deduction=25),
    ]
    assert score_regulatory(decisions) == pytest.approx(55.0)


def test_regulatory_score_can_go_negative():
    """§7.4.5: no minimum imposed."""
    decisions = [_Decision(deduction=60), _Decision(deduction=60)]
    assert score_regulatory(decisions) == pytest.approx(-20.0)


# ── Distance (§8) ────────────────────────────────────────────────────────────


def test_distance_closer_scores_higher():
    out = score_distance({"near": 2.0, "mid": 10.0, "far": 30.0})
    assert out["near"] == pytest.approx(100.0)
    assert out["far"] == pytest.approx(0.0)
    assert 0 < out["mid"] < 100


def test_distance_returns_50_when_all_equal():
    """§8.4 edge case: D_max == D_min → all firms 50."""
    assert score_distance({"a": 5.0, "b": 5.0}) == {"a": 50.0, "b": 50.0}


def test_distance_empty_input():
    assert score_distance({}) == {}


# ── Offices (§9) ─────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "count,expected",
    [
        (1, 70.0),
        (2, 78.0),
        (3, 78.0),
        (4, 85.0),
        (6, 85.0),
        (7, 90.0),
        (10, 90.0),
        (11, 95.0),
        (20, 95.0),
        (21, 100.0),
        (500, 100.0),
    ],
)
def test_offices_banded_scoring(count: int, expected: float):
    """Annex One §9.4 banded score — saturates at 21+."""
    assert score_offices(count) == expected


def test_offices_zero_or_negative_treated_as_minimum_band():
    """Defensive: an SRA-regulated firm must have ≥1 registered address;
    if data is missing we floor to the 1-office band rather than crash."""
    assert score_offices(0) == 70.0
    assert score_offices(-1) == 70.0
