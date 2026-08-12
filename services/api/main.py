"""SparkleMe Platform API — FastAPI application entrypoint.

Run: ``uvicorn services.api.main:app --reload`` (from the repo root).
Seed: ``python -m services.api.seed``.
"""
from __future__ import annotations
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import init_db
from .routers import auth, analyses, prompts, admin, metrics


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="SparkleMe Platform API", version="1.0.0", lifespan=lifespan)

# Permissive CORS for the local frontend (dev only).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], expose_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True, "service": "sparkleme-api"}


app.include_router(auth.router)
app.include_router(analyses.router)
app.include_router(prompts.router)
app.include_router(admin.router)
app.include_router(metrics.router)
