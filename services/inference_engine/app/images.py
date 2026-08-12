"""Load a client's drape images (5 per client).

Accepts either a folder of image files (<root>/<client_id>/*.jpg|png) or a single
PDF (<root>/<client_id>.pdf or <root>/<client_id>/<something>.pdf) whose pages are
rendered to images. Returns base64 data URIs suitable for vision model calls.
"""
from __future__ import annotations
import base64
import io
from pathlib import Path

IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}


def _b64(data: bytes, media_type: str) -> dict:
    return {"media_type": media_type, "b64": base64.b64encode(data).decode("ascii")}


def _render_pdf(path: Path, max_pages: int = 5, zoom: float = 2.0) -> list[dict]:
    import pymupdf  # lazy import
    out: list[dict] = []
    doc = pymupdf.open(path)
    for i, page in enumerate(doc):
        if i >= max_pages:
            break
        pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
        out.append(_b64(pix.tobytes("png"), "image/png"))
    doc.close()
    return out


def _load_image_file(path: Path) -> dict:
    media = "image/jpeg" if path.suffix.lower() in {".jpg", ".jpeg"} else f"image/{path.suffix.lower().lstrip('.')}"
    return _b64(path.read_bytes(), media)


def find_client_dir(images_root: Path, client_id: str) -> Path | None:
    """A client folder may be named '<client_id>' or '<seq>-<client_id>'."""
    if not images_root.exists():
        return None
    exact = images_root / client_id
    if exact.is_dir():
        return exact
    for child in images_root.iterdir():
        if child.is_dir() and child.name.split("-")[-1] == client_id:
            return child
    return None


def load_client_images(images_root: Path, client_id: str, max_images: int = 5) -> list[dict]:
    """Return up to `max_images` images as {media_type, b64} dicts, or [] if none."""
    # a bare pdf named <client_id>.pdf
    pdf = images_root / f"{client_id}.pdf"
    if pdf.is_file():
        return _render_pdf(pdf, max_pages=max_images)

    cdir = find_client_dir(images_root, client_id)
    if cdir is None:
        return []

    imgs = sorted(p for p in cdir.iterdir() if p.suffix.lower() in IMG_EXTS)
    if imgs:
        return [_load_image_file(p) for p in imgs[:max_images]]

    pdfs = sorted(p for p in cdir.iterdir() if p.suffix.lower() == ".pdf")
    if pdfs:
        return _render_pdf(pdfs[0], max_pages=max_images)
    return []
