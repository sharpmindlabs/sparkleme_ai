"""Batch runner: run the engine over the golden set and score vs Carol's column O."""
from __future__ import annotations
import json
import time
from pathlib import Path

from .config import get_settings
from .engine import run_client, load_prompt
from .providers.base import get_provider
from .images import find_client_dir
from .scoring import score_case, summarize
from .schema import CaseResult, BatchSummary


def load_goldenset() -> list[dict]:
    data = json.loads(get_settings().goldenset_path.read_text(encoding="utf-8"))
    return data.get("cases", data if isinstance(data, list) else [])


def available_client_ids() -> set[str]:
    """Client ids that actually have images present locally."""
    s = get_settings()
    ids: set[str] = set()
    if not s.images_root.exists():
        return ids
    for child in s.images_root.iterdir():
        if child.is_dir():
            ids.add(child.name.split("-")[-1])
        elif child.suffix.lower() == ".pdf":
            ids.add(child.stem.split("-")[-1])
    return ids


def run_case(case: dict, provider, prompt: str) -> CaseResult:
    cid = str(case["client_id"])
    cr = CaseResult(
        client_id=cid, test_id=case.get("test_id"),  # model set by caller
        carol_result=case.get("carol_result"),
    )
    try:
        result, latency, _ = run_client(cid, provider=provider, prompt=prompt)
        predicted = result.flow_result if result.valid else None
        match, kind, primary, accepted = score_case(predicted, case.get("carol_result"))
        cr.predicted = predicted
        cr.match, cr.match_kind = match, kind
        cr.carol_primary, cr.carol_accepted = primary, accepted
        cr.confidence = result.confidence
        cr.latency_ms = latency
        cr.result = result
        if not result.valid:
            cr.error = result.validation_error
    except Exception as e:  # keep the batch going
        _, kind, primary, accepted = score_case(None, case.get("carol_result"))
        cr.match_kind = "error"
        cr.carol_primary, cr.carol_accepted = primary, accepted
        cr.error = f"{type(e).__name__}: {e}"
    return cr


def run_batch(client_ids: list[str] | None = None, only_available: bool = True,
              progress=None) -> BatchSummary:
    s = get_settings()
    provider = get_provider(s.provider)
    model = s.model_label()
    prompt = load_prompt()

    cases = load_goldenset()
    if client_ids:
        wanted = {str(c) for c in client_ids}
        cases = [c for c in cases if str(c["client_id"]) in wanted]
    if only_available:
        have = available_client_ids()
        if have:
            cases = [c for c in cases if str(c["client_id"]) in have]

    results: list[CaseResult] = []
    for i, case in enumerate(cases):
        cr = run_case(case, provider, prompt)
        cr.model = model
        results.append(cr)
        if progress:
            progress(i + 1, len(cases), cr)

    summary = summarize(results, model=model, provider=s.provider)
    _save(summary)
    return summary


def _save(summary: BatchSummary) -> Path:
    s = get_settings()
    s.results_dir.mkdir(parents=True, exist_ok=True)
    out = s.results_dir / "latest.json"
    out.write_text(summary.model_dump_json(indent=2), encoding="utf-8")
    return out
