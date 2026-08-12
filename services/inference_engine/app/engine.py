"""Run inference for a single client: prompt + images -> InferenceResult."""
from __future__ import annotations
import json
import re
import time
from pathlib import Path

from .config import get_settings
from .images import load_client_images
from .providers.base import get_provider
from .schema import InferenceResult, DrapeStep

_FALLBACK_PROMPT = """You are an expert virtual colour analyst using the CAMS method.
From the client's 5 drape images (one Home-Season page + four Flow pages), decide which
ONE of these ten palettes best harmonizes with the person: True Winter, True Summer,
True Spring, True Autumn, Cool, Warm, Deep, Bright, Light, Muted.
Do not use hair colour or Fitzpatrick type. Judge only the drape images on the seven CAMS
checks (facial details, skin colour, skin consistency, jawline, eyes, focus, balance),
Eyes -> Person -> Colour. Determine the Home Season first, then the Flow within it.
Return ONLY strict JSON: {"home_season","flow_result","leaning","confidence",
"steps":[{"step","winner","criteria_cited","reasoning"}],"final_reasoning"}."""


def load_prompt() -> str:
    p: Path = get_settings().prompt_path
    if p.is_file():
        return p.read_text(encoding="utf-8")
    return _FALLBACK_PROMPT


def _extract_json(text: str) -> dict:
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        text = m.group(1)
    else:
        a, b = text.find("{"), text.rfind("}")
        if a != -1 and b != -1 and b > a:
            text = text[a:b + 1]
    return json.loads(text)


def _canon_palette(value):
    """Map a model's palette string to one of the 10 canonical names, tolerating
    extra words (e.g. 'Bright Spring' -> 'Bright', 'True Summer (Cool)' -> 'True Summer')."""
    from .palettes import PALETTES, extract_palettes
    if value in PALETTES:
        return value
    found = extract_palettes(value or "")
    return found[0] if found else value


def _canon_season(value):
    from .palettes import HOME_SEASONS
    if value in HOME_SEASONS:
        return value
    for s in HOME_SEASONS:
        if value and s.lower() in value.lower():
            return s
    return value


def parse_result(raw: str) -> InferenceResult:
    data = _extract_json(raw)
    steps = [DrapeStep(**s) if isinstance(s, dict) else DrapeStep(step=str(s), winner="")
             for s in data.get("steps", [])]
    return InferenceResult(
        home_season=_canon_season(data.get("home_season")),
        flow_result=_canon_palette(data.get("flow_result")),
        leaning=data.get("leaning"),
        confidence=data.get("confidence", "Low"),
        steps=steps,
        final_reasoning=data.get("final_reasoning", ""),
    ).sanity_check()


_METRICS_CACHE: dict | None = None


def _depth_hint(client_id: str) -> str:
    """Append the one OBJECTIVE, validated measurement — value/depth from ITA — as a
    soft constraint. Undertone (warm/cool) is NOT reliably measurable from these
    composited photos, so we deliberately do not assert it. Depth separates the
    light seasons (Spring/Summer/Light) from the deep ones (Autumn/Winter/Deep)."""
    global _METRICS_CACHE
    if _METRICS_CACHE is None:
        p = Path(__file__).resolve().parents[1] / "results" / "skin_metrics.json"
        try:
            _METRICS_CACHE = json.loads(p.read_text())
        except Exception:
            _METRICS_CACHE = {}
    d = _METRICS_CACHE.get(str(client_id))
    if not d or d.get("ita") is None:
        return ""
    ita = d["ita"]
    band = ("very light" if ita > 45 else "light" if ita > 30 else
            "medium" if ita > 18 else "deep" if ita > 5 else "very deep")
    return (f"\n\nOBJECTIVE MEASUREMENT (from pixels, undertone-neutral): the person's "
            f"skin value/depth measures **{band}** (ITA {ita:.0f}). Treat this as a strong "
            f"constraint on the VALUE axis only — a light measurement favours the lighter "
            f"palettes and a deep measurement favours the deeper palettes — but decide "
            f"warm/cool and chroma purely from the drape harmony in the images.")


def run_client(client_id: str, provider=None, prompt: str | None = None) -> tuple[InferenceResult, int, list[dict]]:
    """Returns (result, latency_ms, images). Raises on hard failure (caller handles)."""
    s = get_settings()
    provider = provider or get_provider(s.provider)
    prompt = prompt if prompt is not None else load_prompt()
    images = load_client_images(s.images_root, client_id)
    if not images:
        raise FileNotFoundError(f"no images found for client '{client_id}' under {s.images_root}")
    user_msg = "Analyse this client's five drape images and return the JSON verdict."
    # NOTE: explicit depth-band injection (_depth_hint) was tested in v3 and REGRESSED
    # accuracy (28% -> 14%): the model over-obeys the crude light/deep label and floods
    # Deep/Light. Kept in the file for reference but no longer appended to the prompt.
    t0 = time.time()
    raw = provider.complete(prompt, user_msg, images)
    latency = int((time.time() - t0) * 1000)
    result = parse_result(raw)
    return result, latency, images
