"""RBAC enforcement from the §2 matrix (acceptance criteria #6, #7)."""
from __future__ import annotations

from services.api.tests.conftest import auth, create_analysis


def test_analyst_cannot_review(client, analyst_token):
    r = create_analysis(client, analyst_token, tag=b"rbac-review")
    aid = r.json()["id"]
    rr = client.post(f"/analyses/{aid}/review",
                     json={"verdict": "APPROVE", "comments": "ok"},
                     headers=auth(analyst_token))
    assert rr.status_code == 403


def test_analyst_cannot_rerun(client, analyst_token):
    r = create_analysis(client, analyst_token, tag=b"rbac-rerun")
    aid = r.json()["id"]
    rr = client.post(f"/analyses/{aid}/rerun", headers=auth(analyst_token))
    assert rr.status_code == 403


def test_analyst_cannot_manage_prompts(client, analyst_token):
    r = client.post("/prompts/ANALYSIS/versions",
                    json={"body": "hacked", "change_note": "n"},
                    headers=auth(analyst_token))
    assert r.status_code == 403


def test_analyst_cannot_access_admin_engine(client, analyst_token):
    assert client.get("/admin/engine", headers=auth(analyst_token)).status_code == 403


def test_expert_cannot_access_model_config(client, expert_token):
    # Model configuration is Admin-only (§2).
    assert client.get("/admin/models", headers=auth(expert_token)).status_code == 403
    assert client.get("/admin/users", headers=auth(expert_token)).status_code == 403


def test_expert_can_review(client, analyst_token, expert_token):
    r = create_analysis(client, analyst_token, tag=b"rbac-expert-ok")
    aid = r.json()["id"]
    rr = client.post(f"/analyses/{aid}/review",
                     json={"verdict": "APPROVE", "comments": "looks correct"},
                     headers=auth(expert_token))
    assert rr.status_code == 200
    assert rr.json()["analysis"]["status"] == "Approved"


def test_admin_can_change_engine_mode(client, admin_token):
    r = client.put("/admin/engine", json={"mode": "single", "primary_model_id": "mock-a"},
                   headers=auth(admin_token))
    assert r.status_code == 200 and r.json()["mode"] == "single"
    # restore
    client.put("/admin/engine", json={"mode": "consensus"}, headers=auth(admin_token))


def test_approval_requires_comments(client, analyst_token, expert_token):
    r = create_analysis(client, analyst_token, tag=b"rbac-approve-nocomment")
    aid = r.json()["id"]
    rr = client.post(f"/analyses/{aid}/review",
                     json={"verdict": "APPROVE", "comments": ""},
                     headers=auth(expert_token))
    assert rr.status_code == 400


def test_unauthenticated_blocked(client):
    assert client.get("/analyses").status_code == 401


def test_idempotency_replay(client, analyst_token):
    r1 = create_analysis(client, analyst_token, tag=b"idem", idem="key-123")
    r2 = create_analysis(client, analyst_token, tag=b"idem-different-bytes", idem="key-123")
    # Same Idempotency-Key replays the first response despite different payload.
    assert r1.json()["id"] == r2.json()["id"]
