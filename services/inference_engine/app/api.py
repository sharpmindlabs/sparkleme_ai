"""FastAPI surface for the inference engine + review UI."""
from __future__ import annotations
import base64
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, FileResponse
from pydantic import BaseModel

from .config import get_settings
from .batch import run_batch, load_goldenset, available_client_ids
from .images import load_client_images
from .palettes import PALETTES, FLOWS_BY_SEASON

app = FastAPI(title="SparkleMe Inference Engine", version="0.1.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)


class RunRequest(BaseModel):
    client_ids: list[str] | None = None
    only_available: bool = True


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/config")
def config():
    s = get_settings()
    have = available_client_ids()
    return {
        "provider": s.provider,
        "model": s.model_label(),
        "images_root": str(s.images_root),
        "available_clients": sorted(have),
        "available_count": len(have),
        "palettes": PALETTES,
        "flows_by_season": FLOWS_BY_SEASON,
    }


@app.get("/api/cases")
def cases():
    have = available_client_ids()
    out = []
    for c in load_goldenset():
        cid = str(c["client_id"])
        out.append({**c, "client_id": cid, "has_images": cid in have})
    return out


@app.post("/api/run")
def run(req: RunRequest):
    summary = run_batch(client_ids=req.client_ids, only_available=req.only_available)
    return json.loads(summary.model_dump_json())


@app.get("/api/results")
def results():
    p = get_settings().results_dir / "latest.json"
    if not p.is_file():
        raise HTTPException(404, "no results yet — run a batch first")
    return json.loads(p.read_text(encoding="utf-8"))


@app.get("/api/image/{client_id}/{idx}")
def image(client_id: str, idx: int):
    imgs = load_client_images(get_settings().images_root, client_id)
    if idx < 0 or idx >= len(imgs):
        raise HTTPException(404, "image not found")
    img = imgs[idx]
    return Response(content=base64.b64decode(img["b64"]), media_type=img["media_type"])


# Serve the built UI if present (apps/web/dist copied to app/static)
_static = Path(__file__).resolve().parent / "static"
if _static.is_dir():
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=str(_static), html=True), name="ui")
