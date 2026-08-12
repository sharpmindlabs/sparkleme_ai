"""Seed the SparkleMe platform database.

Creates admin/expert/analyst users, loads prompt v1 (ANALYSIS + AUDIT), seeds the
model registry + engine config, and imports a few golden-set cases as sample
analyses (using the inference-engine fixture images) so the UI has data.

Run:  python -m services.api.seed
"""
from __future__ import annotations
import base64
import hashlib
import json
from pathlib import Path

from .config import get_settings, REPO_ROOT, INFERENCE_ENGINE_DIR
from .db import SessionLocal, init_db
from . import models as M
from .security import hash_password
from .domain import memory as memmod
from .domain.state_machine import AnalysisStatus
from . import orchestrator, inference_bridge  # inference_bridge puts engine on sys.path

SETTINGS = get_settings()

# Documented seeded credentials (dev only).
SEED_USERS = [
    {"name": "Ada Admin",    "email": "admin@sparkleme.dev",   "password": "admin123",   "role": M.Role.ADMIN},
    {"name": "Erin Expert",  "email": "expert@sparkleme.dev",  "password": "expert123",  "role": M.Role.EXPERT},
    {"name": "Alan Analyst", "email": "analyst@sparkleme.dev", "password": "analyst123", "role": M.Role.ANALYST},
]

SEED_MODELS = [
    {"model_id": "mock-a", "provider": "mock", "type": M.ModelType.OPEN_SOURCE,
     "vote_weight": 1.0, "registry_order": 0, "is_primary": True},
    {"model_id": "mock-b", "provider": "mock", "type": M.ModelType.OPEN_SOURCE,
     "vote_weight": 0.8, "registry_order": 1},
    {"model_id": "mock-c", "provider": "mock", "type": M.ModelType.COMMERCIAL,
     "vote_weight": 0.6, "registry_order": 2},
]

ANALYSIS_PROMPT_PATH = INFERENCE_ENGINE_DIR / "prompts" / "consolidated_first_pass_prompt.md"
AUDIT_PROMPT_PATH = REPO_ROOT / "docs" / "specs" / "prompts" / "audit-review-instructions.md"
GOLDENSET_PATH = REPO_ROOT / "data" / "goldenset" / "top50_cases.json"


def _read_or(path: Path, fallback: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return fallback


def seed_users(db):
    for u in SEED_USERS:
        if db.query(M.User).filter(M.User.email == u["email"]).first():
            continue
        db.add(M.User(name=u["name"], email=u["email"],
                      password_hash=hash_password(u["password"]), role=u["role"],
                      status=M.UserStatus.ACTIVE))
    db.commit()


def seed_prompts(db):
    if not db.query(M.PromptVersion).filter(M.PromptVersion.type == M.PromptType.ANALYSIS).first():
        db.add(M.PromptVersion(
            version="v1", type=M.PromptType.ANALYSIS,
            body=_read_or(ANALYSIS_PROMPT_PATH, "ANALYSIS PROMPT v1 (fallback)"),
            author="seed", change_note="Imported consolidated_first_pass_prompt.md", active=True,
        ))
    if not db.query(M.PromptVersion).filter(M.PromptVersion.type == M.PromptType.AUDIT).first():
        db.add(M.PromptVersion(
            version="v1", type=M.PromptType.AUDIT,
            body=_read_or(AUDIT_PROMPT_PATH, "AUDIT PROMPT v1 (fallback)"),
            author="seed", change_note="Imported audit-review-instructions.md", active=True,
        ))
    db.commit()


def seed_models(db):
    for m in SEED_MODELS:
        if db.get(M.ModelConfig, m["model_id"]):
            continue
        db.add(M.ModelConfig(
            model_id=m["model_id"], provider=m["provider"], type=m["type"], enabled=True,
            vote_weight=m["vote_weight"], endpoint="", active_version="v1",
            registry_order=m["registry_order"], is_primary=m.get("is_primary", False),
        ))
    if not db.get(M.EngineConfig, "default"):
        db.add(M.EngineConfig(
            id="default", mode=M.EngineMode.CONSENSUS,
            strategy=M.ConsensusStrategy.WEIGHTED_MAJORITY, primary_model_id="mock-a",
        ))
    db.commit()


def _load_fixture_images(client_id: str):
    """Return (image_dicts, image_bytes_list) for a fixture client, or ([],[])."""
    try:
        from app.images import load_client_images  # engine loader (sys.path set by bridge)
        from app.config import get_settings as engine_settings
        dicts = load_client_images(engine_settings().images_root, client_id)
    except Exception:
        dicts = []
    if not dicts:
        return [], []
    byts = [base64.b64decode(d["b64"]) for d in dicts]
    return dicts, byts


def seed_sample_analyses(db, limit: int = 5):
    if db.query(M.Analysis).count() > 0:
        return
    analyst = db.query(M.User).filter(M.User.role == M.Role.ANALYST).first()
    try:
        cases = json.loads(GOLDENSET_PATH.read_text())["cases"]
    except Exception:
        cases = []

    made = 0
    for c in cases:
        if made >= limit:
            break
        client_id = str(c["client_id"])
        image_dicts, image_bytes = _load_fixture_images(client_id)
        if not image_dicts:
            continue  # no fixture images for this client

        analysis = M.Analysis(initiator_id=analyst.id, client_label=f"Client {client_id}",
                              status=AnalysisStatus.DRAFT)
        db.add(analysis)
        db.flush()

        sha = hashlib.sha256(b"".join(image_bytes)).hexdigest()
        emb = memmod.embed_image(image_bytes, dim=SETTINGS.embedding_dim)
        hair, fitz = "I Do Not Know", "II"  # broad, non-conflicting candidate set
        db.add(M.AnalysisInput(
            analysis_id=analysis.id, image_uri="(fixture)", image_embedding=emb,
            image_sha256=sha, hair_colour=hair, fitzpatrick=fitz, freeform_notes="",
            crop_metadata={"auto_crop": "fixture"},
        ))
        # Persist a copy of the bytes so rerun works.
        (SETTINGS.image_store / f"{analysis.id}.bin").write_bytes(b"".join(image_bytes))

        outcome, snapshot, model_runs, consensus_dict, prompt_version = orchestrator.compute_run(
            db, image_dicts=image_dicts, image_bytes_list=image_bytes,
            hair_colour=hair, fitzpatrick=fitz, freeform_notes="", initiator_is_expert=False,
        )
        orchestrator.persist_run(db, analysis, outcome, snapshot, model_runs,
                                 consensus_dict, prompt_version, "v1")
        made += 1
    db.commit()
    return made


def main():
    init_db()
    db = SessionLocal()
    try:
        seed_users(db)
        seed_prompts(db)
        seed_models(db)
        n = seed_sample_analyses(db)
        print("Seed complete.")
        print(f"  users:   {db.query(M.User).count()}")
        print(f"  prompts: {db.query(M.PromptVersion).count()}")
        print(f"  models:  {db.query(M.ModelConfig).count()}")
        print(f"  sample analyses: {db.query(M.Analysis).count()} (new this run: {n or 0})")
        print("\nSeeded credentials (dev only):")
        for u in SEED_USERS:
            print(f"  {u['role'].value:7} {u['email']} / {u['password']}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
