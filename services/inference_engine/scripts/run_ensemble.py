"""Multi-pass ensemble for chasing max accuracy on gpt-5.6.

Stacks three levers on top of the consolidated first-pass prompt:
  1. Self-consistency: run the first pass K times (temp>0 => varied) and keep every verdict.
  2. Adversarial re-audit: feed the first-pass verdict + its own reasoning back with a
     Carol-style critic prompt that specifically challenges the Summer/Cool/Muted default,
     forces reverse audits and the home-season gate checks, and returns a revised verdict.
     This automates Carol's actual second turn (her results were NOT first-pass).
  3. Majority vote across {K first passes} + {re-audit, weighted}. Ties broken by re-audit.

Usage:
  AZURE_FOUNDRY_API_KEY=... SPARKLEME_IMAGES_ROOT=./realimages \
  python -m scripts.run_ensemble --model gpt-5.6-terra --k 3 --reaudit [--workers 6]
"""
import os, sys, json, threading, collections
from concurrent.futures import ThreadPoolExecutor, as_completed

os.environ.setdefault("SPARKLEME_PROVIDER", "azure_foundry")
from app.config import get_settings
from app.engine import load_prompt, run_client, parse_result, _depth_hint, _extract_json
from app.images import load_client_images
from app.providers.azure_foundry import AzureFoundryProvider
from app.batch import load_goldenset, available_client_ids
from app.scoring import score_case
from app.palettes import extract_palettes

_lock = threading.Lock()


def canonical_palette(text):
    """Normalize a model's flow_result string to a single canonical palette."""
    if not text:
        return None
    got = extract_palettes(str(text))
    return got[0] if got else str(text).strip()


def parse_flow_tolerant(raw):
    """Extract just the final palette from a critic response, tolerant of any `steps`
    schema (the critic uses a different step shape, which crashes the strict parser)."""
    try:
        data = _extract_json(raw)
        fr = data.get("flow_result") or data.get("final") or data.get("palette")
        c = canonical_palette(fr)
        if c:
            return c
    except Exception:
        pass
    got = extract_palettes(raw)  # last resort: first canonical palette named anywhere
    return got[0] if got else None

CRITIC_SYSTEM = """You are the senior CAMS auditor doing a SECOND, independent review of a
first-pass drape analysis. The first pass is frequently wrong in one specific way and your job
is to catch it.

THE PHYSICS: in every image the face is the identical cut-out on different drape backgrounds;
the drape never re-tones the skin. "Which drape makes the skin look calmer/more even" is an
ILLUSION (simultaneous contrast). Judge only which drape's hue/value/chroma HARMONIZES with the
person's fixed colouring.

THE #1 FAILURE you must actively hunt for: the first pass over-selects Summer / Cool / Muted
(~3x too often) because grey/muted drapes make the unchanged face read as "settled". Do not let
that stand unless the cool-muted harmony is genuinely decisive.

MANDATORY checks:
- Reverse every pairwise comparison (judge B vs A as a fresh case), with NO bias to any season.
- Home-season gate: if Summer beats Winter, Cool MUST beat Winter; if Winter beats Summer, Cool
  MUST beat Summer; if Autumn beats Spring, Warm MUST beat Spring; if Spring beats Autumn, Warm
  MUST beat Autumn. If a gate fails, the claimed winner has NOT won.
- Grey-veil / luminosity audit both ways: credit genuine brightness, warmth and depth; reject
  greyness dressed up as "calm".
- Respect the objective VALUE/depth measurement provided; do not cross it.

Return ONLY the JSON verdict in the required schema (home_season, flow_result, leaning,
confidence, steps). flow_result is your FINAL palette."""


