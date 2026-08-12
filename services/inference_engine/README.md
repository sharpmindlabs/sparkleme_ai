# SparkleMe — Inference Engine

Core colour-analysis inference engine + eval harness. Takes **5 drape images per
client**, calls an AI vision model with a **consolidated CAMS prompt** (no hair /
Fitzpatrick inputs), and scores the result against expert **Carol's** ground truth
(column O of the TOP-50 workbook).

## What it does
- Loads a client's 5 drape images (a folder of images, or a 5-page PDF that gets rendered).
- Sends them + the consolidated first-pass prompt to a vision model.
- Parses a strict-JSON verdict: one of the **10 palettes** + home season + leaning + confidence + per-step reasoning.
- Scores vs Carol's column O — **lenient on stated boundaries** (e.g. *"Deep or True Winter…"* accepts either).
- Produces accuracy, exact-accuracy, and a confusion matrix over the 50 cases.

## Providers (`SPARKLEME_PROVIDER`)
| value | model | notes |
|---|---|---|
| `mock` | — | deterministic, no network; runs anywhere (default) |
| `anthropic` | Claude vision | reachable from the dev sandbox; set `ANTHROPIC_API_KEY` |
| `azure_foundry` | grok-4.3 / gpt-5.6-sol / gpt-5.4 / gpt-5.6-terra / Kimi-K2.6 | your Azure AI Foundry endpoint; set `AZURE_FOUNDRY_*`. Kimi-K2.6 is **text-only** (no drape judging). |

> The Azure adapter is written to the documented Foundry contract but could not be
> validated from the dev sandbox (the Azure host is egress-blocked there). Verify
> `AZURE_FOUNDRY_BASE_URL` / `AZURE_FOUNDRY_API_VERSION` on your infra.

## Quick start
```bash
cd services/inference_engine
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # then edit provider + keys

# make placeholder images so the mock runs without the real photos:
python scripts/make_fixtures.py 6

# run a batch from the CLI (mock):
SPARKLEME_PROVIDER=mock python -m app.cli

# or serve the API for the review UI:
uvicorn app.api:app --port 8000
```

### Running against real images + a real model
Put each client's images at `${SPARKLEME_IMAGES_ROOT}/<client_id>/*.jpg` (or a
`<client_id>.pdf`). Client ids are the workbook's column B (folder names like
`009-6779` are matched on the trailing id). Then:
```bash
SPARKLEME_PROVIDER=azure_foundry SPARKLEME_AZURE_MODEL=gpt-5.6-sol \
  AZURE_FOUNDRY_API_KEY=... python -m app.cli
```
Run each model in turn to compare; results are written to `results/latest.json`.

## Tests
```bash
pip install pytest && python -m pytest tests/ -q
```

## Layout
```
app/
  palettes.py   10 palettes, flow structure, column-O parser
  schema.py     Pydantic contracts (InferenceResult, CaseResult, BatchSummary)
  scoring.py    lenient scoring + confusion
  images.py     load 5 images per client (folder or PDF)
  providers/    mock · anthropic · azure_foundry
  engine.py     run one client
  batch.py      run the golden set
  api.py        FastAPI for the review UI
  cli.py        command-line batch runner
prompts/        consolidated CAMS prompt (authored separately)
scripts/        fixture generator
tests/
```
