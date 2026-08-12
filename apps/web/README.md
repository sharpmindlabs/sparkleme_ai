# SparkleMe — Web App (`apps/web`)

Role-based web client for the SparkleMe virtual colour-analysis platform.
React 19 + Vite 6 + TypeScript + TailwindCSS 3 + React Router 7.

It implements the three-role application described in
`docs/specs/02-functional-spec.md` (FR-1…FR-8) against the documented REST
contract (§11). The rule-out tables (§5.1/§5.2), the ten palettes (§1.1), the
output contract (§5.5) and the seven drape criteria (§5.4) are reproduced
client-side.

## Run

```bash
cd apps/web
npm install
npm run dev      # http://localhost:5173
npm run build    # tsc -b && vite build — must pass
npm run preview  # serve the production build
```

### Backend / API base

The API base URL comes from `VITE_API_BASE` (default `http://localhost:8000`).
Copy `.env.example` to `.env` to override.

The app is **usable with no backend running.** The typed client (`src/api.ts`)
targets the real endpoints; when the server is unreachable (network error) the
data layer (`src/lib/store.tsx`) and auth layer (`src/lib/auth.tsx`) fall back to
an in-memory mock seeded from the reference prototype, and a "Demo mode" banner
is shown. As soon as the API responds, live data replaces the seed. Credential
rejections (401/403) are **not** masked by the fallback — only genuine
connectivity failures are.

## Roles & access model

JWT-based. On login the token is stored (`localStorage`) and its `role` claim is
decoded (`src/lib/jwt.ts`). In offline demo mode a token is minted locally from
the role picked on the login screen; a real server token's claim always wins.
Suspended users are blocked at sign-in with a support message (FR-1.3).

| Role (`role` claim) | Nav | Extra capabilities |
|---|---|---|
| `ANALYST` (Colour Analyst) | Dashboard, Analyses, Start | run + submit; pending items read-only |
| `EXPERT` (Colour Analysis Expert) | + Settings | approve / correct / rerun; prompt management |
| `ADMIN` | + Admin | engine, models, users, memory, training |
| `VIEWER` | Dashboard, Analyses, Start | read-only (seeded, suspended in demo) |

Routes are guarded (`RequireAuth`, `RequireRole` in `src/App.tsx`). Model
selection is platform-wide Admin config — never a per-analysis choice.

## Pages

| Route | Page | FR |
|---|---|---|
| `/login` | Login (email/password, demo-role picker, suspended message) | FR-1 |
| `/` | Dashboard — role-scoped (Analyst / Expert / Admin variants) | FR-8 |
| `/start` | Start Analysis — upload + preview, hair (12 values) & Fitzpatrick (I–VI) selectors, notes, **live Level 1 ∩ Level 2 rule-out preview**, engine banner, pipeline stepper | FR-2 |
| `/analyses` | Analyses list — columns, search, filters (status/palette/model/date), sortable, pagination 50/page, CSV export | FR-3 |
| `/analyses/:id` | Analysis detail — 10-palette overlay grid (recommended highlighted, click-to-zoom, compare any two), result panel, model votes + consensus, evidence a–d with cited criteria | FR-4 |
| `/analyses/:id/review` | Review / Correct / Rerun — approve+comments, correct (constrained to candidate set), prompt influence, rerun log with memory HIT/MISS | FR-5 |
| `/settings` | Prompts — version list w/ accuracy, immutable save → vN+1, activate, diff view | FR-6 |
| `/admin` | Admin console — execution mode, model registry, users, metrics, correction-memory (view/expire), training jobs | FR-7 |

## Domain constants (client-side, authoritative-mirroring)

- `src/palettes.ts` — the ten palettes, swatches, families, `FLOWS_BY_SEASON`.
- `src/ruleouts.ts` — `HAIR_COLOURS` (12), `FITZPATRICK` (I–VI), `level1`,
  `level2`, `candidateSet` (§5.1/§5.2), `DRAPE_CRITERIA` (the seven §5.4 labels).
- `src/types.ts` — output contract shape (§5.5), roles, statuses.

## FR coverage

**Implemented (UI + wiring + client-side logic):** FR-1 (login, role nav,
suspended), FR-2 (all inputs, live rule-out preview, empty-set blocks Run with
`CONFLICTING_INPUTS`, engine banner, stepper), FR-3 (table, search, filters,
sort, pagination, CSV), FR-4 (overlay grid, zoom, compare, result panel, votes,
evidence a–d with criteria), FR-5 (approve/correct constrained to candidate set,
outside-set blocked, prompt influence, rerun log with HIT/MISS), FR-6 (version
history, immutable save, activate, diff), FR-7 (engine mode/strategy, model
registry enable/disable/weight, user invite/role/suspend, metrics, memory
view/expire, training jobs), FR-8 (role-scoped dashboards).

**Stubbed / placeholder (needs the live backend or real assets):**

- **Overlay composites** are placeholders — an SVG face on each palette's swatch
  gradient (`src/components/PaletteViz.tsx`). Real face-cropped composites are
  produced server-side by the Overlay Composer; a demo skin-tone selector stands
  in. Auto face-detection / crop-adjustment (FR-2.2) is not performed client-side.
- **Pipeline run** animates the real stages but the result is a deterministic
  local pick within the candidate set (stands in for the model pipeline). With a
  live API, `POST /analyses` replaces this.
- **Report email / PDF** (FR-4.5): email is a toast; PDF uses `window.print()`
  with a print-friendly layout rather than a templated branded document.
- **Metrics** on dashboards/admin mix live-derived values (from seeded analyses)
  with representative figures; `GET /metrics/{scope}` is defined in the client
  but the panels do not yet bind every series to it.
- **Idempotency-Key / SSE stepper** (§11) and multipart upload are wired in the
  client surface but exercised only against a real server.

Everything mutable (approve, correct, rerun, prompt versions, engine/model/user
changes, memory expiry) updates local state immediately so flows are fully
demoable offline, and best-effort writes to the API when a server is present.
