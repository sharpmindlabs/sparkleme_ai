"""Correction-memory regression guarantee (FR-5.3 / FR-5.4) and determinism.

The load-bearing test: after an expert correction, an immediate rerun (and every
subsequent rerun) of identical inputs returns the expert's palette via memory HIT.
"""
from __future__ import annotations

from services.api.domain import memory as memmod
from services.api.tests.conftest import auth, create_analysis


# --- unit level: deterministic embedding + cosine ---
def test_identical_bytes_embed_to_cosine_one():
    a = memmod.embed_image([b"same-bytes"], dim=64)
    b = memmod.embed_image([b"same-bytes"], dim=64)
    assert memmod.cosine(a, b) == 1.0


def test_different_bytes_are_dissimilar():
    a = memmod.embed_image([b"one"], dim=64)
    b = memmod.embed_image([b"two-different"], dim=64)
    assert memmod.cosine(a, b) < 0.99


# --- API level: the FR-5.4 regression guarantee ---
def test_correction_then_rerun_returns_expert_palette(client, analyst_token, expert_token):
    tag = b"memory-regression-case"
    r = create_analysis(client, analyst_token, hair="I Do Not Know", fitz="II", tag=tag)
    assert r.status_code == 201, r.text
    detail = r.json()
    aid = detail["id"]
    ai_palette = detail["flow_result"]
    candidate_set = detail["candidate_set"]
    assert ai_palette in candidate_set

    # Expert corrects to a DIFFERENT palette within the candidate set.
    corrected = next(p for p in candidate_set if p != ai_palette)
    rr = client.post(f"/analyses/{aid}/review",
                     json={"verdict": "CORRECT", "palette": corrected,
                           "comments": "expert override", "influence": "prefer this drape"},
                     headers=auth(expert_token))
    assert rr.status_code == 200, rr.text
    assert rr.json()["memory_written"] is True

    # Immediate rerun -> memory HIT -> corrected palette.
    for _ in range(5):
        rerun = client.post(f"/analyses/{aid}/rerun", headers=auth(expert_token))
        assert rerun.status_code == 200, rerun.text
        body = rerun.json()
        assert body["memory_lookup"] == "HIT"
        assert body["flow_result"] == corrected
        assert body["analysis"]["evidence"]["memory"]["hit"] is True


def test_determinism_same_inputs_same_result(client, analyst_token):
    tag = b"determinism-case-unique"
    r1 = create_analysis(client, analyst_token, tag=tag)
    r2 = create_analysis(client, analyst_token, tag=tag)
    assert r1.status_code == 201 and r2.status_code == 201
    d1, d2 = r1.json(), r2.json()
    assert d1["flow_result"] == d2["flow_result"]
    assert d1["confidence"] == d2["confidence"]
    assert d1["candidate_set"] == d2["candidate_set"]


def test_correction_outside_candidate_set_is_blocked(client, analyst_token, expert_token):
    # Blonde + Fitz II -> {True Spring, True Summer, Light}; correcting to Deep is blocked.
    tag = b"fr-5-5-block"
    r = create_analysis(client, analyst_token, hair="Blonde", fitz="II", tag=tag)
    assert r.status_code == 201, r.text
    aid = r.json()["id"]
    rr = client.post(f"/analyses/{aid}/review",
                     json={"verdict": "CORRECT", "palette": "Deep", "comments": "x"},
                     headers=auth(expert_token))
    assert rr.status_code == 400
    assert "candidate_set" in rr.json()["detail"]


def test_conflicting_inputs_status(client, analyst_token):
    # Blonde + Fitz VI -> empty candidate set -> CONFLICTING_INPUTS.
    r = create_analysis(client, analyst_token, hair="Blonde", fitz="VI", tag=b"conflict")
    assert r.status_code == 201, r.text
    assert r.json()["result_status"] == "CONFLICTING_INPUTS"
