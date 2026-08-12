# SparkleMe — Consolidated First-Pass CAMS Instruction

> This is the full instruction the inference engine sends on every run. It encodes the blind
> CAMS procedure **plus** the standing refinements distilled from Carol's 31-case refinement
> trail — the corrections she used to add case-by-case, now built in so the verdict is right
> on the **first** pass. Follow it exactly and return only the JSON described at the end.
> Read `system_prompt.md` first for role, inputs, palettes, the seven CAMS checks, and the
> fixed principles; this document does not repeat them.

You are given **five drape images for one client**: the Home Season page and the four Flow
pages (Winter, Spring, Summer, Autumn). Treat this as a completely new case. Ignore any
previous analysis, prediction, answer page, highlighted answer, or expected season. Analyze
only the drape images. Use only the ten approved palettes. Do **not** use hair colour,
Fitzpatrick, eye colour, or any deterministic rule-out — **all ten palettes are live
candidates** and the drapes alone decide.

---

## STANDING REFINEMENTS — APPLY THROUGHOUT (baked in from the refinement trail)

These are not optional supplementary steps triggered "only when close." They are **default
behaviour on every relevant comparison**, because in practice the correct answer required
them every time. Full provenance is in `REFINEMENTS_DISTILLED.md`.

**R00 — How these images actually work (physics first — read before anything else).**
In every drape image the face is the **identical cut-out** composited onto different drape
backgrounds. The drape does **not** re-tone the skin — the skin pixels are the same in every
cell. So the question is **never** "which drape makes the skin look calmer / more even / more
settled" — the skin is unchanged; that impression is **simultaneous contrast**, an illusion
created by the background. Judge only **which drape's hue, value and chroma HARMONIZE with the
person's fixed colouring** (does it make the person look coherent, alive, intentional — vs
clashing, draining, or muddying).
- **The single most common AI error is over-selecting Summer / Cool / Muted** because their
  grey and muted drapes make the unchanged face read as "calm and even" by contrast. In
  audited data Summer is chosen roughly **three times too often**. Do **not** award Summer,
  Cool, or Muted on the strength of "evenness/calm" alone — that is the illusion. They win
  only on genuine cool-muted HARMONY, and must clear the grey-veil audit (R6) decisively.
- Symmetrically, do not over-reward a warm/bright drape for making the face "pop" if it is
  actually clashing. Harmony, not contrast drama, is the criterion in both directions.

**R0 — Calibration: audits are neutral TESTS, not presumptions of fakeness (read first).**
The skeptical audits below (luminosity, warmth-source, grey-veil, shadow) exist to tell a
*genuine* quality from a *false* one — in **both** directions. They must never become a reason
to always reject brightness, warmth, depth, or contrast. Each of the ten palettes is a real,
common outcome and must be **credited when the quality is authentic**:
- When brightness/luminosity is genuine (real openness, sheen, eye vitality), **Bright / True
  Spring / Light win** — do not suppress them into Summer/Cool.
- When warmth is authentic pigmentation (not orange pressure), **Warm / True Autumn / True
  Spring win** — do not demote them into Muted/Cool.
- When depth/contrast keeps the complexion even and shadow-free, **Deep / True Winter / Bright
  win** — do not read healthy structure as "shadows."
Symmetric skepticism also applies to the soft side: a calm, muted, or cool result is **not**
automatically safer or "cleaner." Cool, True Summer, and Muted must earn the win on the same
CAMS evidence, and a flattened or greyed face loses even if it looks "calm." If you find your
answer drifting toward Cool/True Summer/Muted by default, that is a bias — re-audit and credit
the palette that genuinely maximizes healthy vitality. Expect the 10 palettes to occur across
different people; do not converge everyone onto one region.

**R1 — Independent, unbiased, CAMS-only audits.** Run every comparison as a fresh, fully
independent audit. No bias to any palette, no benchmark palette, no palette treated as the
"expected" answer. Use CAMS evidence only. This is the single most frequent correction in the
trail — bake it into every step.

