# Distilled Refinements — from Carol's 31-Case Refinement Trail

Source: `data/goldenset/refinement_trail.md`. Each row is a pattern that **recurred** across
the per-case corrections Carol used to steer the AI to the right answer on a *later* pass. In
the consolidated first-pass prompt these are turned into **standing rules (R1–R14)** that run
by default, so the verdict is correct on pass one.

The trail has 31 client entries. **12** are non-specific ("needed a rule update / rule
adjustment / new rule, then re-run": clients 4281, 4216, 4192, 4191, 6562, 6627, 6727, 5218,
5205, 5203, 4225, 6755) — these confirm the meta-pattern that a standing rule was missing
(→ R12) but name no new technique. The remaining **19** carry explicit instructions, distilled
below. Counts are the number of distinct clients whose explicit prompt shows the pattern.

| # | Standing rule | Recurring refinement pattern | Cases (count) | Client IDs |
|---|---|---|---|---|
| **R1** | Independent, unbiased, CAMS-only audit on every comparison | "independent audit / no bias / no benchmark / cams only" — the dominant phrase in the trail | **14** | 4363, 4355, 6761, 6072, 4208, 4190, 4195, 6526, 6540, 6560, 6622, 4336, 6586, 6757 |
| **R2** | Reverse the audit (fresh B→A re-check, build the loser's case) | "run the audit in reverse / did you do the reverse analysis" | **2 explicit + base rule** | 6757 (explicit); base prompts mandate it; reinforced by "why did you change your mind after audit" (6761, 6754) |
| **R3** | No True-palette bias (zero incumbent advantage for True) | "no bias to true winter/true summer", "did you put bias on true winter? re-run" | **4** | 6072, 4208, 4336, 4190 |
| **R4** | Home-Season **chain rules** (the bridge must carry the season) | "if summer>winter then cool>winter …"; "for Summer to win over Autumn, Muted must beat True Autumn"; "if cool beats summer, summer can't beat winter" | **3 (highest-leverage)** | 808, 4355, 6560 |
| **R5** | Luminosity audit — auto-run for Spring / Light / Bright | "luminosity check / intrinsic luminosity, openness, healthier complexion organization" | **6** | 4363, 6761, 6560, 4336, 6540, 6586 |
| **R6** | Grey-veil & suppression audit — auto-run for Summer / Muted | "is it causing greyness and shadows / dulling and greying / suppression" | **6** | 4355, 6761, 4208, 6526, 4336, 5220 |
| **R7** | Warmth-source audit — auto-run for Spring vs Autumn / Warm (three-way) | "true autumn vs warm vs true spring, no benchmark"; "is autumn authentic and rich, natural colouring"; "muted vs warm" | **4** | 4190, 4355, 6761, 6560 |
| **R8** | "Healthier vs adds shadows/greyness" direct framing | "which adds shadows / greyness / white patches vs which is healthier complexion" | **5** | 4363, 4355, 6072, 6560, 6754 |
| **R9** | Power & presence only without shadow/drag (Deep/Bright) | "more power and presence, no bias"; "which is strongest" | **3** | 6072, 6560, 6754 |
| **R10** | Even-colour / smooth-skin / white-patch & patchiness audit | "even colouring across face, no shadows or white patches; reduces patchy complexion; blends uniformly" | **4** | 6072, 6526, 4336, 6560 |
| **R11** | Muted cross-check against True Summer and True Autumn | "when there is a muted result, double check the cross-check palettes"; "could this be a true autumn vs muted boundary" | **2** | 6505, 5220 |
| **R12** | Decide once — run all audits up front, don't flip after an audit | "why did you not get this correct the first time? update memory"; and the 12 "needed a rule update" cases | **3 explicit + 12 meta** | 6761, 6072, 6754 (explicit) + the 12 rule-update cases |
| **R13** | Runner-up must be a neighbouring palette; boundary wording only when genuine | "true summer is neighbouring palette, ok"; boundary-case acknowledgements | **4** | 4352, 5220, 6622, 4336 |
| **R14** | Ties carried forward with equal-weight flows (no forced winner) | "if winter/summer/cool tie, audit fully then look at flows with equal weighting to all flows" | **2** | 6560, 6622 |

## Notes on how these were turned into standing rules

- **R1 is the backbone.** It appears in nearly every explicit case, so "independent / no bias /
  no benchmark / CAMS-only" is stated once as global behaviour and re-asserted at each phase,
  rather than as a per-case add-on.
- **R4 (chain rules) is the single most under-applied check** in the trail — Carol repeatedly
  had to remind the model ("stop missing these checks"). It is elevated to a MANDATORY gate in
  Phase B and re-verified in Phase D, and the flow analogue ("Muted must beat True Autumn for
  Summer to win over Autumn") is folded in.
- **R5/R6/R7 are palette-triggered audits.** The base prompt (08-04) says "only the 7 CAMS
  checks" in pairwise; the trail shows these audits were needed anyway. Resolution: the seven
  checks remain the decision engine, and these three audits **auto-trigger by palette** (Spring
  family → luminosity; Summer/Muted → grey veil; Spring-vs-Autumn/Warm → warmth source) instead
  of "only when close," matching what actually made the answers correct.
- **R12 absorbs the 12 unlabeled "rule update" cases.** Their common signal is "a standing rule
  was missing, so the first pass was wrong." Baking R1–R14 in up front is the direct remedy;
  R12 states the discipline (all audits before committing) so the model does not reach a
  provisional answer and then reverse it.
