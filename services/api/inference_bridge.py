"""Thin bridge to ``services/inference_engine``.

The engine is designed to be run as a module from its own directory; we add that
directory to ``sys.path`` and import its provider + parser. Default provider is
``mock`` so everything runs offline with no keys/network.

For multi-model consensus in the sandbox, each configured model produces a
*deterministic* vote derived from ``sha256(image_bytes + model_id)`` mapped into
the candidate set. The primary/first model also carries the engine's full
structured evidence (drape steps, reasoning). This is a documented sandbox
simulation of provider fan-out — swap in real provider adapters for production.
"""
from __future__ import annotations
import hashlib
import sys
import time
from pathlib import Path

from .config import get_settings, INFERENCE_ENGINE_DIR

if str(INFERENCE_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(INFERENCE_ENGINE_DIR))

# Imported from services/inference_engine/app/*
from app.providers.base import get_provider  # noqa: E402
from app.engine import load_prompt as _engine_load_prompt, parse_result  # noqa: E402


def engine_default_prompt() -> str:
    """The engine's active first-pass prompt (fallback if file missing)."""
    return _engine_load_prompt()


def run_engine(image_dicts: list[dict], prompt: str, provider_name: str | None = None):
    """Run the (mock by default) provider once and parse to an InferenceResult.

    ``image_dicts`` are {media_type, b64} entries as produced by the engine's
    ``images.load_client_images`` or by our upload handler.
    Returns (InferenceResult, latency_ms, raw_text).
    """
    s = get_settings()
    provider = get_provider(provider_name or s.inference_provider)
    user_msg = "Analyse this client's drape images and return the JSON verdict."
    t0 = time.time()
    raw = provider.complete(prompt, user_msg, image_dicts)
    latency = int((time.time() - t0) * 1000)
    result = parse_result(raw)
    return result, latency, raw


def model_vote(model_id: str, image_sha: str, candidate_set: list[str]) -> str:
    """Deterministic per-model vote within the candidate set (sandbox fan-out)."""
    if not candidate_set:
        raise ValueError("empty candidate set")
    h = hashlib.sha256(f"{model_id}|{image_sha}".encode()).hexdigest()
    idx = int(h, 16) % len(candidate_set)
    return candidate_set[idx]
