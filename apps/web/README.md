# SparkleMe — Inference Review UI

A lightweight single-page tool for running the SparkleMe inference engine over
the 50 golden-set client cases and reviewing each AI verdict against expert
Carol's ground truth, with overall accuracy and a confusion view.

Stack: React 19 · TypeScript (strict) · Vite · Tailwind CSS. No component
library — small hand-rolled, accessible components.

## Prerequisites

The inference engine must be running on **http://localhost:8000**:

```bash
# from services/inference_engine/
pip install -r requirements.txt
cp .env.example .env          # set SPARKLEME_PROVIDER + keys (defaults to mock)
uvicorn app.api:app --reload  # serves the /api endpoints on :8000
```

With `SPARKLEME_PROVIDER=mock` you get placeholder results (no keys needed) —
useful for exercising the UI. Configure `anthropic` or `azure_foundry` in
`.env` for real model runs.

## Run the UI

```bash
cd apps/web
npm install
npm run dev
```

Open the printed URL (default http://localhost:5173). The Vite dev server
proxies `/api` → `http://localhost:8000`, so no CORS setup is needed.

On load the UI fetches `/api/config`, `/api/cases`, and the latest
`/api/results` (if any) so prior results show without re-running. Press **Run**
to POST `/api/run` — the endpoint is synchronous and can take a few minutes with
a real model; a spinner shows progress.

## Scripts

- `npm run dev` — dev server with API proxy
- `npm run build` — type-check (`tsc -b`) + production build to `dist/`
- `npm run preview` — serve the production build locally

## Configuration

- `VITE_API_BASE` (optional) — override the engine API base. Defaults to the
  same-origin `/api`, which works behind the dev proxy and when the engine
  serves the built UI. See `.env.example`.

## Production / serving from the engine

`npm run build` emits static assets to `dist/`. The engine mounts
`app/static/` at `/` when present (see `services/inference_engine/app/api.py`),
so copying `dist/` there lets the engine serve the UI on the same origin as the
API — no proxy or `VITE_API_BASE` needed.

## Notes

- Palette values render with a colour swatch using the spec's hex refs
  (`src/palettes.ts`).
- Cases without drape images in the current environment are de-emphasised and
  labelled "images not available in this environment". Individual broken
  thumbnails hide themselves gracefully.
- The static baseline chip "Carol first-pass: 32/50 (64%)" is shown for
  comparison against the run's accuracy.