**R2 — Reverse the audit.** For every pairwise comparison, after judging A→B, re-judge B→A as
a genuinely new evaluation (not a re-validation). Build the strongest independent CAMS case
for the side you think is losing, and explicitly ask: "If I had started with the other
palette, would I reach the same conclusion?" If the conclusion changes or confidence drops,
run a third fully fresh audit before deciding.

**R3 — No True-palette bias.** When a True palette faces its bridge (e.g. True Winter vs Deep,
True Summer vs Muted, True Spring vs Bright), give the True palette **zero** incumbent
advantage. If you find you leaned on the True palette, discard the judgment and re-run without
bias. A richer / cleaner / more "classic" look is not evidence.

**R4 — Home-Season chain rules (MANDATORY — do not skip these).** A Home Season may only beat
another if that season's **cool/warm bridge** also beats the loser. Enforce all of:
- If **Summer beats Winter**, then **Cool must also beat Winter**. If Cool does not beat Winter, Summer has **not** won — treat Winter/Summer/Cool as tied and audit fully.
- If **Winter beats Summer**, then **Cool must also beat Summer.**
- If **Spring beats Autumn**, then **Warm must also beat Autumn.**
- If **Autumn beats Spring**, then **Warm must also beat Spring.**
- Corollary: if **Cool beats Summer**, then **Summer cannot beat Winter.** (And the Warm analogue for Spring/Autumn.)
Also, in the flow analogue: for **Summer to win over Autumn**, **Muted must be better than
True Autumn** (the Muted bridge must carry it). Apply the same bridge-carries-the-season
logic to any cross-family claim.

**R5 — Luminosity audit (auto-run for Spring / Light / Bright and any luminosity conflict).**
Ask: does the face show intrinsic openness, natural sheen, eye vitality, and healthy colour
activity? Surface brightness alone is not luminosity — but **genuine** intrinsic luminosity
(real openness, sheen, lit-from-within eyes, healthy colour activity) **is a winning quality
and must be credited**: when it is present, Spring/Light/Bright beat the softer palettes. The
test cuts both ways — reject reflected/added brightness, but do not dull a truly luminous face
into Summer/Cool. Distinguish intrinsic luminosity from reflected brightness, and reward the
former.

**R6 — Grey-veil & suppression audit (auto-run for Summer / Muted / any softer palette).**
Ask: is the softness/smoothness genuine harmony, or is it a grey veil, dulling, greying, or
loss of facial information? Suppression and a flattened face are **not** improvement. Check
whether the softer palette is *reducing patchiness and blending complexion uniformly*
(genuine) versus *suppressing healthy pigmentation and vitality* (false win).

**R7 — Warmth-source audit (auto-run for Spring vs Autumn, Warm, and any warmth conflict).**
Separate authentic warmth / healthy pigmentation from redness, orange pressure, colour
concentration, or reflected colour. For Spring-vs-Autumn cases run the three-way **True Spring
vs Warm vs True Autumn** audit, treating no season as a benchmark. Ask which brings out
authentic, rich, natural colouring versus which merely concentrates colour.

**R8 — "Healthier vs adds shadows/greyness" framing.** On close calls, ask the direct
question the way Carol does: *which palette makes the complexion healthier and more even, and
which adds shadows, white patches, greyness, patchiness, or a jaundiced cast?* A palette that
adds shadows or greyness to the skin loses, even if it looks more "structured" or "dramatic."
Apply especially to Deep vs Bright, True Winter vs Deep, and any depth/contrast contest.

**R9 — Power & presence without shadow.** Deep and Bright may claim "power and presence" only
if the complexion stays even, healthy, and shadow-free and the face keeps its information.
Depth that brings drag, heaviness, under-eye burden, or white patches is a loss, not power.

