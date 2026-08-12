"""Analyses: create/run, list, detail, review, rerun (FR-2..FR-5, §11)."""
from __future__ import annotations
import base64
import hashlib
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Query
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import get_session
from ..domain import ruleouts, memory as memmod
from ..domain.palettes import SEASON_UNDERTONE, derive_home_season, is_valid_flow
from ..domain.state_machine import AnalysisStatus, assert_transition, IllegalTransition
from .. import models as M
from ..security import current_user, require_roles
from ..serializers import analysis_summary, analysis_detail
from ..schemas import ReviewRequest
from ..idempotency import get_idempotency_key, replay, store
from .. import orchestrator
from .. import inference_bridge

router = APIRouter(tags=["analyses"])
settings = get_settings()


def _image_dict_from_bytes(data: bytes, content_type: str | None) -> dict:
    media = content_type or "image/jpeg"
    return {"media_type": media, "b64": base64.b64encode(data).decode("ascii")}


def _run_and_persist(db: Session, analysis: M.Analysis, image_dicts, image_bytes_list,
                     hair, fitz, notes, initiator: M.User):
    initiator_is_expert = initiator.role in (M.Role.EXPERT, M.Role.ADMIN)
    outcome, snapshot, model_runs, consensus_dict, prompt_version = orchestrator.compute_run(
        db,
        image_dicts=image_dicts, image_bytes_list=image_bytes_list,
        hair_colour=hair, fitzpatrick=fitz, freeform_notes=notes,
        initiator_is_expert=initiator_is_expert,
    )
    audit_pv = (
        db.query(M.PromptVersion)
        .filter(M.PromptVersion.type == M.PromptType.AUDIT, M.PromptVersion.active == True)  # noqa: E712
        .first()
    )
    orchestrator.persist_run(
        db, analysis, outcome, snapshot, model_runs, consensus_dict, prompt_version,
        audit_pv.version if audit_pv else None,
    )
    return outcome


# --------------------------------------------------------------------------- create
@router.post("/analyses", status_code=status.HTTP_201_CREATED)
def create_analysis(
    image: UploadFile = File(...),
    hair_colour: str = Form(...),
    fitzpatrick: str = Form(...),
    freeform_notes: str = Form(""),
    client_label: str = Form(""),
    db: Session = Depends(get_session),
    user: M.User = Depends(require_roles(M.Role.ANALYST, M.Role.EXPERT, M.Role.ADMIN)),
    idem_key: str | None = Depends(get_idempotency_key),
):
    replayed = replay(db, idem_key, "POST /analyses")
    if replayed is not None:
        return replayed

    data = image.file.read()
    image_dicts = [_image_dict_from_bytes(data, image.content_type)]
    image_bytes_list = [data]
    image_sha = hashlib.sha256(data).hexdigest()

    analysis = M.Analysis(
        initiator_id=user.id, client_label=client_label,
        status=AnalysisStatus.DRAFT, idempotency_key=idem_key,
    )
    db.add(analysis)
    db.flush()

    # Persist image (encrypt-at-rest stubbed) + input row.
    img_path = settings.image_store / f"{analysis.id}.bin"
    img_path.write_bytes(data)
    emb = memmod.embed_image(image_bytes_list, dim=settings.embedding_dim)
    db.add(M.AnalysisInput(
        analysis_id=analysis.id, image_uri=str(img_path), image_embedding=emb,
        image_sha256=image_sha, hair_colour=hair_colour, fitzpatrick=fitzpatrick,
        freeform_notes=freeform_notes, crop_metadata={"auto_crop": "face-only (stub)"},
    ))
    # Draft -> Validating -> (Running) is modelled; we advance directly through the run.
    analysis.status = AnalysisStatus.VALIDATING
    db.flush()

    _run_and_persist(db, analysis, image_dicts, image_bytes_list,
                     hair_colour, fitzpatrick, freeform_notes, user)
    db.commit()
    db.refresh(analysis)
    detail = analysis_detail(analysis)
    store(db, idem_key, "POST /analyses", detail, analysis.id)
    db.commit()
    return detail


