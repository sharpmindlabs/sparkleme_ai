"""Prompt registry (FR-6, §7.3). Immutable versions; one active per type."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ..db import get_session
from .. import models as M
from ..security import require_roles, current_user
from ..schemas import PromptCreate, PromptActivate
from ..serializers import prompt_out

router = APIRouter(tags=["prompts"])


def _ptype(t: str) -> M.PromptType:
    try:
        return M.PromptType(t.upper())
    except ValueError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "type must be ANALYSIS or AUDIT")


def _next_version(db: Session, ptype: M.PromptType) -> str:
    n = db.query(M.PromptVersion).filter(M.PromptVersion.type == ptype).count()
    return f"v{n + 1}"


@router.get("/prompts/{type}/versions")
def list_versions(
    type: str,
    include_body: bool = Query(False),
    db: Session = Depends(get_session),
    user: M.User = Depends(current_user),
):
    ptype = _ptype(type)
    rows = (
        db.query(M.PromptVersion)
        .filter(M.PromptVersion.type == ptype)
        .order_by(M.PromptVersion.created_at.desc())
        .all()
    )
    return [prompt_out(p, include_body=include_body) for p in rows]


@router.post("/prompts/{type}/versions", status_code=status.HTTP_201_CREATED)
def create_version(
    type: str,
    body: PromptCreate,
    db: Session = Depends(get_session),
    user: M.User = Depends(require_roles(M.Role.EXPERT, M.Role.ADMIN)),
):
    ptype = _ptype(type)
    version = _next_version(db, ptype)
    pv = M.PromptVersion(
        version=version, type=ptype, body=body.body, author=user.name,
        change_note=body.change_note, active=False,
    )
    db.add(pv)
    db.add(M.AuditLog(actor_id=user.id, action="prompt.create",
                      target=f"{ptype.value}:{version}"))
    db.commit()
    return prompt_out(pv, include_body=True)


@router.put("/prompts/{type}/active")
def activate_version(
    type: str,
    body: PromptActivate,
    db: Session = Depends(get_session),
    user: M.User = Depends(require_roles(M.Role.EXPERT, M.Role.ADMIN)),
):
    ptype = _ptype(type)
    target = (
        db.query(M.PromptVersion)
        .filter(M.PromptVersion.type == ptype, M.PromptVersion.version == body.version)
        .first()
    )
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "version not found")
    # Exactly one active per type (FR-6.2).
    for p in db.query(M.PromptVersion).filter(M.PromptVersion.type == ptype).all():
        p.active = (p.version == body.version)
    db.add(M.AuditLog(actor_id=user.id, action="prompt.activate",
                      target=f"{ptype.value}:{body.version}"))
    db.commit()
    return {"type": ptype.value, "active": body.version}