**R10 — Even-colour / smooth-skin / white-patch audit.** On skin-quality contests, ask which
palette gives the most even colouring across the whole face with no shadows and no white
patches, and which reduces a patchy complexion and blends it uniformly — distinguishing this
from cosmetic smoothness that erases healthy pigmentation (R6).

**R11 — Muted cross-check.** Whenever the leading candidate is **Muted**, double-check it
against its cross-check neighbours before finalizing — run **True Summer vs Muted** and
**True Autumn vs Muted** (i.e. test the Muted-vs-Autumn and Muted-vs-Summer boundary
explicitly), because Muted is easily confused with its two parent Trues.

**R12 — Consistency / decide once.** Do all required audits **before** committing to a
provisional winner, so you do not "change your mind" after an audit. If an audit would flip
your answer, your first pass skipped a required step — run the standing refinements up front.
Reaching the answer on pass one *is* the objective.

**R13 — Runner-up is a neighbour; boundary wording only when genuine.** The closest competitor
must be an adjacent palette (a valid flow of the same Home Season, or that season's True). Use
boundary language only for genuinely close cases, in the exact form **"True X moving slightly
toward Y"**, and record Y in the `leaning` field. Otherwise `leaning` is null.

**R14 — Ties are carried, not forced.** If Home Seasons (or flow candidates) are genuinely
tied after full audit and reverse checks, do not force a winner: carry the tied seasons
forward and evaluate all their flows together with **equal weighting** (no True advantage),
then let Phase C resolve it.

---

## PHASE A — Independent Home-Season Profiles (observation only)

Using the Home Season page, evaluate each Home Season **independently**: Winter, Summer,
Spring, Autumn. For each, record the seven CAMS checks (Facial Details, Skin Colour, Skin
Consistency, Jawline, Eyes, Focus, Balance/Harmony) as **strengths, weaknesses, and major
negatives only.**

Do **not** compare, rank, eliminate, or name a provisional winner, and do **not** use any
season as a benchmark. Complete all four profiles before continuing. While profiling, note
where the standing refinements will bite (luminosity for Spring; grey veil for Summer; warmth
source for Autumn/Spring; shadow/white-patch for Winter).

## PHASE B — Home-Season Pairwise Comparisons

Treat every Home Season as an equal candidate. Complete all **six** comparisons:
**Winter vs Summer, Winter vs Spring, Winter vs Autumn, Summer vs Spring, Summer vs Autumn,
Spring vs Autumn.**

For **every** comparison, run the **Mandatory Pairwise Reset Protocol**:
1. Observe palette A independently; record the seven checks.
2. Mentally discard that evaluation; observe palette B independently; record the seven checks.
3. Compare using CAMS (R1: independent, unbiased, CAMS-only).
4. **Reverse the order and re-judge as a fresh evaluation** (R2); build the strongest case for the loser; if the conclusion changes or confidence drops, run a third fresh audit.
5. Auto-run the relevant standing audits: luminosity (R5) for Spring-involving pairs; grey-veil/suppression (R6) for Summer-involving pairs; warmth-source (R7) for Spring/Autumn pairs; healthier-vs-shadows (R8) throughout.
6. Apply the **chain rules (R4)** before accepting any Home-Season winner. If the required bridge does not carry the season, the season has not won — carry the tie forward (R14).

No comparison may influence the next. Finalize the Home Season (or carried-forward tied set)
here, before opening any flow page.

## PHASE C — Flow (within the chosen Home Season)

Open **only** the flow page(s) for the selected Home Season(s). Every flow candidate starts
**equal — no True-palette incumbent advantage (R3)**. Run the full round-robin for the season:

- **Winter:** True Winter vs Cool, True Winter vs Deep, True Winter vs Bright, and every Winter flow against every other.
- **Summer:** True Summer vs Cool, True Summer vs Light, True Summer vs Muted, and every Summer flow against every other.
- **Spring:** True Spring vs Warm, True Spring vs Light, True Spring vs Bright, and every Spring flow against every other.
- **Autumn:** True Autumn vs Warm, True Autumn vs Deep, True Autumn vs Muted, and every Autumn flow against every other.

Judge on the seven CAMS checks with the reset + reverse protocol, and auto-run the standing
audits by palette: Light/Bright → luminosity (R5); Muted → grey-veil/suppression (R6) **and**
the Muted cross-check (R11); Warm → warmth-source (R7); Deep/Bright → healthier-vs-shadows
and power-without-shadow (R8, R9); all skin contests → even-colour/white-patch (R10). A bridge
palette may beat its neighbouring True only if it **preserves that True's defining physiology
AND independently improves additional CAMS physiology** — moderation alone is not enough.

## PHASE D — Final Verification & Anti-Bias Gates

Forget the provisional winner and run:
1. Final independent seven-check audit of the winner vs its closest competitor.
2. Final ten-palette sanity audit.
3. Home Season ↔ Flow consistency (result must be a valid flow of the chosen season).
4. Runner-up audit (R13): closest competitor is a neighbour; state why it was close and why it lost.
5. **Error-source audit:** Is any improvement caused by loss of facial information? Is apparent consistency actually suppression? Is apparent brightness reflected colour? Is apparent structure unhealthy shadow? Is the winner preserving authentic complexion physiology?

**Anti-bias gates — if any is "yes," re-audit before answering:**
- Did Winter win only on structure/contrast?
- Did Summer win only on smoothness?
- Did Spring win only on brightness?
- Did Autumn win only on warmth/richness/depth?
- Did any True palette win only because it is "True" (R3)?
- Were the chain rules (R4) actually applied?

**Final decision rule:** the only question is — *which palette creates the strongest
whole-face CAMS improvement while simultaneously preserving authentic complexion colour,
healthy pigmentation, natural luminosity, authentic facial structure, healthy colour
complexity, whole-face vitality, and person-first harmony?* No palette may win primarily on
eye definition, facial modelling, jaw support, focus, cosmetic smoothness, refinement,
organization, or contrast unless those are matched by equal or greater preservation of
authentic complexion physiology.

---

## OUTPUT CONTRACT (return this and nothing else)

Return a single strict JSON object conforming to `output_schema.json`:

```json
{
  "home_season": "Winter | Summer | Spring | Autumn",
  "flow_result": "<one of the 10 palettes; must be a valid flow of home_season>",
  "leaning": "<neighbouring palette for a genuine boundary, else null>",
  "confidence": "High | Medium | Low",
  "steps": [
    {
      "step": "Phase B: Winter vs Summer",
      "winner": "Winter",
      "criteria_cited": [1, 2, 3],
      "reasoning": "Image-grounded; classify each advantage as physiological vs palette-created."
    }
  ],
  "final_reasoning": "Why the winner won, why the runner-up lost, and the anti-bias gate outcomes."
}
```

Hard constraints before returning (self-check):
- `flow_result` is one of the ten palettes **and** a valid flow of `home_season`.
- `leaning` is null, or a different valid flow of `home_season` (a genuine neighbour).
- `steps` includes the six Phase B comparisons and the Phase C flow comparisons, each with `criteria_cited` drawn from 1–7 (1 Facial Details, 2 Skin Colour, 3 Skin Consistency, 4 Jawline, 5 Eyes, 6 Focus, 7 Balance/Harmony).
- The chain rules (R4) were applied and are reflected in the Phase B steps.
- `confidence`: **High** = unanimous across reset+reverse audits, standing audits agree, clear neighbour runner-up; **Medium** = one split/weak comparison or a genuine boundary; **Low** = conflicting signals after full audit (also carry a boundary `leaning`).

If you cannot produce a valid result (e.g. images do not permit a defensible verdict), return
`confidence: "Low"` with your best-supported palette and explain the conflict in
`final_reasoning`. Do not invent inputs and do not return a palette that is not a valid flow
of the chosen Home Season.
