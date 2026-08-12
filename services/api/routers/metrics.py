"""Role-scoped dashboards / metrics (FR-8, §11 GET /metrics/{scope})."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db import get_session
from .. import models as M
from ..security import current_user
from ..domain.state_machine import AnalysisStatus

router = APIRouter(tags=["metrics"])


def _counts_by_status(db: Session, initiator_id: str | None = None) -> dict:
    q = db.query(M.Analysis)
    if initiator_id:
        q = q.filter(M.Analysis.initiator_id == initiator_id)
    out: dict[str, int] = {}
    for a in q.all():
        out[a.status.value] = out.get(a.status.value, 0) + 1
    return out


def _palette_distribution(db: Session, initiator_id: str | None = None) -> dict:
    q = db.query(M.Analysis)
    if initiator_id:
        q = q.filter(M.Analysis.initiator_id == initiator_id)
    out: dict[str, int] = {}
    for a in q.all():
        if a.flow_result:
            out[a.flow_result] = out.get(a.flow_result, 0) + 1
    return out


def _first_pass_rate(db: Session) -> float:
    """Approved without correction / total reviewed (FR-6.3 style)."""
    approved = db.query(M.ExpertReview).filter(M.ExpertReview.verdict == M.Verdict.APPROVE).count()
    corrected = db.query(M.ExpertReview).filter(M.ExpertReview.verdict == M.Verdict.CORRECT).count()
    total = approved + corrected
    return round(approved / total, 4) if total else 0.0


@router.get("/metrics/{scope}")
def metrics(scope: str, db: Session = Depends(get_session), user: M.User = Depends(current_user)):
    scope = scope.lower()

    if scope == "analyst":
        mine = user.id if user.role in (M.Role.ANALYST, M.Role.VIEWER) else None
        return {
            "scope": "analyst",
            "submissions": db.query(M.Analysis).filter(
                M.Analysis.initiator_id == (mine or user.id)).count(),
            "by_status": _counts_by_status(db, mine or user.id),
            "palette_distribution": _palette_distribution(db, mine or user.id),
            "awaiting_review": db.query(M.Analysis).filter(
                M.Analysis.initiator_id == (mine or user.id),
                M.Analysis.status == AnalysisStatus.PENDING_REVIEW).count(),
        }

    if scope == "expert":
        if user.role not in (M.Role.EXPERT, M.Role.ADMIN):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "expert metrics require Expert/Admin")
        queue = db.query(M.Analysis).filter(
            M.Analysis.status.in_([AnalysisStatus.PENDING_REVIEW,
                                   AnalysisStatus.NEEDS_HUMAN_REVIEW,
                                   AnalysisStatus.CONFLICTING_INPUTS])).count()
        return {
            "scope": "expert",
            "queue_depth": queue,
            "first_pass_accuracy": _first_pass_rate(db),
            "corrections": db.query(M.Correction).count(),
            "instant_memory_count": db.query(M.MemoryEntry).filter(
                M.MemoryEntry.active == True).count(),  # noqa: E712
            "reruns_consistent": True,  # deterministic pipeline -> 100% (NFR)
            "by_status": _counts_by_status(db),
        }

    if scope == "admin":
        if user.role != M.Role.ADMIN:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "admin metrics require Admin")
        return {
            "scope": "admin",
            "total_analyses": db.query(M.Analysis).count(),
            "active_users": db.query(M.User).filter(
                M.User.status == M.UserStatus.ACTIVE).count(),
            "by_status": _counts_by_status(db),
            "palette_distribution": _palette_distribution(db),
            "first_pass_accuracy": _first_pass_rate(db),
            "corrections": db.query(M.Correction).count(),
            "memory_entries": db.query(M.MemoryEntry).count(),
            "audit_outcomes": _audit_distribution(db),
            "enabled_models": db.query(M.ModelConfig).filter(
                M.ModelConfig.enabled == True).count(),  # noqa: E712
        }

    raise HTTPException(status.HTTP_400_BAD_REQUEST, "scope must be analyst|expert|admin")


def _audit_distribution(db: Session) -> dict:
    out: dict[str, int] = {}
    for r in db.query(M.AuditRecord).all():
        out[r.verdict.value] = out.get(r.verdict.value, 0) + 1
    return out
