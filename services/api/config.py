"""Runtime configuration for the SparkleMe platform API.

Everything defaults to an offline, zero-network posture: SQLite on disk and the
inference-engine ``mock`` provider. Point the env vars at real infra to switch.
"""
from __future__ import annotations
import os
from functools import lru_cache
from pathlib import Path

# services/api
API_ROOT = Path(__file__).resolve().parent
# repo root: services/api -> services -> repo
REPO_ROOT = API_ROOT.parents[1]
INFERENCE_ENGINE_DIR = REPO_ROOT / "services" / "inference_engine"


class Settings:
    def __init__(self) -> None:
        self.database_url = os.getenv(
            "SPARKLEME_API_DB", f"sqlite:///{API_ROOT / 'sparkleme.db'}"
        )
        # JWT signing
        self.jwt_secret = os.getenv("SPARKLEME_JWT_SECRET", "dev-insecure-secret-change-me")
        self.jwt_algorithm = "HS256"
        self.jwt_expiry_minutes = int(os.getenv("SPARKLEME_JWT_EXPIRY_MIN", "720"))

        # Inference: reuse services/inference_engine. Default mock => offline.
        self.inference_provider = os.getenv("SPARKLEME_PROVIDER", "mock").lower()

        # Determinism knobs (FR-2.7): fixed seed + temperature 0.
        self.inference_seed = int(os.getenv("SPARKLEME_SEED", "42"))
        self.inference_temperature = float(os.getenv("SPARKLEME_TEMPERATURE", "0"))

        # Correction-memory cosine threshold (FR-5.4).
        self.memory_match_threshold = float(os.getenv("SPARKLEME_MEMORY_THRESHOLD", "0.92"))
        self.embedding_dim = 64

        # Where uploaded face images are stored (encrypted-at-rest is stubbed).
        self.image_store = Path(os.getenv("SPARKLEME_IMAGE_STORE", str(API_ROOT / "_imagestore")))
        self.image_store.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> "Settings":
    return Settings()
