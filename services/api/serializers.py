"""ORM -> dict serialization + output-contract assembly (§5.5)."""
from __future__ import annotations

from . import models as M


def analysis_summary(a: M.Analysis) -> dict:
    return {
        "id": a.id,
        "client_label": a.client_label,
        "initiator_id": a.initiator_id,
        "status": a.status.value,
        "result_status": a.result_status,
        "undertone": a.undertone,
        "home_season": a.home_season,
        "flow_result": a.flow_result,
        "ai_result": a.ai_result,
        "expert_result": a.expert_result,
        "confidence": a.confidence,
        "memory_hit": a.memory_hit,
        "prompt_version": a.prompt_version,
        "created_at": a.created_at.isoformat(),
    }


def output_contract(a: M.Analysis) -> dict:
    """The §5.5 output-contract JSON for this analysis."""
    return {
        "status": a.result_status,
        "undertone": a.undertone,
        "home_season": a.home_season,
        "flow_result": a.flow_result,
        "confidence": a.confidence,
        "candidate_set": a.candidate_set,
        "evidence": a.evidence,
        "model_votes": a.model_votes,
        "prompt_version": a.prompt_version,
        "engine": {
            "mode": a.engine_config_snapshot.get("mode") if a.engine_config_snapshot else None,
            "strategy": a.engine_config_snapshot.get("strategy") if a.engine_config_snapshot else None,
        },
    }


def analysis_detail(a: M.Analysis) -> dict:
    d = analysis_summary(a)
    inp = a.input
    d.update({
        "candidate_set": a.candidate_set or [],
        "evidence": a.evidence or {},
        "model_votes": a.model_votes or [],
        "engine_config_snapshot": a.engine_config_snapshot or {},
        "inputs": {
            "hair_colour": inp.hair_colour if inp else None,
            "fitzpatrick": inp.fitzpatrick if inp else None,
            "freeform_notes": inp.freeform_notes if inp else None,
            "image_sha256": inp.image_sha256 if inp else None,
            "crop_metadata": inp.crop_metadata if inp else {},
        },
        "output_contract": output_contract(a),
    })
    return d


def prompt_out(p: M.PromptVersion, include_body: bool = False) -> dict:
    out = {
        "version": p.version,
        "type": p.type.value,
        "author": p.author,
        "change_note": p.change_note,
        "active": p.active,
        "created_at": p.created_at.isoformat(),
    }
    if include_body:
        out["body"] = p.body
    return out


def model_config_out(m: M.ModelConfig) -> dict:
    return {
        "model_id": m.model_id,
        "provider": m.provider,
        "type": m.type.value,
        "enabled": m.enabled,
        "vote_weight": m.vote_weight,
        "endpoint": m.endpoint,
        "active_version": m.active_version,
        "registry_order": m.registry_order,
        "is_primary": m.is_primary,
    }


def user_out(u: M.User) -> dict:
    return {
        "id": u.id,
        "name": u.name,
        "email": u.email,
        "role": u.role.value,
        "status": u.status.value,
    }


def training_job_out(j: M.TrainingJob) -> dict:
    return {
        "id": j.id,
        "model_id": j.model_id,
        "method": j.method.value,
        "example_count": j.example_count,
        "status": j.status.value,
        "golden_set_result": j.golden_set_result or {},
        "created_at": j.created_at.isoformat(),
    }
