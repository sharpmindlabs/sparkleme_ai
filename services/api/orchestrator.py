"""Analysis orchestration (§6 flowchart, §7.1 sequence).

Given inputs (image bytes + hair + fitzpatrick + notes) this computes the
candidate set, checks correction memory, runs inference via the inference engine
(mock by default), applies multi-model consensus, validates the output contract,
runs a lightweight audit, and persists the full evidence trail.

Everything is deterministic: identical inputs -> identical output on the 1st and
nth run (§1.2.5, FR-2.7). Correction-memory HITs short-circuit synchronously.
"""
from __future__ import annotations
import hashlib
from dataclasses import dataclass

from sqlalchemy.orm import Session

from .config import get_settings
from .domain import ruleouts, contract, memory as memmod
from .domain.consensus import ModelVote, weighted_majority
from .domain.palettes import SEASON_UNDERTONE, derive_home_season
from .domain.state_machine import AnalysisStatus, landing_status
from . import models as M
from . import inference_bridge


@dataclass
class RunOutcome:
    result_status: str
    lifecycle_status: AnalysisStatus
    undertone: str | None = None
    home_season: str | None = None
    flow_result: str | None = None
    confidence: str | None = None
    candidate_set: list[str] | None = None
    evidence: dict | None = None
    model_votes: list[dict] | None = None
    memory_hit: bool = False


def _confidence_from_margin(winner_w: float, total_w: float) -> str:
    if total_w <= 0:
        return "Low"
    frac = winner_w / total_w
    if frac >= 0.66:
        return "High"
    if frac >= 0.45:
        return "Medium"
    return "Low"


def _engine_snapshot(db: Session) -> dict:
    """Freeze engine mode/strategy/models per analysis (FR-7.1, reproducibility)."""
    eng = db.get(M.EngineConfig, "default")
    enabled = (
        db.query(M.ModelConfig)
        .filter(M.ModelConfig.enabled == True)  # noqa: E712
        .order_by(M.ModelConfig.registry_order)
        .all()
    )
    if eng.mode == M.EngineMode.SINGLE:
        primary = eng.primary_model_id
        models = [m for m in enabled if m.model_id == primary] or enabled[:1]
    else:
        models = enabled
    s = get_settings()
    return {
        "mode": eng.mode.value,
        "strategy": eng.strategy.value,
        "provider": s.inference_provider,
        "seed": s.inference_seed,
        "temperature": s.inference_temperature,
        "models": [
            {"model_id": m.model_id, "weight": m.vote_weight, "order": m.registry_order,
             "provider": m.provider, "active_version": m.active_version}
            for m in models
        ],
    }


def _active_analysis_prompt(db: Session) -> tuple[str | None, str]:
    pv = (
        db.query(M.PromptVersion)
        .filter(M.PromptVersion.type == M.PromptType.ANALYSIS, M.PromptVersion.active == True)  # noqa: E712
        .first()
    )
    if pv:
        return pv.version, pv.body
    return None, inference_bridge.engine_default_prompt()


