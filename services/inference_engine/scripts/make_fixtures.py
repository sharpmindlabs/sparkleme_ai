"""Generate synthetic placeholder drape images so the mock pipeline runs without
the real (large, access-restricted) client photos. NOT real data."""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT.parents[1] / "data" / "goldenset" / "top50_cases.json"
OUT = ROOT / "fixtures" / "cases"
PAGES = ["Home Season", "Winter Flows", "Spring Flows", "Summer Flows", "Autumn Flows"]

def make(n=6):
    cases = json.loads(GOLD.read_text())["cases"][:n]
    for c in cases:
        cid = str(c["client_id"]); d = OUT / cid; d.mkdir(parents=True, exist_ok=True)
        for i, label in enumerate(PAGES):
            img = Image.new("RGB", (512, 640), (40 + i * 30, 60, 120))
            dr = ImageDraw.Draw(img)
            dr.ellipse((156, 140, 356, 380), fill=(220, 190, 170))  # placeholder "face"
            dr.text((20, 20), f"[PLACEHOLDER] client {cid}", fill="white")
            dr.text((20, 600), f"page {i+1}/5 - {label}", fill="white")
            img.save(d / f"{cid}_{i+1}.png")
    print(f"generated {len(cases)} placeholder client sets under {OUT}")

if __name__ == "__main__":
    make(int(sys.argv[1]) if len(sys.argv) > 1 else 6)