# --------------------------------------------------------------------------- rule preview (FR-2.5)
@router.get("/analyses/rule-preview")
def rule_preview(
    hair_colour: str = Query(...),
    fitzpatrick: str = Query(...),
    user: M.User = Depends(current_user),
):
    try:
        return ruleouts.rule_out_preview(hair_colour, fitzpatrick)
    except ruleouts.InvalidRuleInput as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))


# --------------------------------------------------------------------------- list
@router.get("/analyses")
def list_analyses(
    db: Session = Depends(get_session),
    user: M.User = Depends(current_user),
    query: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    palette: str | None = Query(None),
    initiator: str | None = Query(None),
    sort: str = Query("created_at"),
    order: str = Query("desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    q = db.query(M.Analysis)
    # Role scoping (§2): Analysts see their own; Expert/Admin see all.
    if user.role == M.Role.ANALYST:
        q = q.filter(M.Analysis.initiator_id == user.id)
    elif user.role == M.Role.VIEWER:
        q = q.filter(M.Analysis.initiator_id == user.id)

    if status_filter:
        q = q.filter(M.Analysis.status == AnalysisStatus(status_filter)) if _is_status(status_filter) \
            else q.filter(M.Analysis.result_status == status_filter)
    if palette:
        q = q.filter(M.Analysis.flow_result == palette)
    if initiator:
        q = q.filter(M.Analysis.initiator_id == initiator)
    if query:
        like = f"%{query}%"
        q = q.filter((M.Analysis.client_label.ilike(like)) | (M.Analysis.id.ilike(like)))

    total = q.count()
    sort_col = getattr(M.Analysis, sort, M.Analysis.created_at)
    q = q.order_by(sort_col.desc() if order == "desc" else sort_col.asc())
    rows = q.offset((page - 1) * page_size).limit(page_size).all()
    return {
        "total": total, "page": page, "page_size": page_size,
        "items": [analysis_summary(a) for a in rows],
    }


def _is_status(value: str) -> bool:
    try:
        AnalysisStatus(value)
        return True
    except ValueError:
        return False


# --------------------------------------------------------------------------- detail
@router.get("/analyses/{analysis_id}")
def get_analysis(
    analysis_id: str,
    db: Session = Depends(get_session),
    user: M.User = Depends(current_user),
):
    a = db.get(M.Analysis, analysis_id)
    if a is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "analysis not found")
    if user.role in (M.Role.ANALYST, M.Role.VIEWER) and a.initiator_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "not permitted to view this analysis")
    return analysis_detail(a)


