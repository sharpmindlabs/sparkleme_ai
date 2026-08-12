# SparkleMe AI

AI-assisted virtual **colour analysis** — determining which of ten colour palettes
harmonizes with a person's natural colouring, digitizing expert "Carol's" CAMS method.

This repo currently contains the **core inferencing engine + eval UI** (the first slice),
plus the full source documentation for the wider platform.

## What's here

| Path | What it is |
|---|---|
| `services/inference_engine/` | The inference engine + eval harness: 5 drape images → AI vision model → 1 of 10 palettes, scored vs Carol's ground truth. Runnable now. |
| `apps/web/` | React review UI: run all cases, review AI-vs-Carol results, accuracy + confusion. |
| `data/goldenset/` | The TOP-50 ground truth (Carol's column O) + refinement trail. |
| `data/rulebook/source_docs/` | The CAMS knowledge corpus (25 KB docs + 3 base prompts) + digest. |
| `docs/specs/` | Official BRD, Functional Spec, Technical Spec, and the two operational prompts. |
| `docs/prototype/` | Reference UX prototype. |

## The inference slice (built first)

Takes **5 drape images per client** (no hair colour / Fitzpatrick), sends them to a vision
model with a **consolidated CAMS prompt** — Carol's base method + the 14 standing rules
distilled from her 31-case refinement trail — and returns one of the ten palettes with
per-step reasoning. Results are scored against Carol's column O (lenient on stated boundaries).

**Baseline to beat:** Carol's own first pass was 32/50 (64%).

### Run the demo (mock, no keys, no network)
```bash
make install          # pip install engine deps
make demo             # generate placeholder images + run a mock batch (CLI)

# or the full UI:
cd apps/web && npm install && npm run build   # build the UI
make engine           # serve API + UI at http://localhost:8000
```

### Run for real
Set a provider in `services/inference_engine/.env` (`anthropic` or `azure_foundry`),
place each client's images at `${SPARKLEME_IMAGES_ROOT}/<client_id>/*.jpg` (or a
`<client_id>.pdf`), and run `make engine`. See `services/inference_engine/README.md`.

> Note on the dev sandbox: the Azure AI Foundry endpoint and the client image store are
> both network-blocked from the cloud dev environment, so the live 5-model bake-off runs
> on infra where those are reachable. The engine + UI run here fully on the mock provider.

## Wider platform
The BRD/Functional/Technical specs in `docs/specs/` define the full 6-milestone platform
(Keycloak, PostgreSQL+pgvector, Temporal, LiteLLM/vLLM, consensus, correction memory,
golden-set-gated MLOps). The inference engine here is the M2 core of that plan.
