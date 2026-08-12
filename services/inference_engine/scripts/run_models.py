"""Full bake-off: run the golden set against several Azure Foundry models and
write per-model results + a comparison summary.

Usage:
  AZURE_FOUNDRY_API_KEY=... SPARKLEME_IMAGES_ROOT=/path/to/images \
  python -m scripts.run_models grok-4.3 gpt-5.6-sol gpt-5.4 gpt-5.6-terra
"""
import json, os, sys
from pathlib import Path

DEFAULT_MODELS = ["grok-4.3", "gpt-5.6-sol", "gpt-5.4", "gpt-5.6-terra"]


def main(models: list[str]) -> int:
    os.environ["SPARKLEME_PROVIDER"] = "azure_foundry"
    # import after env is set so settings pick it up
    from app.config import get_settings
    from app.batch import run_batch
    from app import config as cfgmod

    results_dir = get_settings().results_dir
    results_dir.mkdir(parents=True, exist_ok=True)
    comparison = []

    for model in models:
        os.environ["SPARKLEME_AZURE_MODEL"] = model
        cfgmod.get_settings.cache_clear()  # re-read env for this model
        print(f"\n{'='*60}\n=== {model} ===\n{'='*60}")
        def prog(i, n, cr):
            mark = {"exact": "OK ", "boundary": "~OK", "miss": "XX ",
                    "error": "ERR", "no_ground_truth": "?  "}.get(cr.match_kind, "?")
            print(f"[{i}/{n}] {mark} {cr.client_id}: {cr.predicted} vs {cr.carol_primary}")
        summary = run_batch(only_available=True, progress=prog)
        (results_dir / f"results_{model}.json").write_text(
            summary.model_dump_json(indent=2), encoding="utf-8")
        comparison.append({
            "model": model, "scored": summary.scored, "exact": summary.exact,
            "boundary": summary.boundary, "misses": summary.misses,
            "errors": summary.errors, "accuracy": summary.accuracy,
            "exact_accuracy": summary.exact_accuracy,
        })
        print(f"-> {model}: accuracy {summary.accuracy:.1%} "
              f"(exact {summary.exact_accuracy:.1%}, errors {summary.errors})")

    (results_dir / "comparison.json").write_text(
        json.dumps(comparison, indent=2), encoding="utf-8")
    print(f"\n{'='*60}\n=== COMPARISON (baseline: Carol first-pass 64%) ===\n{'='*60}")
    for c in sorted(comparison, key=lambda x: x["accuracy"], reverse=True):
        print(f"  {c['model']:<16} acc {c['accuracy']:.1%}  exact {c['exact_accuracy']:.1%}  "
              f"errors {c['errors']}")
    print(f"\nWrote per-model results + comparison.json to {results_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:] or DEFAULT_MODELS))
