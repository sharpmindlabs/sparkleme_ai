"""Parallel bake-off: every (model, client) combo run concurrently against Azure.
Writes per-model results + comparison.json. Much faster than the sequential runner.

Usage:
  AZURE_FOUNDRY_API_KEY=... SPARKLEME_IMAGES_ROOT=./realimages \
  python -m scripts.run_all_parallel [--workers 8] [model ...]
"""
import os, sys, json, time, threading
from concurrent.futures import ThreadPoolExecutor, as_completed

os.environ.setdefault("SPARKLEME_PROVIDER", "azure_foundry")
from app.config import get_settings
from app.engine import load_prompt, run_client
from app.providers.azure_foundry import AzureFoundryProvider
from app.batch import load_goldenset, available_client_ids
from app.scoring import score_case, summarize
from app.schema import CaseResult

DEFAULT_MODELS = ["grok-4.3", "gpt-5.6-sol", "gpt-5.4", "gpt-5.6-terra"]
_print_lock = threading.Lock()


def one(model, provider, case, prompt):
    cid = str(case["client_id"])
    cr = CaseResult(client_id=cid, test_id=case.get("test_id"),
                    model=model, carol_result=case.get("carol_result"))
    try:
        result, latency, _ = run_client(cid, provider=provider, prompt=prompt)
        predicted = result.flow_result if result.valid else None
        match, kind, primary, accepted = score_case(predicted, case.get("carol_result"))
        cr.predicted, cr.match, cr.match_kind = predicted, match, kind
        cr.carol_primary, cr.carol_accepted = primary, accepted
        cr.confidence, cr.latency_ms, cr.result = result.confidence, latency, result
        if not result.valid:
            cr.error = result.validation_error
    except Exception as e:
        _, kind, primary, accepted = score_case(None, case.get("carol_result"))
        cr.match_kind, cr.carol_primary, cr.carol_accepted = "error", primary, accepted
        cr.error = f"{type(e).__name__}: {e}"
    with _print_lock:
        mk = {"exact": "OK ", "boundary": "~OK", "miss": "XX ", "error": "ERR"}.get(cr.match_kind, "?")
        print(f"  {mk} {model:<14} {cid}: {cr.predicted} vs {cr.carol_primary}", flush=True)
    return cr


def main(argv):
    workers = 8
    models = []
    it = iter(argv)
    for a in it:
        if a == "--workers":
            workers = int(next(it))
        else:
            models.append(a)
    models = models or DEFAULT_MODELS

    s = get_settings()
    prompt = load_prompt()
    cases = [c for c in load_goldenset() if str(c["client_id"]) in available_client_ids()]
    providers = {m: AzureFoundryProvider(model=m) for m in models}
    print(f"models={models} cases={len(cases)} workers={workers}", flush=True)

    t0 = time.time()
    results = {m: [] for m in models}
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(one, m, providers[m], c, prompt) for m in models for c in cases]
        for f in as_completed(futs):
            cr = f.result()
            results[cr.model].append(cr)

    s.results_dir.mkdir(parents=True, exist_ok=True)
    comparison = []
    for m in models:
        summary = summarize(results[m], model=m, provider="azure_foundry")
        (s.results_dir / f"results_{m}.json").write_text(summary.model_dump_json(indent=2))
        comparison.append({"model": m, "scored": summary.scored, "exact": summary.exact,
                           "boundary": summary.boundary, "misses": summary.misses,
                           "errors": summary.errors, "accuracy": summary.accuracy,
                           "exact_accuracy": summary.exact_accuracy})
    (s.results_dir / "comparison.json").write_text(json.dumps(comparison, indent=2))

    print(f"\n=== COMPARISON ({len(cases)} cases · {time.time()-t0:.0f}s · baseline Carol 64%) ===")
    for c in sorted(comparison, key=lambda x: x["accuracy"], reverse=True):
        print(f"  {c['model']:<16} acc {c['accuracy']:.1%}  exact {c['exact_accuracy']:.1%}  "
              f"boundary {c['boundary']}  errors {c['errors']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