# --------------------------------------------------------------------------- review (approve/correct)
@router.post("/analyses/{analysis_id}/review")
def review_analysis(
    analysis_id: str,
    body: ReviewRequest,
    db: Session = Depends(get_session),
    user: M.User = Depends(require_roles(M.Role.EXPERT, M.Role.ADMIN)),
    idem_key: str | None = Depends(get_idempotency_key),
):
    replayed = replay(db, idem_key, f"POST /analyses/{analysis_id}/review")
    if replayed is not None:
        return replayed

    a = db.get(M.Analysis, analysis_id)
    if a is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "analysis not found")

    # Expert opens the case -> ExpertReview (if it was pending/needs-review/conflicting).
    if a.status in (AnalysisStatus.PENDING_REVIEW, AnalysisStatus.NEEDS_HUMAN_REVIEW,
                    AnalysisStatus.CONFLICTING_INPUTS):
        a.status = AnalysisStatus.EXPERT_REVIEW
        db.flush()

    verdict = body.verdict.upper()
    if verdict == "APPROVE":
        if not body.comments.strip():
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "approval comments are required (FR-5.1)")
        review = M.ExpertReview(analysis_id=a.id, expert_id=user.id,
                                verdict=M.Verdict.APPROVE, comments=body.comments)
        db.add(review)
        _transition(a, AnalysisStatus.APPROVED)
        a.expert_result = a.flow_result
        db.add(M.AuditLog(actor_id=user.id, action="review.approve", target=a.id))
        db.commit()
        db.refresh(a)
        out = {"review": "APPROVE", "analysis": analysis_detail(a)}
        store(db, idem_key, f"POST /analyses/{analysis_id}/review", out, a.id)
        db.commit()
        return out

    if verdict == "CORRECT":
        palette = (body.palette or "").strip()
        # FR-5.5: correction must be within the candidate set.
        if palette not in set(a.candidate_set or []):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"corrected palette '{palette}' is outside candidate_set {a.candidate_set}; "
                "fix the inputs and run a new analysis instead (FR-5.5)",
            )
        review = M.ExpertReview(analysis_id=a.id, expert_id=user.id,
                                verdict=M.Verdict.CORRECT, comments=body.comments)
        db.add(review)
        db.flush()
        correction = M.Correction(review_id=review.id, corrected_palette=palette,
                                  prompt_influence=body.influence, reasoning=body.comments)
        db.add(correction)

        # Derive a home season for the corrected palette (prefer current).
        season = derive_home_season(palette, prefer=a.home_season)
        undertone = SEASON_UNDERTONE.get(season) if season else None

        # FR-5.3: synchronous correction-memory write (instant), effective_from = now.
        inp = a.input
        db.add(M.MemoryEntry(
            embedding_key=inp.image_embedding, input_key={"hair_colour": inp.hair_colour,
                                                          "fitzpatrick": inp.fitzpatrick},
            verified_palette=palette, home_season=season, undertone=undertone,
            expert_note=body.influence or body.comments,
            match_threshold=settings.memory_match_threshold, source_analysis_id=a.id,
            effective_from=datetime.now(timezone.utc),
        ))
        # Async training-queue enqueue is represented by a QUEUED TrainingJob stub.
        db.add(M.TrainingJob(model_id="correction-queue", method=M.TrainingMethod.SFT,
                             example_count=1, status=M.TrainingStatus.QUEUED))

        a.expert_result = palette
        _transition(a, AnalysisStatus.CORRECTED)
        db.add(M.AuditLog(actor_id=user.id, action="review.correct", target=a.id,
                          detail={"palette": palette}))
        db.commit()
        db.refresh(a)
        out = {
            "review": "CORRECT", "memory_written": True, "training_enqueued": True,
            "analysis": analysis_detail(a),
        }
        store(db, idem_key, f"POST /analyses/{analysis_id}/review", out, a.id)
        db.commit()
        return out

    raise HTTPException(status.HTTP_400_BAD_REQUEST, "verdict must be APPROVE or CORRECT")


# --------------------------------------------------------------------------- rerun (FR-5.4)
@router.post("/analyses/{analysis_id}/rerun")
def rerun_analysis(
    analysis_id: str,
    db: Session = Depends(get_session),
    user: M.User = Depends(require_roles(M.Role.EXPERT, M.Role.ADMIN)),
    idem_key: str | None = Depends(get_idempotency_key),
):
    replayed = replay(db, idem_key, f"POST /analyses/{analysis_id}/rerun")
    if replayed is not None:
        return replayed

    a = db.get(M.Analysis, analysis_id)
    if a is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "analysis not found")
    inp = a.input
    if inp is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "analysis has no stored inputs")

    # Re-read image bytes from the store to reproduce identical inputs.
    data = (settings.image_store / f"{a.id}.bin").read_bytes()
    image_dicts = [_image_dict_from_bytes(data, "image/jpeg")]

    _transition(a, AnalysisStatus.RUNNING)
    db.flush()
    outcome = _run_and_persist(db, a, image_dicts, [data],
                               inp.hair_colour, inp.fitzpatrick, inp.freeform_notes, user)
    db.add(M.AuditLog(actor_id=user.id, action="analysis.rerun", target=a.id,
                      detail={"memory_hit": outcome.memory_hit, "result": outcome.flow_result}))
    db.commit()
    db.refresh(a)
    out = {
        "rerun": True,
        "memory_lookup": "HIT" if outcome.memory_hit else "MISS",
        "result_status": outcome.result_status,
        "flow_result": outcome.flow_result,
        "analysis": analysis_detail(a),
    }
    store(db, idem_key, f"POST /analyses/{analysis_id}/rerun", out, a.id)
    db.commit()
    return out


def _transition(a: M.Analysis, dst: AnalysisStatus):
    try:
        assert_transition(a.status, dst)
    except IllegalTransition as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))
    a.status = dst
