"""Unit tests for app.services.scorecard — weight tables and §11 tie-break.

Annex One §16.6 fixes the seven weight sets verbatim; these tests pin the
table so an accidental edit would break the build. §11 specifies the
deterministic tie-break order all the way down to alphabetical fallback.
"""

import pytest

from app.services.scorecard import (
    FACTORS,
    SCORECARDS,
    FactorScores,
    RankableFirm,
    apply,
    overall_score,
    resolve_weights,
)


# ── Weight tables (§16.6) ────────────────────────────────────────────────────


def test_every_scorecard_sums_to_100():
    """Annex One §16.6 — integer weights summing to exactly 100."""
    for name, weights in SCORECARDS.items():
        assert sum(weights.values()) == 100, f"{name} does not sum to 100"


def test_balanced_scorecard_matches_annex_one():
    assert SCORECARDS["balanced"] == {
        "reputation": 25,
        "price": 25,
        "complaints": 15,
        "regulatory": 15,
        "distance": 10,
        "offices": 10,
    }


def test_priority_factor_always_weighted_40():
    """§16.7.1 — the selected priority always gets 40."""
    for priority in ("reputation", "price", "complaints", "regulatory", "distance", "offices"):
        assert SCORECARDS[priority][priority] == 40


def test_every_scorecard_covers_all_six_factors():
    for name, weights in SCORECARDS.items():
        assert set(weights.keys()) == set(FACTORS), f"{name} factor coverage"


# ── Distance excluded — proportional rescale (§8.2) ──────────────────────────


def test_resolve_weights_keeps_distance_when_included():
    weights = resolve_weights("balanced", include_distance=True)
    assert weights["distance"] == 10.0
    assert sum(weights.values()) == pytest.approx(100.0)


def test_resolve_weights_zeroes_distance_when_excluded_and_rescales_others():
    """§8.2: opting out of distance proportionately rescales remaining
    factors. Balanced: rep+price+comp+reg+off = 90 → scale by 100/90."""
    weights = resolve_weights("balanced", include_distance=False)
    assert weights["distance"] == 0.0
    assert sum(weights.values()) == pytest.approx(100.0)
    # Original ratios preserved between non-distance factors.
    assert weights["reputation"] == pytest.approx(25 * 100 / 90)
    assert weights["price"] == pytest.approx(25 * 100 / 90)
    assert weights["offices"] == pytest.approx(10 * 100 / 90)


def test_resolve_weights_rescale_for_prioritised_scorecard():
    """Cost-priority excluded distance: 40+20+12+12+8 = 92 → scale 100/92."""
    weights = resolve_weights("price", include_distance=False)
    assert weights["distance"] == 0.0
    assert sum(weights.values()) == pytest.approx(100.0)
    assert weights["price"] == pytest.approx(40 * 100 / 92)


def test_resolve_weights_unknown_preference_falls_back_to_balanced():
    weights = resolve_weights("not_a_real_scorecard", include_distance=True)
    assert weights == {f: float(SCORECARDS["balanced"][f]) for f in FACTORS}


# ── overall_score arithmetic ─────────────────────────────────────────────────


def _scores(rep=80, price=80, complaints=80, regulatory=80, distance=80, offices=80):
    return FactorScores(
        reputation=rep,
        price=price,
        complaints=complaints,
        regulatory=regulatory,
        distance=distance,
        offices=offices,
    )


def test_overall_score_all_eighties_with_balanced_weights():
    """80 across the board × balanced weights = 80."""
    weights = resolve_weights("balanced", include_distance=True)
    assert overall_score(_scores(), weights) == pytest.approx(80.0)


def test_overall_score_perfect_factor_scores_yields_100():
    weights = resolve_weights("balanced", include_distance=True)
    assert overall_score(_scores(*[100] * 6), weights) == pytest.approx(100.0)


# ── apply() ranking + tie-break (§11) ────────────────────────────────────────


def _firm(name: str, **score_kwargs) -> RankableFirm:
    return RankableFirm(org_id=name, name=name, scores=_scores(**score_kwargs))


def test_apply_ranks_higher_overall_first():
    firms = [
        _firm("Alpha", rep=50, price=50, complaints=50, regulatory=50, distance=50, offices=70),
        _firm("Bravo", rep=90, price=90, complaints=90, regulatory=90, distance=90, offices=90),
    ]
    ranked = apply(firms, "balanced", include_distance=True)
    assert [f.name for f, _ in ranked] == ["Bravo", "Alpha"]


def test_apply_tie_break_prefers_higher_reputation():
    """§11.2.1 — first tie-break is reputation."""
    firms = [
        _firm("Alpha", rep=80),
        _firm("Bravo", rep=90),
    ]
    # Identical overall (reputation contributes equally to weighted score
    # only when other factors compensate exactly), so we contrive a tie:
    firms = [
        RankableFirm(
            org_id="Alpha",
            name="Alpha",
            scores=FactorScores(
                reputation=70, price=80, complaints=80, regulatory=80, distance=80, offices=80
            ),
        ),
        RankableFirm(
            org_id="Bravo",
            name="Bravo",
            scores=FactorScores(
                reputation=80, price=70, complaints=80, regulatory=80, distance=80, offices=80
            ),
        ),
    ]
    # Balanced rep=25, price=25 → equal contributions, identical overall.
    ranked = apply(firms, "balanced", include_distance=True)
    overall_a = next(s for f, s in ranked if f.name == "Alpha")
    overall_b = next(s for f, s in ranked if f.name == "Bravo")
    assert overall_a == pytest.approx(overall_b)
    # Bravo has higher reputation → ranks first under tie-break #1.
    assert [f.name for f, _ in ranked] == ["Bravo", "Alpha"]


def test_apply_alphabetical_final_fallback():
    """§11.2.7 — alphabetical when every other score is identical."""
    firms = [_firm("Charlie"), _firm("Alpha"), _firm("Bravo")]
    ranked = apply(firms, "balanced", include_distance=True)
    assert [f.name for f, _ in ranked] == ["Alpha", "Bravo", "Charlie"]


def test_apply_distance_excluded_rescales_weights_in_overall():
    """A firm with weak distance shouldn't be penalised when the user
    opted out of distance — verify the rescaling actually flows through
    overall_score."""
    weak_distance = _firm("Weak", distance=0)
    strong_distance = _firm("Strong", distance=100)
    # When distance is excluded, both should score identically.
    ranked = apply([weak_distance, strong_distance], "balanced", include_distance=False)
    overall_weak = next(s for f, s in ranked if f.name == "Weak")
    overall_strong = next(s for f, s in ranked if f.name == "Strong")
    assert overall_weak == pytest.approx(overall_strong)