def critic_user(cid, first):
    steps = ""
    if isinstance(first, dict):
        for s in first.get("steps", [])[:8]:
            steps += f"  - {s.get('step')}: winner={s.get('winner')} | {str(s.get('reasoning',''))[:180]}\n"
        hs, fr, lean = first.get("home_season"), first.get("flow_result"), first.get("leaning")
    else:
        hs = getattr(first, "home_season", None); fr = getattr(first, "flow_result", None); lean = getattr(first, "leaning", None)
    return (f"FIRST-PASS RESULT to audit:\n  home_season={hs}  flow_result={fr}  leaning={lean}\n"
            f"first-pass step reasoning:\n{steps}\n"
            f"{_depth_hint(cid)}\n\n"
            f"Re-audit the five images independently per your instructions. Actively test whether "
            f"the first pass fell for the Summer/Cool/Muted contrast illusion. Return the final JSON verdict.")


def vote(verdicts, reaudit):
    """verdicts: list of palette strings (first passes). reaudit: palette string or None.
    Re-audit gets weight 2 (it saw the first pass and challenged it)."""
    tally = collections.Counter()
    for v in verdicts:
        if v: tally[v] += 1
    if reaudit:
        tally[reaudit] += 2
    if not tally:
        return None
    top = tally.most_common()
    best = top[0][1]
    tied = [p for p, n in top if n == best]
    if len(tied) > 1 and reaudit in tied:
        return reaudit
    return tied[0]


def process(model, provider, case, prompt, k, do_reaudit):
    cid = str(case["client_id"])
    first_passes, first_full = [], None
    for i in range(k):
        try:
            result, _, _ = run_client(cid, provider=provider, prompt=prompt)
            if result.valid:
                first_passes.append(canonical_palette(result.flow_result))
                if first_full is None:
                    first_full = result.model_dump() if hasattr(result, "model_dump") else result
        except Exception as e:
            pass
    reaudit_v = None
    if do_reaudit and first_full is not None:
        try:
            images = load_client_images(get_settings().images_root, cid)
            raw = provider.complete(CRITIC_SYSTEM, critic_user(cid, first_full), images)
            reaudit_v = parse_flow_tolerant(raw)
        except Exception:
            pass
    final = vote(first_passes, reaudit_v)
    match, kind, primary, accepted = score_case(final, case.get("carol_result"))
    with _lock:
        mk = {"exact": "OK ", "boundary": "~OK", "miss": "XX "}.get(kind, "?")
        print(f"  {mk} {cid}: first={first_passes} reaudit={reaudit_v} -> {final} vs {primary}", flush=True)
    return {"client_id": cid, "carol_primary": primary, "first_passes": first_passes,
            "reaudit": reaudit_v, "final": final, "match_kind": kind}


def main(argv):
    model, k, do_reaudit, workers = "gpt-5.6-terra", 3, False, 6
    it = iter(argv)
    for a in it:
        if a == "--model": model = next(it)
        elif a == "--k": k = int(next(it))
        elif a == "--reaudit": do_reaudit = True
        elif a == "--workers": workers = int(next(it))
    os.environ["SPARKLEME_AZURE_MODEL"] = model
    prompt = load_prompt()
    provider = AzureFoundryProvider(model=model)
    cases = [c for c in load_goldenset() if str(c["client_id"]) in available_client_ids()]
    print(f"ensemble model={model} k={k} reaudit={do_reaudit} cases={len(cases)} workers={workers}")
    rows = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(process, model, provider, c, prompt, k, do_reaudit) for c in cases]
        for f in as_completed(futs):
            rows.append(f.result())
    ex_n = sum(1 for r in rows if r["match_kind"] == "exact")
    bd = sum(1 for r in rows if r["match_kind"] == "boundary")
    n = len(rows)
    tag = f"{model}_k{k}{'_reaudit' if do_reaudit else ''}"
    out = get_settings().results_dir / f"ensemble_{tag}.json"
    out.write_text(json.dumps({"config": {"model": model, "k": k, "reaudit": do_reaudit},
                               "exact": ex_n, "boundary": bd, "n": n,
                               "exact_acc": ex_n / n, "rows": rows}, indent=2))
    print(f"\n=== {tag}: exact {ex_n}/{n} = {ex_n/n:.0%}  (+{bd} boundary = {(ex_n+bd)/n:.0%})  -> {out.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
