"""Output-contract validation (§5.5 hard constraints).

A result that violates any hard constraint becomes ``NEEDS_HUMAN_REVIEW`` and is
*never silently fixed*.
"""
from __future__ import annotations
from dataclasses import dataclass, field

from .palettes import (
    PALETTE_SET, HOME_SEASONS, SEASON_UNDERTONE, is_valid_flow,
)

# Result-level status (§5.5), distinct from the lifecycle status in §8.
STATUS_OK = "OK"
STATUS_INVALID_INPUT = "INVALID_INPUT"
STATUS_CONFLICTING_INPUTS = "CONFLICTING_INPUTS"
STATUS_NEEDS_HUMAN_REVIEW = "NEEDS_HUMAN_REVIEW"


@dataclass
class ContractCheck:
    ok: bool
    violations: list[str] = field(default_factory=list)


def validate_output_contract(
    *,
    undertone: str | None,
    home_season: str | None,
    flow_result: str | None,
    candidate_set: list[str],
) -> ContractCheck:
    """Enforce the three §5.5 hard constraints:

    1. ``flow_result ∈ candidate_set``
    2. flow valid for ``home_season``
    3. ``home_season`` consistent with ``undertone``
    """
    violations: list[str] = []

    if flow_result not in PALETTE_SET:
        violations.append(f"flow_result '{flow_result}' is not one of the ten palettes")
    if home_season not in HOME_SEASONS:
        violations.append(f"home_season '{home_season}' is not a valid season")
    if undertone not in ("Cool", "Warm"):
        violations.append(f"undertone '{undertone}' is not Cool/Warm")

    # Constraint 1: within candidate set.
    if flow_result not in set(candidate_set):
        violations.append(
            f"flow_result '{flow_result}' is not in candidate_set {candidate_set}"
        )

    # Constraint 2: flow valid for home season.
    if home_season in HOME_SEASONS and not is_valid_flow(flow_result, home_season):
        violations.append(
            f"flow_result '{flow_result}' is not a valid flow of home_season '{home_season}'"
        )

    # Constraint 3: home season consistent with undertone.
    if home_season in HOME_SEASONS:
        expected = SEASON_UNDERTONE[home_season]
        if undertone != expected:
            violations.append(
                f"undertone '{undertone}' inconsistent with home_season "
                f"'{home_season}' (expected {expected})"
            )

    return ContractCheck(ok=not violations, violations=violations)
