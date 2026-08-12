"""Extract each client's INVARIANT complexion signature from the drape-grid photos.

The drape photos are 4-column (Winter/Summer/Spring/Autumn) x 5-row contact grids
with the SAME face cutout composited onto every drape. The skin never changes with
the drape, so we can measure the person's true colour signature once:

  - skin L*, a*, b*  (CIELAB)
  - ITA  (Individual Typology Angle) -> depth/value (higher = lighter)
  - undertone hue angle atan2(b*,a*) and warm/cool call
  - chroma sqrt(a*^2+b*^2)  -> bright vs muted
  - hair-skin luminance contrast -> high/low contrast

Segmentation is cleanest against the neutral Winter/Summer drapes (black/grey/blue/
purple), so skin pixels are pooled from those columns; the modal skin colour is robust
to the minority of drape-tinted edge pixels.
"""
from __future__ import annotations
import json, math, sys
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
IMAGES = ROOT / "realimages"


# ---- sRGB -> CIELAB (D65) ----
def rgb_to_lab(rgb):
    rgb = np.asarray(rgb, float) / 255.0
    m = rgb > 0.04045
    lin = np.where(m, ((rgb + 0.055) / 1.055) ** 2.4, rgb / 12.92)
    X = lin @ np.array([0.4124, 0.3576, 0.1805])
    Y = lin @ np.array([0.2126, 0.7152, 0.0722])
    Z = lin @ np.array([0.0193, 0.1192, 0.9505])
    xyz = np.stack([X / 0.95047, Y / 1.0, Z / 1.08883], -1)
    d = 6 / 29
    f = np.where(xyz > d ** 3, np.cbrt(xyz), xyz / (3 * d * d) + 4 / 29)
    L = 116 * f[..., 1] - 16
    a = 500 * (f[..., 0] - f[..., 1])
    b = 200 * (f[..., 1] - f[..., 2])
    return np.stack([L, a, b], -1)


def find_client_dir(client_id: str):
    exact = IMAGES / client_id
    if exact.is_dir():
        return exact
    for c in IMAGES.iterdir():
        if c.is_dir() and c.name.split("-")[-1] == client_id:
            return c
    return None


def _local_std(gray, k=2):
    """Cheap local stddev via box mean of x and x^2 (drapes are flat -> low std)."""
    from numpy.lib.stride_tricks import sliding_window_view
    pad = np.pad(gray, k, mode="edge")
    win = sliding_window_view(pad, (2 * k + 1, 2 * k + 1))
    m = win.mean(axis=(-1, -2))
    m2 = (win.astype(float) ** 2).mean(axis=(-1, -2))
    return np.sqrt(np.maximum(m2 - m * m, 0))


def extract(client_id: str):
    """Layout-agnostic: skin is the dominant TEXTURED fleshy cluster. Drapes are large
    FLAT regions (low local std) and are removed regardless of grid layout."""
    cdir = find_client_dir(client_id)
    if not cdir:
        return None
    imgs = sorted([p for p in cdir.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"}])
    if not imgs:
        return None

    skin_all, hair_all = [], []
    for p in imgs[:5]:
        im = np.asarray(Image.open(p).convert("RGB")).astype(float)
        # downsample for speed
        step = max(1, int(min(im.shape[:2]) / 500))
        sm = im[::step, ::step]
        gray = sm.mean(2)
        std = _local_std(gray, 2)
        textured = std > 6.0  # drapes are flat; face/hair are textured
        R, G, B = sm[..., 0], sm[..., 1], sm[..., 2]
        skin_m = textured & (R > G) & (G >= B) & (R > 70) & (R < 245) & ((R - B) > 12) & ((R - B) < 130)
        hair_m = textured & (R < 95) & (G < 90) & (B < 90) & (np.abs(R - B) < 35)
        skin_all.append(sm[skin_m])
        hair_all.append(sm[hair_m])

    skin = np.concatenate(skin_all)
    if len(skin) < 200:
        return {"client_id": client_id, "error": "insufficient skin pixels"}
    # dominant skin cluster: iterate median a few times, trimming outliers
    for _ in range(3):
        med = np.median(skin, 0)
        skin = skin[np.linalg.norm(skin - med, axis=1) < 38]
        if len(skin) < 200:
            break
    skin_rgb = skin.mean(0)
    hair = np.concatenate(hair_all) if sum(len(h) for h in hair_all) > 300 else None

    lab = rgb_to_lab(skin_rgb)
    L, a, b = float(lab[0]), float(lab[1]), float(lab[2])
    ita = math.degrees(math.atan2(L - 50, b)) if b != 0 else 0.0
    hue = math.degrees(math.atan2(b, a))
    chroma = math.hypot(a, b)
    hair_L = float(rgb_to_lab(hair.mean(0))[0]) if hair is not None else None
    contrast = (L - hair_L) if hair_L is not None else None

    return {
        "client_id": client_id,
        "skin_rgb": [round(x, 1) for x in skin_rgb.tolist()],
        "L": round(L, 1), "a": round(a, 1), "b": round(b, 1),
        "ita": round(ita, 1), "hue_deg": round(hue, 1), "chroma": round(chroma, 1),
        "hair_L": round(hair_L, 1) if hair_L is not None else None,
        "contrast": round(contrast, 1) if contrast is not None else None,
        "n_skin_px": int(len(skin)),
    }


if __name__ == "__main__":
    cases = json.load(open(ROOT.parent.parent / "data" / "goldenset" / "top50_cases.json"))["cases"]
    out = {}
    for c in cases:
        cid = c["client_id"]
        try:
            m = extract(cid)
        except Exception as e:
            m = {"client_id": cid, "error": str(e)}
        if m:
            m["carol"] = c["carol_result"]
            out[cid] = m
    (ROOT / "results").mkdir(exist_ok=True)
    json.dump(out, open(ROOT / "results" / "skin_metrics.json", "w"), indent=2)
    print(f"extracted {len(out)} clients -> results/skin_metrics.json")
