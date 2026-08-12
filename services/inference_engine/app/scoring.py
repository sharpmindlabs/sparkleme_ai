"""Score model predictions against Carol's ground truth (lenient on boundaries)."""
from __future__ import annotations

from .palettes import PALETTES, canonical_ground_truth, neighbours
from .schema import CaseResult, BatchSummary


def score_case(predicted: str | None, carol_raw: str | None) -> tuple[bool, str, str | None, list[str]]:
    """Return (match, match_kind, carol_primary, carol_accepted).

    - exact:    prediction == Carol's primary palette
    - boundary: prediction is in Carol's explicitly-named boundary set, OR a
                direct neighbour of her primary when she flagged a boundary
    - miss:     otherwise
    """
    gt = canonical_ground_truth(carol_raw or "")
    primary = gt["primary"]
    accepted = gt["accepted"]
    if primary is None:
        return (False, "no_ground_truth", None, [])
    if predicted is None or predicted not in PALETTES:
        return (False, "error", primary, accepted)
    if predicted == primary:
        return (True, "exact", primary, accepted)
    # Carol named more than one palette (a stated boundary) -> accept any named
    if len(accepted) > 1 and predicted in accepted:
        return (True, "boundary", primary, accepted)
    return (False, "miss", primary, accepted)


def summarize(cases: list[CaseResult], model: str, provider: str) -> BatchSummary:
    scored = [c for c in cases if c.match_kind not in ("no_ground_truth",)]
    exact = sum(1 for c in scored if c.match_kind == "exact")
    boundary = sum(1 for c in scored if c.match_kind == "boundary")
    errors = sum(1 for c in scored if c.match_kind == "error")
    misses = sum(1 for c in scored if c.match_kind == "miss")
    n = len(scored)
    # confusion: carol_primary -> predicted -> count
    confusion: dict[str, dict[str, int]] = {}
    for c in scored:
        if not c.carol_primary:
            continue
        pred = c.predicted or "(none)"
        confusion.setdefault(c.carol_primary, {}).setdefault(pred, 0)
        confusion[c.carol_primary][pred] += 1
    return BatchSummary(
        model=model, provider=provider, total=len(cases), scored=n,
        exact=exact, boundary=boundary, misses=misses, errors=errors,
        accuracy=round((exact + boundary) / n, 4) if n else 0.0,
        exact_accuracy=round(exact / n, 4) if n else 0.0,
        confusion=confusion, cases=cases,
    )
