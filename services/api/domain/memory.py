"""Correction memory — the instant regression-guarantee layer (FR-5.3 / FR-5.4).

Sandbox substitution for pgvector: image embedding is a deterministic feature
vector derived from the image bytes (not a learned embedding), and cosine
similarity is computed in numpy. A memory lookup is synchronous on every run;
a HIT (cosine ≥ threshold *and* matching hair+fitz input key) short-circuits the
pipeline to the expert-verified palette.
"""
from __future__ import annotations
import hashlib
import numpy as np


def embed_image(image_bytes_list: list[bytes], dim: int = 64) -> list[float]:
    """Deterministic pseudo-embedding: hash the image bytes into a fixed-length
    L2-normalised float vector. Identical bytes -> identical vector (cosine 1.0)."""
    h = hashlib.sha256()
    for b in image_bytes_list:
        h.update(b)
        h.update(b"\x00")
    seed = h.digest()
    # Expand the 32-byte digest deterministically to `dim` floats.
    raw = bytearray()
    counter = 0
    while len(raw) < dim * 4:
        raw += hashlib.sha256(seed + counter.to_bytes(4, "big")).digest()
        counter += 1
    arr = np.frombuffer(bytes(raw[: dim * 4]), dtype=np.uint32).astype(np.float64)
    arr = arr / np.iinfo(np.uint32).max  # -> [0,1]
    arr = arr - arr.mean()               # centre so vectors are discriminative
    norm = np.linalg.norm(arr)
    if norm == 0:
        return arr.tolist()
    return (arr / norm).tolist()


def cosine(a: list[float], b: list[float]) -> float:
    va, vb = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    na, nb = np.linalg.norm(va), np.linalg.norm(vb)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(va, vb) / (na * nb))


def input_key(hair_colour: str, fitzpatrick: str) -> dict:
    return {"hair_colour": hair_colour, "fitzpatrick": fitzpatrick}


def matches_input_key(a: dict, b: dict) -> bool:
    return a.get("hair_colour") == b.get("hair_colour") and a.get("fitzpatrick") == b.get("fitzpatrick")


def best_match(
    query_embedding: list[float],
    query_key: dict,
    entries: list,
    threshold: float,
):
    """Return (entry, score) of the best HIT, or (None, best_score).

    ``entries`` is a list of objects with ``.embedding_key`` (list[float]),
    ``.input_key`` (dict) and ``.effective_from``. A HIT requires the hair+fitz
    input key to match AND cosine ≥ threshold. Newest effective_from wins ties.
    """
    best = None
    best_score = -1.0
    for e in entries:
        if not matches_input_key(query_key, e.input_key):
            continue
        score = cosine(query_embedding, e.embedding_key)
        if score < threshold:
            continue
        if score > best_score or (
            score == best_score and best is not None
            and e.effective_from > best.effective_from
        ):
            best = e
            best_score = score
    return best, best_score
