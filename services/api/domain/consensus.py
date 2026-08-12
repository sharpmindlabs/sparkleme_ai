"""Multi-model consensus (§5.5 engine block, FR-7.1).

Votes outside the candidate set are discarded and logged (acceptance criterion
#1). Ties break by a *fixed* model ordering for determinism (NFR-Determinism).
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class ModelVote:
    model_id: str
    vote: str          # palette
    weight: float = 1.0
    order: int = 0     # fixed registry order for deterministic tie-break


@dataclass
class ConsensusOutcome:
    strategy: str
    final_palette: str | None
    vote_weights: dict[str, float]           # palette -> summed weight (accepted only)
    accepted_votes: list[dict] = field(default_factory=list)
    discarded_votes: list[dict] = field(default_factory=list)
    tally: dict[str, float] = field(default_factory=dict)


STRATEGY_WEIGHTED_MAJORITY = "weighted_majority"
STRATEGY_AUDITOR_SCORED = "auditor_scored"
STRATEGY_UNANIMITY = "unanimity"


def weighted_majority(
    votes: list[ModelVote],
    candidate_set: list[str],
    strategy: str = STRATEGY_WEIGHTED_MAJORITY,
) -> ConsensusOutcome:
    cs = set(candidate_set)
    accepted: list[ModelVote] = []
    discarded: list[dict] = []
    for v in votes:
        if v.vote in cs:
            accepted.append(v)
        else:
            discarded.append({"model": v.model_id, "vote": v.vote, "reason": "outside_candidate_set"})

    tally: dict[str, float] = {}
    for v in accepted:
        tally[v.vote] = tally.get(v.vote, 0.0) + v.weight

    if not tally:
        return ConsensusOutcome(
            strategy=strategy, final_palette=None, vote_weights={},
            accepted_votes=[], discarded_votes=discarded, tally={},
        )

    # Deterministic tie-break: highest weight, then lowest min registry order of
    # a model that voted for it, then alphabetical palette.
    order_of: dict[str, int] = {}
    for v in accepted:
        order_of[v.vote] = min(order_of.get(v.vote, 1 << 30), v.order)

    def sort_key(item):
        palette, w = item
        return (-w, order_of.get(palette, 1 << 30), palette)

    if strategy == STRATEGY_UNANIMITY and len(tally) > 1:
        # Not unanimous -> escalate (no winner).
        final = None
    else:
        final = sorted(tally.items(), key=sort_key)[0][0]

    return ConsensusOutcome(
        strategy=strategy,
        final_palette=final,
        vote_weights=dict(tally),
        accepted_votes=[{"model": v.model_id, "vote": v.vote, "weight": v.weight} for v in accepted],
        discarded_votes=discarded,
        tally=dict(tally),
    )
