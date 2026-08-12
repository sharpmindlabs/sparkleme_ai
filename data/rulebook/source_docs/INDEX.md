# CAMS Source Document Index

Digest of all ingested CAMS (Colour Analysis Methodology System) source documents. The corpus is a single methodology expressed many times over; most knowledge-base files are re-formats of the same core content (identity, 10-palette system, Eyes to Person to Colour hierarchy, 7 CAMS checks, Home Season then Flow workflow, ~14 named audits, anti-bias safeguards). The genuinely distinctive material is noted in the redundancy column.

## Knowledge Base Docs (`knowledge_base/`)

| File | Summary | Most engine-relevant content | Distinct vs redundant |
|---|---|---|---|
| 01_CAMS_v18_Final_Training_Corpus_Master | Consolidated "master upload" corpus (v18). Full methodology in one file: identity, palettes, hierarchy, 7 checks, workflow, audits, comparisons, safeguards, validation. | Complete rulebook + master transfer checklist; the single best all-in-one reference. | Consolidation of everything; content redundant with v15/v8/v1 but most complete. |
| 02_CAMS_v15_Single_Upload_Version | Consolidated master training file (v15), the designated "primary" load per the indices. | Full methodology + anti-bias system + final decision rules. | Near-duplicate of v18/v8; slightly leaner. |
| 02a_CAMS_v8_Full_Implementation_Bundle | Implementation bundle (v8) combining methodology + prompt stack + failure prevention. | 7-layer prompt stack; Effect Source Separation (A/B/C classification). | Redundant methodology; prompt-stack list overlaps v7. |
| 02b_CAMS_v1_Project_Methodology_Export | Original foundational methodology layer (v1) — "what the AI must know." | Core scope, evidence rules, interpretation principles, global audit framework. | Foundational/original; leaner audit set than later versions. |
| 03_CAMS_v2_Encyclopedic_Training_Manual | Expanded encyclopedic manual (v2). Adds bridge validations and per-boundary detail. | **Bridge validations** (Winter-Summer-Cool, Spring-Warm-Autumn, three-way) and boundary knowledge. | Distinct: bridge-validation section richer than most. |
| 04_CAMS_v3_Full_Rule_Encyclopedia | Rule encyclopedia (v3) with a full per-audit and per-Flow-boundary breakdown. | **Complete audit encyclopedia** with triggers; every Flow pair (True X vs bridge) with its named audit. | Distinct: most detailed audit-per-boundary mapping. |
| 05_CAMS_v4_Operational_Rulebook | Operational rulebook (v4). Methodology recast as numbered executable rules. | **Rule IDs CAMS-001..062** grouped (core/workflow/checks/audits/flow/finalization). | Distinct format: the only ID'd rule spec; good for rule-engine ingestion. |
| 06_CAMS_v5_Comparison_Matrix_and_Audit_Library | Comparison matrix (v5). Per-comparison conflict + required audits + invalid shortcuts. | **Home Season comparison matrix** and cross-comparison rules (Bright vs Cool, Cool vs Deep, etc.); audit template. | Distinct: comparison-level intelligence and cross-pairings. |
| 07_CAMS_v13_Boundary_Encyclopedia | Boundary encyclopedia (v13). Deep per-boundary conflict reasoning. | Every Home + Flow + cross boundary with primary conflict, required audits, invalid shortcuts. | Overlaps v5 heavily; boundary reasoning slightly deeper. |
| 08_CAMS_v14_Complete_Audit_Manual | Complete audit manual (v14). Each audit fully specified. | **16 numbered audits** with purpose/trigger/questions/positive/negative/decision impact. | Distinct: the definitive audit spec (structured fields). |
| 09a_CAMS_v6_Decision_Trees_and_Execution_Flowcharts | Execution flowcharts (v6). Methodology as sequential decision trees. | **11 decision-tree flows** (master execution, comparison, physiology, shadow, colour, luminosity, suppression, home, flow, anti-bias, final). | Distinct: only procedural/flowchart representation. |
| 10_CAMS_v7_Complete_Prompt_Package | Prompt package (v7). Ready-to-use agent instruction prompts. | **9 prompts** (master system, observation, comparison, home, flow, audit controller, anti-bias, report, self-audit). | Distinct: directly usable prompt text. |
| 11_CAMS_v11_Complete_Agent_Architecture | Multi-agent architecture (v11). Roles and information flow for a 7-agent pipeline. | **Agent orchestration** (Orchestrator, Observation, Evaluation, Comparison, Audit Controller, Decision Validation, Report) + escalation rules. | Distinct: system/agent design. |
| 11a_CAMS_v19_Failure_Mode_Encyclopedia | Failure-mode encyclopedia (v19). Catalog of reasoning failures + corrections. | Each failure -> why -> correction -> preventing audit; self-check questions. | Distinct: error-prevention framing. |
| 11b_CAMS_v20_Reasoning_Principles_Manual | Reasoning principles manual (v20). The deeper judgment philosophy. | 13 principles (physiology-before-aesthetics, effect-source, person-first, magnitude, identity preservation, health-vs-appearance, expert distinctions). | Distinct: philosophy/"why" layer. |
| 11c_CAMS_v21_Evolution_and_Refinement_Log | Evolution/refinement log (v21). Rationale and history of each safeguard. | Why each per-season safeguard and audit was created; methodology-protection + future-refinement framework. | Distinct: change-rationale/governance. |
| 11d_CAMS_v22_Expert_Decision_Notes | Expert decision notes (v22). Advanced judgment for close/ambiguous calls. | Definition-vs-shadow, smoothness-vs-suppression, illusion prevention, close-decision framework, preferred decision language. | Distinct: expert tie-breaking + language. |
| 12_CAMS_v12_Evaluation_and_Calibration_Framework | Evaluation/calibration framework (v12). How to test a CAMS AI post-implementation. | Workflow/check/audit/bias/consistency/regression **test cases**; release checklist. | Distinct: QA/validation. |
| 12a_CAMS_v23_Calibration_and_Future_Learning | Calibration + future-learning governance (v23). Safe vs prohibited learning. | Approved vs prohibited learning; calibration review process; change control; regression protection. | Distinct: governance (complements v12). |
| 12b_CAMS_v24_Master_Glossary | Master glossary (v24). Canonical term definitions. | **Definitions** for physiological improvement, palette-created effect, grey veil, suppression, luminosity, grounding, each audit, etc. | Distinct: terminology reference. |
| 13_CAMS_v9_Full_Training_Corpus_Format | Retrieval corpus format (v9). Methodology as tagged knowledge cards. | **Knowledge cards** (CAMS-CORE/CHECK/AUDIT/comparison/workflow) with ID/trigger/forbidden/decision-impact. | Distinct format: RAG/retrieval units. |
| 14_CAMS_v10_Master_Dataset_Schema | Dataset schema (v10). Storage/governance architecture. | **6-layer knowledge architecture**, object models, workflow state machine (CASE_CREATED..COMPLETED), retrieval priority. | Distinct: data model/schema. |
| 15_CAMS_v16_Structured_RAG_JSON_Package | Structured RAG/JSON package (v16). Machine-ingestion object model. | Knowledge/audit/comparison/prompt object fields, retrieval metadata tags, relationship mapping. | Distinct format; overlaps v9/v10 (technical). |
| 16_CAMS_v17_Master_Archive_and_Transfer_Index | Transfer index (v17). Recommended load order + ownership map. | Loading sequence; knowledge-ownership map; transfer verification checklist. | Distinct: meta/organizational (no new rules). |
| 17_CAMS_v25_Final_Package_Index_and_Upload_Checklist | Final package index (v25). Full 24-file inventory + load order + upload checklist. | Complete file inventory and configuration instructions. | Distinct: meta/organizational; superset index of v17. |

