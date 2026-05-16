"""Unit tests for app.services.ranking — runtime-side scorers.

Reputation, complaints and regulatory scores arrive pre-computed from the
Master Export workbook (per Annex One: all ingestion/normalisation completes
prior to runtime). The remaining runtime work is min-max normalisation of
the relative factors and the absolute offices banding.
"""

import pytest

from app.services.ranking import (
    normalise_price,
    normalise_reputation,
    score_distance,
    score_offices,
)


# ── Reputation normalisation (§5) ────────────────────────────────────────────


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


# ── Price normalisation (§6) ─────────────────────────────────────────────────


def test_normalise_price_lower_price_gets_higher_score():
    out = normalise_price({"cheap": 1000.0, "mid": 1500.0, "dear": 2000.0})
    assert out["cheap"] == pytest.approx(100.0)
    assert out["dear"] == pytest.approx(0.0)
    assert out["mid"] == pytest.approx(50.0)


def test_normalise_price_returns_50_when_all_equal():
    out = normalise_price({"a": 1500.0, "b": 1500.0})
    assert out == {"a": 50.0, "b": 50.0}


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
    assert score_offices(0) == 70.0
    assert score_offices(-1) == 70.0
