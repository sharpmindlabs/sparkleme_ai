# SparkleMe Platform API (`services/api`)

The platform backend for SparkleMe — the AI virtual colour-analysis product that
classifies a person into one of ten colour palettes using the expert **CAMS**
method. This service implements the [Functional Spec](../../docs/specs/02-functional-spec.md):
RBAC, deterministic rule-outs, analysis orchestration with multi-model consensus,
the correction-memory instant-regression guarantee, the prompt registry, the admin
console, and role-scoped metrics.

It reuses the existing vision pipeline in [`services/inference_engine`](../inference_engine)
for real inference and **defaults to the offline `mock` provider**, so the whole
service runs with zero network access and no API keys.

---

## Run it

From the **repo root** (`sparkleme_ai/`):

```bash
# 1. install deps
pip install -r services/api/requirements.txt

# 2. seed the database (users, prompts, models, sample analyses)
python -m services.api.seed

# 3. serve the API (http://localhost:8000, docs at /docs)
uvicorn services.api.main:app --reload

# run the test suite
python -m pytest services/api
```

The DB is created automatically on startup; the seed step is what populates it
with the credentials and sample data below.

### Seeded credentials (dev only)

| Role | Email | Password |
|---|---|---|
| Admin | `admin@sparkleme.dev` | `admin123` |
| Expert | `expert@sparkleme.dev` | `expert123` |
| Analyst | `analyst@sparkleme.dev` | `analyst123` |

`POST /auth/login` returns a JWT; send it as `Authorization: Bearer <token>`.

---

## Sandbox infrastructure substitutions

This dev container cannot run the production infra, so each piece has an in-process
equivalent. The seams are kept "production-shaped" so the real service slots in.

| Concern | Production (per spec) | Sandbox substitution here |
|---|---|---|
| Database | Postgres + pgvector | **SQLite** via SQLAlchemy 2.0 (`sparkleme.db`) |
| Vectors / similarity | pgvector ANN | image embedding stored as a **JSON float array**; **cosine in numpy** (`domain/memory.py`) |
| Auth | Keycloak / OIDC SSO | email+password → **JWT (PyJWT)** with a role claim; **bcrypt** password hashes. Same bearer→claims→role-gate shape SSO would use |
| Workflow | Temporal | **in-process synchronous orchestration** (`orchestrator.py`) |
| Model gateway | vLLM / Azure Foundry / Anthropic / OpenAI adapters | reuse `services/inference_engine` providers; **`mock` provider by default** (offline, deterministic). Set `SPARKLEME_PROVIDER=azure_foundry` + the engine's env keys for real inference |
| Image embedding | learned biometric embedding | **deterministic hash-derived feature vector** from image bytes (identical bytes → cosine 1.0). Good enough to prove the memory-HIT regression guarantee |
| Encryption at rest | KMS-encrypted image store | images written to a local `_imagestore/` (encryption **stubbed**) |
| Multi-model fan-out | N real provider calls in parallel | one engine call for evidence + **deterministic per-model votes** `sha256(image+model_id) → candidate_set`, so consensus weighting is real and reproducible |

Relevant env vars (all optional): `SPARKLEME_API_DB`, `SPARKLEME_JWT_SECRET`,
`SPARKLEME_PROVIDER`, `SPARKLEME_SEED`, `SPARKLEME_MEMORY_THRESHOLD`,
`SPARKLEME_IMAGE_STORE`.

---

## How a run works (`orchestrator.py`)

1. **Input validation** → `INVALID_INPUT` if hair/Fitzpatrick aren't canonical or no image.
2. **Deterministic rule-outs** (§5.1 hair, §5.2 Fitzpatrick). `candidate_set = L1 ∩ L2`; empty → `CONFLICTING_INPUTS`.
3. **Correction-memory lookup** (synchronous, every run). A HIT (cosine ≥ threshold *and* matching hair+fitz key) **short-circuits** to the expert-verified palette.
4. On a MISS: run inference (mock), collect a deterministic weighted vote per enabled model, apply **consensus** (weighted majority / unanimity), discarding any vote outside the candidate set.
5. **Output-contract validation** (§5.5): `flow_result ∈ candidate_set`, flow valid for `home_season`, `home_season` consistent with `undertone`. Any violation → `NEEDS_HUMAN_REVIEW`, never silently fixed.
6. Persist `ModelRun`s, `ConsensusResult`, `AuditRecord`, evidence, `prompt_version`, and the frozen `engine_config_snapshot` (FR-7.1 reproducibility).

