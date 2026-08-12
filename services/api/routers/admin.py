"""Admin console: engine config, model registry, users, correction memory,
training pipeline (FR-7, §11). All endpoints Admin-only."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db import get_session
from .. import models as M
from ..security import require_roles, hash_password
from ..schemas import (
    EngineConfigUpdate, ModelConfigCreate, ModelConfigPatch,
    UserCreate, UserPatch, TrainingJobCreate,
)
from ..serializers import model_config_out, user_out, training_job_out

router = APIRouter(tags=["admin"])

_admin = require_roles(M.Role.ADMIN)


# --------------------------------------------------------------------------- engine
@router.get("/admin/engine")
def get_engine(db: Session = Depends(get_session), user: M.User = Depends(_admin)):
    eng = db.get(M.EngineConfig, "default")
    return {"mode": eng.mode.value, "strategy": eng.strategy.value,
            "primary_model_id": eng.primary_model_id}


@router.put("/admin/engine")
def update_engine(body: EngineConfigUpdate, db: Session = Depends(get_session),
                  user: M.User = Depends(_admin)):
    eng = db.get(M.EngineConfig, "default")
    if body.mode is not None:
        try:
            eng.mode = M.EngineMode(body.mode)
        except ValueError:
            raise HTTPException(400, "mode must be single|consensus")
    if body.strategy is not None:
        try:
            eng.strategy = M.ConsensusStrategy(body.strategy)
        except ValueError:
            raise HTTPException(400, "invalid strategy")
    if body.primary_model_id is not None:
        eng.primary_model_id = body.primary_model_id
    db.add(M.AuditLog(actor_id=user.id, action="engine.update",
                      detail={"mode": eng.mode.value, "strategy": eng.strategy.value}))
    db.commit()
    return {"mode": eng.mode.value, "strategy": eng.strategy.value,
            "primary_model_id": eng.primary_model_id}


# --------------------------------------------------------------------------- models
@router.get("/admin/models")
def list_models(db: Session = Depends(get_session), user: M.User = Depends(_admin)):
    rows = db.query(M.ModelConfig).order_by(M.ModelConfig.registry_order).all()
    return [model_config_out(m) for m in rows]


@router.post("/admin/models", status_code=status.HTTP_201_CREATED)
def add_model(body: ModelConfigCreate, db: Session = Depends(get_session),
              user: M.User = Depends(_admin)):
    if db.get(M.ModelConfig, body.model_id):
        raise HTTPException(409, "model_id already exists")
    try:
        mtype = M.ModelType(body.type)
    except ValueError:
        raise HTTPException(400, "type must be COMMERCIAL|OPEN_SOURCE")
    m = M.ModelConfig(
        model_id=body.model_id, provider=body.provider, type=mtype, enabled=body.enabled,
        vote_weight=body.vote_weight, endpoint=body.endpoint, active_version=body.active_version,
        registry_order=body.registry_order, is_primary=body.is_primary,
    )
    db.add(m)
    db.add(M.AuditLog(actor_id=user.id, action="model.add", target=body.model_id))
    db.commit()
    return model_config_out(m)


@router.patch("/admin/models/{model_id}")
def patch_model(model_id: str, body: ModelConfigPatch, db: Session = Depends(get_session),
                user: M.User = Depends(_admin)):
    m = db.get(M.ModelConfig, model_id)
    if m is None:
        raise HTTPException(404, "model not found")
    for field in ("enabled", "vote_weight", "endpoint", "active_version",
                  "registry_order", "is_primary"):
        val = getattr(body, field)
        if val is not None:
            setattr(m, field, val)
    db.add(M.AuditLog(actor_id=user.id, action="model.patch", target=model_id))
    db.commit()
    return model_config_out(m)


# --------------------------------------------------------------------------- users
@router.get("/admin/users")
def list_users(db: Session = Depends(get_session), user: M.User = Depends(_admin)):
    return [user_out(u) for u in db.query(M.User).order_by(M.User.created_at).all()]


@router.post("/admin/users", status_code=status.HTTP_201_CREATED)
def create_user(body: UserCreate, db: Session = Depends(get_session),
                user: M.User = Depends(_admin)):
    email = body.email.lower().strip()
    if db.query(M.User).filter(M.User.email == email).first():
        raise HTTPException(409, "email already registered")
    try:
        role = M.Role(body.role)
    except ValueError:
        raise HTTPException(400, "invalid role")
    u = M.User(name=body.name, email=email, password_hash=hash_password(body.password),
               role=role, status=M.UserStatus.ACTIVE)
    db.add(u)
    db.add(M.AuditLog(actor_id=user.id, action="user.create", target=email))
    db.commit()
    return user_out(u)


@router.patch("/admin/users/{user_id}")
def patch_user(user_id: str, body: UserPatch, db: Session = Depends(get_session),
               user: M.User = Depends(_admin)):
    u = db.get(M.User, user_id)
    if u is None:
        raise HTTPException(404, "user not found")
    if body.role is not None:
        try:
            u.role = M.Role(body.role)
        except ValueError:
            raise HTTPException(400, "invalid role")
    if body.status is not None:
        try:
            u.status = M.UserStatus(body.status)
        except ValueError:
            raise HTTPException(400, "invalid status")
    db.add(M.AuditLog(actor_id=user.id, action="user.patch", target=user_id,
                      detail={"role": body.role, "status": body.status}))
    db.commit()
    return user_out(u)


# --------------------------------------------------------------------------- memory
@router.get("/admin/memory")
def list_memory(db: Session = Depends(get_session), user: M.User = Depends(_admin)):
    rows = db.query(M.MemoryEntry).order_by(M.MemoryEntry.effective_from.desc()).all()
    return [{
        "id": e.id, "verified_palette": e.verified_palette, "home_season": e.home_season,
        "undertone": e.undertone, "input_key": e.input_key, "expert_note": e.expert_note,
        "match_threshold": e.match_threshold, "active": e.active,
        "source_analysis_id": e.source_analysis_id,
        "effective_from": e.effective_from.isoformat(),
    } for e in rows]


@router.delete("/admin/memory/{entry_id}")
def expire_memory(entry_id: str, db: Session = Depends(get_session),
                  user: M.User = Depends(_admin)):
    e = db.get(M.MemoryEntry, entry_id)
    if e is None:
        raise HTTPException(404, "memory entry not found")
    db.delete(e)
    db.add(M.AuditLog(actor_id=user.id, action="memory.expire", target=entry_id))
    db.commit()
    return {"deleted": entry_id}


# --------------------------------------------------------------------------- training
@router.get("/admin/training/jobs")
def list_training_jobs(db: Session = Depends(get_session), user: M.User = Depends(_admin)):
    rows = db.query(M.TrainingJob).order_by(M.TrainingJob.created_at.desc()).all()
    return [training_job_out(j) for j in rows]


@router.post("/admin/training/jobs", status_code=status.HTTP_201_CREATED)
def create_training_job(body: TrainingJobCreate, db: Session = Depends(get_session),
                        user: M.User = Depends(_admin)):
    try:
        method = M.TrainingMethod(body.method)
    except ValueError:
        raise HTTPException(400, "invalid method")
    # STUB: no real training. Simulate a golden-set evaluation result deterministically.
    corrections = db.query(M.Correction).count()
    job = M.TrainingJob(
        model_id=body.model_id, method=method, example_count=corrections,
        status=M.TrainingStatus.PASSED,
        golden_set_result={"note": "stubbed evaluation", "agreement": 0.96,
                           "candidate_set_breaches": 0, "examples": corrections},
    )
    db.add(job)
    db.add(M.AuditLog(actor_id=user.id, action="training.trigger", target=body.model_id))
    db.commit()
    return training_job_out(job)