def compute_run(
    db: Session,
    *,
    image_dicts: list[dict],
    image_bytes_list: list[bytes],
    hair_colour: str,
    fitzpatrick: str,
    freeform_notes: str,
    initiator_is_expert: bool,
) -> tuple[RunOutcome, dict, list[M.ModelRun], dict, str | None]:
    """Pure-ish computation of a run. Returns
    (outcome, engine_snapshot, model_run_rows, consensus_dict, prompt_version).
    ModelRun rows are unattached (caller associates + persists)."""
    settings = get_settings()

    # ---- input validation (INVALID_INPUT) ----
    if hair_colour not in ruleouts.HAIR_VALUES or fitzpatrick not in ruleouts.FITZPATRICK_VALUES:
        return (
            RunOutcome(
                result_status=contract.STATUS_INVALID_INPUT,
                lifecycle_status=AnalysisStatus.INVALID,
                candidate_set=[],
                evidence={"error": "hair/fitzpatrick not a canonical value"},
            ),
            {}, [], {}, None,
        )
    if not image_dicts:
        return (
            RunOutcome(
                result_status=contract.STATUS_INVALID_INPUT,
                lifecycle_status=AnalysisStatus.INVALID,
                candidate_set=[],
                evidence={"error": "no image provided / face not detected"},
            ),
            {}, [], {}, None,
        )

    # ---- deterministic rule-outs (§5.1/§5.2) ----
    cset = ruleouts.candidate_set(hair_colour, fitzpatrick)
    if not cset:
        return (
            RunOutcome(
                result_status=contract.STATUS_CONFLICTING_INPUTS,
                lifecycle_status=AnalysisStatus.CONFLICTING_INPUTS,
                candidate_set=[],
                evidence={
                    "b_hair": f"{hair_colour}: L1 {ruleouts.level1_candidates(hair_colour)}",
                    "level2": ruleouts.level2_candidates(fitzpatrick),
                    "reason": "empty candidate set (Level 1 ∩ Level 2)",
                },
            ),
            {}, [], {}, None,
        )

    snapshot = _engine_snapshot(db)
    prompt_version, prompt_body = _active_analysis_prompt(db)
    image_sha = hashlib.sha256(b"".join(image_bytes_list)).hexdigest()
    query_emb = memmod.embed_image(image_bytes_list, dim=settings.embedding_dim)
    query_key = memmod.input_key(hair_colour, fitzpatrick)

    # ---- correction memory lookup (synchronous, every run — FR-5.4) ----
    entries = (
        db.query(M.MemoryEntry)
        .filter(M.MemoryEntry.active == True)  # noqa: E712
        .all()
    )
    hit, score = memmod.best_match(query_emb, query_key, entries, settings.memory_match_threshold)
    if hit is not None:
        palette = hit.verified_palette
        season = hit.home_season or derive_home_season(palette)
        undertone = hit.undertone or (SEASON_UNDERTONE.get(season) if season else None)
        evidence = {
            "a_eyes": "hypothesis only",
            "b_hair": f"{hair_colour} -> {ruleouts.level1_candidates(hair_colour)}",
            "c_skin": "expert-verified via correction memory",
            "d_drape_steps": [],
            "memory": {
                "hit": True, "score": round(score, 4),
                "verified_palette": palette,
                "expert_note": hit.expert_note,
                "effective_from": hit.effective_from.isoformat(),
            },
        }
        outcome = RunOutcome(
            result_status=contract.STATUS_OK,
            lifecycle_status=landing_status(contract.STATUS_OK, initiator_is_expert),
            undertone=undertone,
            home_season=season,
            flow_result=palette,
            confidence="High",
            candidate_set=cset,
            evidence=evidence,
            model_votes=[],
            memory_hit=True,
        )
        return outcome, snapshot, [], {"strategy": "memory_override", "final_palette": palette,
                                       "vote_weights": {}}, prompt_version

    # ---- inference (mock provider by default) + consensus ----
    eng_result, latency, raw_text = inference_bridge.run_engine(image_dicts, prompt_body)

    votes: list[ModelVote] = []
    model_runs: list[M.ModelRun] = []
    model_votes_payload: list[dict] = []
    for m in snapshot["models"]:
        v = inference_bridge.model_vote(m["model_id"], image_sha, cset)
        accepted = v in set(cset)
        votes.append(ModelVote(model_id=m["model_id"], vote=v, weight=m["weight"], order=m["order"]))
        mr = M.ModelRun(
            model_id=m["model_id"], vote=v,
            raw_response={"engine_raw": raw_text, "vote": v},
            latency_ms=latency, cost=0.0, seed=settings.inference_seed, accepted=accepted,
        )
        model_runs.append(mr)
        model_votes_payload.append({"model": m["model_id"], "vote": v, "raw": v})

    outcome_consensus = weighted_majority(votes, cset, strategy=snapshot["strategy"])
    final = outcome_consensus.final_palette
    consensus_dict = {
        "strategy": outcome_consensus.strategy,
        "final_palette": final,
        "vote_weights": outcome_consensus.vote_weights,
        "discarded": outcome_consensus.discarded_votes,
    }

    if final is None:
        # No winner (e.g. unanimity strategy with disagreement) -> human review.
        outcome = RunOutcome(
            result_status=contract.STATUS_NEEDS_HUMAN_REVIEW,
            lifecycle_status=AnalysisStatus.NEEDS_HUMAN_REVIEW,
            candidate_set=cset,
            evidence={"reason": "consensus produced no winner", "tally": outcome_consensus.tally},
            model_votes=model_votes_payload,
        )
        return outcome, snapshot, model_runs, consensus_dict, prompt_version

    season = derive_home_season(final, prefer=eng_result.home_season)
    undertone = SEASON_UNDERTONE.get(season) if season else None
    total_w = sum(outcome_consensus.vote_weights.values())
    winner_w = outcome_consensus.vote_weights.get(final, 0.0)
    confidence = _confidence_from_margin(winner_w, total_w)

    # ---- output-contract hard constraints (§5.5) ----
    check = contract.validate_output_contract(
        undertone=undertone, home_season=season, flow_result=final, candidate_set=cset,
    )
    if not check.ok:
        outcome = RunOutcome(
            result_status=contract.STATUS_NEEDS_HUMAN_REVIEW,
            lifecycle_status=AnalysisStatus.NEEDS_HUMAN_REVIEW,
            undertone=undertone, home_season=season, flow_result=final,
            confidence=confidence, candidate_set=cset,
            evidence={"contract_violations": check.violations},
            model_votes=model_votes_payload,
        )
        return outcome, snapshot, model_runs, consensus_dict, prompt_version

    drape_steps = [
        {"step": i + 1, "winner": s.winner, "criteria_cited": s.criteria_cited}
        for i, s in enumerate(eng_result.steps)
    ]
    evidence = {
        "a_eyes": "hypothesis only",
        "b_hair": f"{hair_colour} -> remaining {ruleouts.level1_candidates(hair_colour)}",
        "c_skin": eng_result.final_reasoning or "observed characteristics vs palette profile",
        "d_drape_steps": drape_steps,
    }
    outcome = RunOutcome(
        result_status=contract.STATUS_OK,
        lifecycle_status=landing_status(contract.STATUS_OK, initiator_is_expert),
        undertone=undertone, home_season=season, flow_result=final,
        confidence=confidence, candidate_set=cset, evidence=evidence,
        model_votes=model_votes_payload, memory_hit=False,
    )
    return outcome, snapshot, model_runs, consensus_dict, prompt_version