Everything is deterministic (fixed seed, temperature 0), so a duplicate submission
returns an identical result (FR-2.7), and a rerun after an expert correction returns
the expert's palette via a memory HIT (FR-5.4).

---

## Endpoints (§11)

| Method & path | Roles | Notes |
|---|---|---|
| `POST /auth/login` · `GET /auth/me` | all | JWT issue / whoami |
| `POST /analyses` | Analyst, Expert, Admin | multipart `image` + `hair_colour` + `fitzpatrick` + `freeform_notes` |
| `GET /analyses/rule-preview` | all | live Level-1/2 + intersection (FR-2.5) |
| `GET /analyses` | all (scoped) | search/filter/sort/paginate |
| `GET /analyses/{id}` | all (scoped) | detail + evidence + votes + output contract |
| `POST /analyses/{id}/review` | Expert, Admin | `verdict=APPROVE\|CORRECT` |
| `POST /analyses/{id}/rerun` | Expert, Admin | reports memory HIT/MISS |
| `GET/POST /prompts/{type}/versions` · `PUT /prompts/{type}/active` | Expert, Admin | immutable versions, one active per type |
| `GET/PUT /admin/engine` | Admin | mode / strategy / primary model |
| `GET/POST/PATCH /admin/models` | Admin | model registry |
| `GET/POST/PATCH /admin/users` | Admin | user management |
| `GET /admin/memory` · `DELETE /admin/memory/{id}` | Admin | correction-memory ops |
| `GET/POST /admin/training/jobs` | Admin | training pipeline (stubbed eval) |
| `GET /metrics/{scope}` | role-scoped | `analyst` / `expert` / `admin` |

RBAC is enforced from the §2 matrix via `require_roles(...)` (`security.py`).
All mutating endpoints honour an `Idempotency-Key` header. CORS is fully permissive
(dev) for the local frontend.

---

## Functional requirements: implemented vs stubbed

**Implemented**

- FR-1 auth/session (JWT + roles, suspended-user block).
- FR-2 start analysis: canonical 12 hair values + I–VI Fitzpatrick, rule-out preview, deterministic seeded run, engine snapshot.
- FR-3 listing: role-scoped, search/filter/sort/paginate.
- FR-4 detail: candidate-set chips, evidence a–d, model votes, output contract.
- FR-5 review/correction/rerun: approve (comments required), correct (constrained to candidate set, FR-5.5 block), **synchronous memory write + rerun memory HIT (FR-5.3/5.4)**.
- FR-6 prompt registry: immutable versions, one active per type, audit-logged activation.
- FR-7 admin: platform-wide engine mode/strategy (snapshotted per analysis), model registry, user management, memory view/expire, metrics.
- Core domain (§5): Level-1/2 rule-out tables, candidate intersection, output-contract hard constraints, lifecycle state machine (§8), weighted-majority consensus.

**Stubbed (cleanly, noted in code)**

- **Image service**: no real face detection / auto-crop / overlay composition — the uploaded image is stored as-is and crop metadata is a placeholder. `INVALID_INPUT` triggers only on a missing image, not on true image-quality checks.
- **Audit service (checks 1–7)**: reduced to a contract-outcome verdict (`APPROVE`/`REVISE`/`REJECT`) rather than an independent auditor model pass.
- **Training pipeline (FR-7.5)**: `POST /admin/training/jobs` records a job and returns a *simulated* golden-set result; no real SFT/DPO/fine-tune runs.
- **Report email / PDF export (FR-4.5)**: not implemented (no `/report/*` routes).
- **Real multi-provider fan-out**: per-model votes are deterministic simulations in the sandbox (see substitution table); wire real provider adapters for production.
- **SSE pipeline stepper / `202 Accepted` async mode**: runs are synchronous; the create call returns the finished result directly.

---

## Layout

```
services/api/
  main.py              FastAPI app + router wiring
  config.py            settings (env-driven, offline defaults)
  db.py  models.py     SQLAlchemy 2.0 engine + ORM (Data Model §9)
  security.py          bcrypt + JWT + require_roles RBAC deps
  orchestrator.py      the analysis pipeline (§6)
  inference_bridge.py  sys.path bridge to services/inference_engine
  serializers.py       ORM → dict + §5.5 output contract
  idempotency.py       Idempotency-Key replay/store
  schemas.py           Pydantic request/response models
  domain/              pure, unit-tested logic
    palettes.py ruleouts.py contract.py consensus.py memory.py state_machine.py
  routers/             auth, analyses, prompts, admin, metrics
  seed.py              seed users/prompts/models/sample analyses
  tests/               pytest suite (42 tests, all offline)
```
