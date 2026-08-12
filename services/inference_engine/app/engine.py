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


def parse_result(raw: str) -> InferenceResult:
    data = _extract_json(raw)
    steps = [DrapeStep(**s) if isinstance(s, dict) else DrapeStep(step=str(s), winner="")
             for s in data.get("steps", [])]
    return InferenceResult(
        home_season=data.get("home_season"),
        flow_result=data.get("flow_result"),
        leaning=data.get("leaning"),
        confidence=data.get("confidence", "Low"),
        steps=steps,
        final_reasoning=data.get("final_reasoning", ""),
    ).sanity_check()


def run_client(client_id: str, provider=None, prompt: str | None = None) -> tuple[InferenceResult, int, list[dict]]:
    """Returns (result, latency_ms, images). Raises on hard failure (caller handles)."""
    s = get_settings()
    provider = provider or get_provider(s.provider)
    prompt = prompt if prompt is not None else load_prompt()
    images = load_client_images(s.images_root, client_id)
    if not images:
        raise FileNotFoundError(f"no images found for client '{client_id}' under {s.images_root}")
    user_msg = "Analyse this client's five drape images and return the JSON verdict."
    t0 = time.time()
    raw = provider.complete(prompt, user_msg, images)
    latency = int((time.time() - t0) * 1000)
    result = parse_result(raw)
    return result, latency, images
