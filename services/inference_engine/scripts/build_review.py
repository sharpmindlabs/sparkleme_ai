"""Build a self-contained HTML review page from the bake-off results.
Embeds client drape thumbnails (base64) + every model's verdict vs Carol's
ground truth + reasoning + per-model accuracy. Output: results/review.html
"""
import base64, glob, html, json
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1]
GT = {c["client_id"]: c for c in json.loads(
    (ENGINE.parents[1] / "data/goldenset/top50_cases.json").read_text())["cases"]}
SWATCH = {"True Winter": "#66008D", "True Summer": "#875F96", "True Spring": "#FCFB58",
          "True Autumn": "#9B710B", "Cool": "#8535A3", "Warm": "#E9BA47", "Deep": "#551455",
          "Bright": "#F000FA", "Light": "#E4DBD3", "Muted": "#5A4646"}
BADGE = {"exact": ("#137333", "exact"), "boundary": ("#a86400", "boundary"),
         "miss": ("#b00020", "miss"), "error": ("#666", "error"),
         "no_ground_truth": ("#888", "no truth")}


def load_models():
    out = {}
    for f in sorted(glob.glob(str(ENGINE / "results/results_*.json"))):
        d = json.loads(Path(f).read_text())
        out[d.get("model", Path(f).stem)] = d
    return out


def img_dir(client_id):
    root = ENGINE / "realimages"
    if not root.exists():
        return None
    for c in root.iterdir():
        if c.is_dir() and c.name.split("-")[-1] == client_id:
            return c
    return None


def thumbs(client_id):
    import io
    from PIL import Image
    d = img_dir(client_id)
    if not d:
        return ""
    imgs = sorted(p for p in d.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"})[:5]
    out = []
    for p in imgs:
        try:
            im = Image.open(p).convert("RGB")
            im.thumbnail((520, 900))  # downscale for a lightweight page
            buf = io.BytesIO()
            im.save(buf, format="JPEG", quality=62)
            b64 = base64.b64encode(buf.getvalue()).decode()
        except Exception:
            b64 = base64.b64encode(p.read_bytes()).decode()
        out.append(f'<img src="data:image/jpeg;base64,{b64}" loading="lazy">')
    return '<div class="thumbs">' + "".join(out) + "</div>"


def chip(palette):
    c = SWATCH.get(palette, "#999")
    return (f'<span class="chip"><span class="sw" style="background:{c}"></span>'
            f'{html.escape(str(palette))}</span>')


def build():
    models = load_models()
    if not models:
        raise SystemExit("no results_*.json found")
    clients = [c["client_id"] for c in next(iter(models.values()))["cases"]]

    # summary
    rows = []
    for m, d in models.items():
        rows.append((m, d["accuracy"], d["exact_accuracy"], d["exact"], d["boundary"],
                     d["misses"], d["errors"], d["scored"]))
    rows.sort(key=lambda r: r[1], reverse=True)
    summ = "".join(
        f"<tr><td>{html.escape(m)}</td><td class=num>{acc:.0%}</td><td class=num>{exx:.0%}</td>"
        f"<td class=num>{e}</td><td class=num>{b}</td><td class=num>{mi}</td>"
        f"<td class=num>{er}</td><td class=num>{sc}</td></tr>"
        for (m, acc, exx, e, b, mi, er, sc) in rows)

    # per client
    cards = []
    for cid in clients:
        g = GT.get(cid, {})
        carol = g.get("carol_result", "?")
        model_rows = []
        for m, d in models.items():
            cc = next(c for c in d["cases"] if c["client_id"] == cid)
            color, label = BADGE.get(cc["match_kind"], ("#888", cc["match_kind"]))
            pred = cc.get("predicted") or "—"
            r = cc.get("result") or {}
            reason = html.escape((r.get("final_reasoning") or cc.get("error") or "")[:600])
            model_rows.append(
                f'<tr><td class=mdl>{html.escape(m)}</td><td>{chip(pred)}</td>'
                f'<td><span class="badge" style="background:{color}">{label}</span></td>'
                f'<td>{html.escape(str(cc.get("confidence") or ""))}</td>'
                f'<td class=reason>{reason}</td></tr>')
        cards.append(f"""
        <section class=card>
          <div class=chead><h3>Client {html.escape(cid)}</h3>
            <div>Carol: {chip(carol)}</div></div>
          {thumbs(cid)}
          <table class=mtab><thead><tr><th>Model</th><th>Predicted</th><th>Match</th>
            <th>Conf</th><th>Reasoning</th></tr></thead>
            <tbody>{"".join(model_rows)}</tbody></table>
        </section>""")

    doc = f"""<!doctype html><html><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>SparkleMe Review</title><style>
:root{{color-scheme:light dark}}
body{{font:14px/1.5 system-ui,sans-serif;margin:0;background:#f6f6f8;color:#111}}
@media(prefers-color-scheme:dark){{body{{background:#15151a;color:#eee}}.card,.sumwrap{{background:#1e1e26 !important;border-color:#333 !important}}}}
header{{padding:20px 24px;background:#5b2a86;color:#fff}}
header h1{{margin:0;font-size:20px}} header p{{margin:4px 0 0;opacity:.85}}
main{{max-width:1100px;margin:0 auto;padding:20px}}
.sumwrap{{background:#fff;border:1px solid #e2e2e8;border-radius:10px;padding:14px 16px;margin-bottom:20px;overflow-x:auto}}
table{{border-collapse:collapse;width:100%}} th,td{{padding:6px 10px;text-align:left;border-bottom:1px solid #eee2}}
.num{{text-align:right;font-variant-numeric:tabular-nums}}
.card{{background:#fff;border:1px solid #e2e2e8;border-radius:10px;padding:16px;margin-bottom:18px}}
.chead{{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}}
.chead h3{{margin:0}}
.thumbs{{display:flex;gap:6px;overflow-x:auto;margin:12px 0}}
.thumbs img{{height:150px;border-radius:6px;border:1px solid #0002}}
.mtab td{{vertical-align:top}} .mdl{{font-weight:600;white-space:nowrap}}
.reason{{font-size:12.5px;color:#444;max-width:520px}}
@media(prefers-color-scheme:dark){{.reason{{color:#bbb}}}}
.chip{{display:inline-flex;align-items:center;gap:6px;white-space:nowrap}}
.sw{{width:12px;height:12px;border-radius:3px;display:inline-block;border:1px solid #0003}}
.badge{{color:#fff;padding:1px 8px;border-radius:20px;font-size:12px}}
</style></head><body>
<header><h1>SparkleMe — Inference Review</h1>
<p>{len(clients)}-client sample · {len(models)} models · baseline: Carol first-pass 64% (32/50)</p></header>
<main>
<div class=sumwrap><table><thead><tr><th>Model</th><th class=num>Accuracy</th>
<th class=num>Exact</th><th class=num>✓</th><th class=num>~</th><th class=num>✗</th>
<th class=num>err</th><th class=num>n</th></tr></thead><tbody>{summ}</tbody></table></div>
{"".join(cards)}
</main></body></html>"""
    out = ENGINE / "results" / "review.html"
    out.write_text(doc, encoding="utf-8")
    print("wrote", out, f"({len(doc)//1024} KB)")
    return out


if __name__ == "__main__":
    build()