## Base Prompts (`base_prompts/`)

These are the actual operational "blind test case" prompts run against client drape images (10-palette only; no methodology theory). They are the practical engine drivers and differ meaningfully by date.

| File | Summary | Most engine-relevant content | Distinct vs redundant |
|---|---|---|---|
| Chat_Base_Prompt_2026-07-26 | Fullest baseline. Includes eligibility filters + exhaustive mandatory audits. | **Phase 1 Fitzpatrick/Hair eligibility filters**; per-boundary mandatory audits; per-Flow-palette audits (Cool/Light/Bright/Warm/Deep/Muted); full Report format. | Most complete/strict variant; distinct eligibility + boundary-audit stack. |
| Chat_Base_Prompt_2026-07-28 | "Stable Baseline." Leaner, no eligibility phase; supplementary audits only when checks are too close. | First-5-checks-are-primary rule; CAMS accumulation/independent-evidence rules; Bridge Palette Identity Preservation Audit; anti-correction-bias rule. | Distinct: de-emphasizes eligibility; adds accumulation + anti-overcorrection nuance. |
| Chat_Base_Prompt_2026-08-04 | Latest. Adds explicit **Phase 2A independent Home Season profiles** (observe-only, no ranking) before 2B pairwise. | 2A independent profiling + 5 named audits per season; strict pairwise reset protocol (up to 3 fresh passes); Final Decision Rule. | Distinct: strongest neutrality/observation-isolation discipline; drops eligibility filters. |

## Notes on redundancy

- **Core methodology is repeated ~15 times.** Files 01/02/02a/02b/03/04/07 restate the same identity + palettes + hierarchy + 7 checks + workflow + audits with different framings (corpus, rulebook, encyclopedia, boundary).
- **Genuinely distinct engine material** lives in: v14 (audit spec), v6 (decision trees), v7 (prompts), v11 (agent design), v4 (numbered rules), v5/v13 (comparison/boundary detail), v24 (glossary), v9/v10/v16 (retrieval/schema), v19-v23 (failure modes, philosophy, evolution, expert notes, calibration).
- **v17 and v25** are pure organizational indices (no new rules).
- **The three base prompts are the real operational layer** and evolve: 07-26 (eligibility-heavy, exhaustive audits) → 07-28 (leaner "stable baseline" + accumulation rules) → 08-04 (independent per-season profiling added, eligibility dropped).
