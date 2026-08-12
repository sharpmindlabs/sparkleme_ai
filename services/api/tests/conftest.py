"""Pytest fixtures: isolated SQLite DB + FastAPI TestClient with seeded data."""
from __future__ import annotations
import base64
import io
import os
import sys
import tempfile
from pathlib import Path

# Ensure the repo root is importable as `services.api...` regardless of how
# pytest is invoked.
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import pytest

# Point the API at a throwaway SQLite file + image store BEFORE importing the app.
_TMP = tempfile.mkdtemp(prefix="sparkleme_test_")
os.environ["SPARKLEME_API_DB"] = f"sqlite:///{_TMP}/test.db"
os.environ["SPARKLEME_IMAGE_STORE"] = f"{_TMP}/imgs"
os.environ["SPARKLEME_PROVIDER"] = "mock"

from fastapi.testclient import TestClient  # noqa: E402

from services.api.config import get_settings  # noqa: E402
get_settings.cache_clear()

from services.api.db import init_db, SessionLocal  # noqa: E402
from services.api.main import app  # noqa: E402
from services.api import seed as seed_mod  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _seeded():
    init_db()
    db = SessionLocal()
    try:
        seed_mod.seed_users(db)
        seed_mod.seed_prompts(db)
        seed_mod.seed_models(db)
    finally:
        db.close()
    yield


@pytest.fixture
def client():
    return TestClient(app)


def _token(client, email, password):
    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture
def admin_token(client):
    return _token(client, "admin@sparkleme.dev", "admin123")


@pytest.fixture
def expert_token(client):
    return _token(client, "expert@sparkleme.dev", "expert123")


@pytest.fixture
def analyst_token(client):
    return _token(client, "analyst@sparkleme.dev", "analyst123")


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def fake_image(tag: bytes = b"seed") -> bytes:
    """Deterministic pseudo-image payload (content drives the mock provider)."""
    return b"\xff\xd8\xff\xe0FAKEJPEG" + tag + b"\x00" * 32


def create_analysis(client, token, hair="I Do Not Know", fitz="II",
                    notes="", tag=b"a", client_label="Test", idem=None):
    files = {"image": ("face.jpg", io.BytesIO(fake_image(tag)), "image/jpeg")}
    data = {"hair_colour": hair, "fitzpatrick": fitz,
            "freeform_notes": notes, "client_label": client_label}
    headers = auth(token)
    if idem:
        headers["Idempotency-Key"] = idem
    return client.post("/analyses", files=files, data=data, headers=headers)
