"""Analysis lifecycle state machine (§8).

The ``AnalysisStatus`` enum mirrors the stateDiagram states; ``TRANSITIONS``
encodes the allowed edges. ``assert_transition`` is the single guard the
orchestrator/routers call before mutating ``Analysis.status``.
"""
from __future__ import annotations
import enum


class AnalysisStatus(str, enum.Enum):
    DRAFT = "Draft"
    VALIDATING = "Validating"
    INVALID = "Invalid"
    RUNNING = "Running"
    CONFLICTING_INPUTS = "ConflictingInputs"
    PENDING_REVIEW = "PendingReview"
    EXPERT_REVIEW = "ExpertReview"
    NEEDS_HUMAN_REVIEW = "NeedsHumanReview"
    APPROVED = "Approved"
    CORRECTED = "Corrected"
    FINALIZED = "Finalized"


S = AnalysisStatus

# Allowed transitions (§8). Rerun re-enters RUNNING from a review state.
TRANSITIONS: dict[AnalysisStatus, set[AnalysisStatus]] = {
    S.DRAFT: {S.VALIDATING},
    S.VALIDATING: {S.INVALID, S.RUNNING},
    S.INVALID: set(),
    S.RUNNING: {S.CONFLICTING_INPUTS, S.PENDING_REVIEW, S.EXPERT_REVIEW, S.NEEDS_HUMAN_REVIEW},
    S.CONFLICTING_INPUTS: {S.EXPERT_REVIEW},
    S.PENDING_REVIEW: {S.EXPERT_REVIEW},
    S.NEEDS_HUMAN_REVIEW: {S.EXPERT_REVIEW},
    # An expert reviewing may approve, correct, or rerun (-> RUNNING).
    S.EXPERT_REVIEW: {S.APPROVED, S.CORRECTED, S.RUNNING},
    S.APPROVED: {S.FINALIZED, S.RUNNING},
    S.CORRECTED: {S.FINALIZED, S.RUNNING},
    S.FINALIZED: {S.RUNNING},
}


class IllegalTransition(ValueError):
    pass


def can_transition(src: AnalysisStatus, dst: AnalysisStatus) -> bool:
    return dst in TRANSITIONS.get(src, set())


def assert_transition(src: AnalysisStatus, dst: AnalysisStatus) -> None:
    if not can_transition(src, dst):
        raise IllegalTransition(f"illegal transition {src.value} -> {dst.value}")


# Which lifecycle status a fresh run lands in, given the result status + initiator.
def landing_status(result_status: str, initiator_is_expert: bool) -> AnalysisStatus:
    from .contract import (
        STATUS_OK, STATUS_INVALID_INPUT,
        STATUS_CONFLICTING_INPUTS, STATUS_NEEDS_HUMAN_REVIEW,
    )
    if result_status == STATUS_INVALID_INPUT:
        return S.INVALID
    if result_status == STATUS_CONFLICTING_INPUTS:
        return S.CONFLICTING_INPUTS
    if result_status == STATUS_NEEDS_HUMAN_REVIEW:
        return S.NEEDS_HUMAN_REVIEW
    # OK
    return S.EXPERT_REVIEW if initiator_is_expert else S.PENDING_REVIEW