def _audit(result_status: str) -> tuple[M.AuditVerdict, list[str]]:
    """Lightweight auditor pass (checks 1–7 are stubbed to the contract result)."""
    if result_status == contract.STATUS_OK:
        return M.AuditVerdict.APPROVE, []
    if result_status == contract.STATUS_NEEDS_HUMAN_REVIEW:
        return M.AuditVerdict.REJECT, ["contract/coherence check failed"]
    return M.AuditVerdict.REVISE, [result_status]


def persist_run(
    db: Session,
    analysis: M.Analysis,
    outcome: RunOutcome,
    snapshot: dict,
    model_runs: list[M.ModelRun],
    consensus_dict: dict,
    prompt_version: str | None,
    audit_prompt_version: str | None,
) -> None:
    """Attach a computed run to an Analysis row and persist all evidence."""
    analysis.result_status = outcome.result_status
    analysis.status = outcome.lifecycle_status
    analysis.undertone = outcome.undertone
    analysis.home_season = outcome.home_season
    analysis.flow_result = outcome.flow_result
    analysis.confidence = outcome.confidence
    analysis.candidate_set = outcome.candidate_set or []
    analysis.evidence = outcome.evidence or {}
    analysis.model_votes = outcome.model_votes or []
    analysis.prompt_version = prompt_version
    analysis.engine_config_snapshot = snapshot
    analysis.memory_hit = outcome.memory_hit
    if outcome.result_status == contract.STATUS_OK and not analysis.ai_result:
        # Record the original AI result once (pre-correction) for metrics.
        analysis.ai_result = outcome.flow_result

    # Replace prior model runs / consensus / audits on rerun.
    for mr in list(analysis.model_runs):
        db.delete(mr)
    if analysis.consensus:
        db.delete(analysis.consensus)
    db.flush()

    for mr in model_runs:
        mr.analysis_id = analysis.id
        db.add(mr)

    if consensus_dict:
        db.add(M.ConsensusResult(
            analysis_id=analysis.id,
            strategy=consensus_dict.get("strategy", ""),
            vote_weights=consensus_dict.get("vote_weights", {}),
            final_palette=consensus_dict.get("final_palette"),
        ))

    verdict, failed = _audit(outcome.result_status)
    db.add(M.AuditRecord(
        analysis_id=analysis.id, verdict=verdict, failed_checks=failed,
        audit_prompt_version=audit_prompt_version,
    ))
    db.flush()
