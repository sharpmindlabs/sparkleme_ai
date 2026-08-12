"""Multi-model consensus weighting + candidate-set enforcement (FR-7.1, §5.5)."""
from __future__ import annotations

from services.api.domain.consensus import (
    ModelVote, weighted_majority,
    STRATEGY_WEIGHTED_MAJORITY, STRATEGY_UNANIMITY,
)

CS = ["True Winter", "Cool", "Deep", "Bright"]


def test_weighted_majority_picks_highest_weight():
    votes = [
        ModelVote("m1", "Cool", weight=0.6, order=0),
        ModelVote("m2", "Deep", weight=1.0, order=1),
        ModelVote("m3", "Deep", weight=0.5, order=2),
    ]
    out = weighted_majority(votes, CS, STRATEGY_WEIGHTED_MAJORITY)
    assert out.final_palette == "Deep"
    assert out.vote_weights["Deep"] == 1.5


def test_votes_outside_candidate_set_are_discarded():
    votes = [
        ModelVote("m1", "Light", weight=5.0, order=0),   # outside CS -> discarded
        ModelVote("m2", "Cool", weight=1.0, order=1),
    ]
    out = weighted_majority(votes, CS, STRATEGY_WEIGHTED_MAJORITY)
    assert out.final_palette == "Cool"
    assert any(d["vote"] == "Light" for d in out.discarded_votes)
    assert "Light" not in out.vote_weights


def test_all_votes_discarded_yields_no_winner():
    votes = [ModelVote("m1", "Light", weight=1.0, order=0)]
    out = weighted_majority(votes, CS, STRATEGY_WEIGHTED_MAJORITY)
    assert out.final_palette is None


def test_tie_breaks_by_registry_order_deterministically():
    votes = [
        ModelVote("m1", "Bright", weight=1.0, order=2),
        ModelVote("m2", "Cool", weight=1.0, order=0),
    ]
    out = weighted_majority(votes, CS, STRATEGY_WEIGHTED_MAJORITY)
    # Equal weight -> lower registry order (Cool, order 0) wins.
    assert out.final_palette == "Cool"


def test_unanimity_escalates_on_disagreement():
    votes = [
        ModelVote("m1", "Cool", weight=1.0, order=0),
        ModelVote("m2", "Deep", weight=1.0, order=1),
    ]
    out = weighted_majority(votes, CS, STRATEGY_UNANIMITY)
    assert out.final_palette is None


def test_unanimity_agrees():
    votes = [
        ModelVote("m1", "Cool", weight=1.0, order=0),
        ModelVote("m2", "Cool", weight=1.0, order=1),
    ]
    out = weighted_majority(votes, CS, STRATEGY_UNANIMITY)
    assert out.final_palette == "Cool"
