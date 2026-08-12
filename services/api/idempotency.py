"""Idempotency-Key support for mutating endpoints (§11).

A prior response for the same (key, endpoint) is replayed instead of re-executing.
"""
from __future__ import annotations
from fastapi import Header
from sqlalchemy.orm import Session

from . import models as M


def get_idempotency_key(idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    return idempotency_key


def replay(db: Session, key: str | None, endpoint: str) -> dict | None:
    if not key:
        return None
    rec = db.get(M.IdempotencyRecord, (key, endpoint))
    return rec.response_json if rec else None


def store(db: Session, key: str | None, endpoint: str, response_json: dict,
          analysis_id: str | None = None) -> None:
    if not key:
        return
    if db.get(M.IdempotencyRecord, (key, endpoint)):
        return
    db.add(M.IdempotencyRecord(
        key=key, endpoint=endpoint, analysis_id=analysis_id, response_json=response_json,
    ))
    db.flush()
