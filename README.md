# SparkleMe AI

AI-powered **seasonal colour analysis**. SparkleMe AI productizes the CAMS
(Colour Analysis Method System) expert methodology into a repeatable,
auditable pipeline: it takes a person's photos plus a few self-reported
inputs, determines their colour **palette** (one of 10 seasons), and produces
a personalized report.

The product ships **analyst-assist first** (AI proposes a palette with a full
reasoning trail; a human reviews and finalizes), architected so the same
pipeline can move to self-serve once accuracy is proven against the
regression case set.

## The method (CAMS), in brief

A deterministic orchestrator sequences an expert procedure — it does not
"classify". A palette wins only if it improves whole-face physiology **while
preserving authentic complexion** (never for structure, smoothness,
brightness, or warmth alone).

1. **Reset & evidence** — every case starts blind; hair colour / Fitzpatrick
   used only if provided.
2. **Pre-filter** — hair, Fitzpatrick, earthy, and flush signals eliminate
   impossible palettes.
3. **Phase 2A** — observe each Home Season (Winter/Summer/Spring/Autumn)
   independently on the 7 CAMS checks + audits (no ranking yet).
4. **Phase 2B** — six pairwise Home-Season comparisons with reset +
   reverse-order verification.
5. **Phase 3** — round-robin the flow palettes within the chosen season.
6. **Final verification** — audits + anti-bias gates before the result.

**The 10 palettes:** True Winter, True Summer, True Spring, True Autumn, Cool,
Warm, Bright, Light, Deep, Muted.

## Repository status

🚧 Early scaffolding. The CAMS source documents (expert knowledge base +
base prompts) are being ingested into `data/rulebook/source_docs/` as the
build's source of truth. Architecture and build plan are defined; module
implementation follows.

## Layout (planned)

```
apps/web/         Next.js + TypeScript — intake, analyst review, report
services/engine/  Python + FastAPI — CAMS pipeline, CV + LLM vision, evals
packages/shared/  Cross-language types & contracts
data/rulebook/    CAMS source docs + compiled rules config
data/palettes/    10-palette swatch definitions
fixtures/         Sample cases (images wired via provider interface)
```
