// Seed data + in-memory backend used when the real API (services/api) is not
// reachable, so the app is fully explorable offline. Mirrors the reference
// prototype and the Functional Spec data model.

import { PALETTES } from "../palettes";
import { candidateSet } from "../ruleouts";
import type {
  Analysis,
  Correction,
  EngineConfig,
  Evidence,
  HomeSeason,
  ModelConfig,
  ModelVote,
  PromptVersion,
  Role,
  TrainingJob,
  Undertone,
  User,
} from "../types";

export const MODELS_SEED: ModelConfig[] = [
  { id: "gpt5", name: "OpenAI GPT-5", type: "Commercial", enabled: true, weight: 1.0, accuracy: 93.1, latency: "3.2s", training: "Fine-tune API + prompt distillation" },
  { id: "claude", name: "Anthropic Claude", type: "Commercial", enabled: true, weight: 1.1, accuracy: 94.6, latency: "2.8s", training: "Prompt distillation + correction retrieval" },
  { id: "llama4", name: "Llama 4 70B (self-hosted)", type: "Open source", enabled: true, weight: 0.9, accuracy: 88.4, latency: "5.1s", training: "SFT + DPO weight updates" },
  { id: "kimi", name: "Kimi K2 (self-hosted)", type: "Open source", enabled: false, weight: 0.8, accuracy: 85.2, latency: "6.0s", training: "SFT + DPO weight updates" },
];

export const ENGINE_SEED: EngineConfig = {
  mode: "consensus",
  strategy: "Weighted majority vote",
  primary: "claude",
};

export function modelName(id: string): string {
  return MODELS_SEED.find((m) => m.id === id)?.name ?? id;
}

const PROMPT_A_SEED = `ROLE: Expert virtual colour analyst. Determine which one of ten palettes harmonizes with the person's natural colouring.

FIXED PRINCIPLES: Eyes are hypothesis only. Hair darkness at 17-20 is most reliable. Never trust user self-reported blushing. Deterministic rule-outs always win.

PHASE A: Validate image (face-only crop, even lighting, no makeup/colour cast).
PHASE B: Level 1 hair rule-outs; Level 2 Fitzpatrick rule-outs; intersect -> candidate set. Level 3 earthy check (Fitz I-IV, prior toward Autumn family). Level 4 flush/blush (Fitz I-III, image-derived, weak signal).
PHASE C: Eye hypothesis (non-binding).
PHASE D: Drape comparison - Step 1 Cool vs Warm, Step 2 home season, Step 3 flow. Judge 7 criteria: facial details, skin colour, skin consistency, jaw line, eyes, focus, balance.
PHASE E: Corroborate with skin characteristics per palette.
PHASE F: Output undertone, home season, flow, confidence, evidence a-d. Result MUST be within candidate set.`;

const PROMPT_B_SEED = `ROLE: Independent audit reviewer. Recompute all deterministic layers; re-judge all drape steps.

CHECK 1 input/crop integrity. CHECK 2 rule-out recomputation (result must be in candidate set - CRITICAL if not). CHECK 3 logic chain (undertone<->season<->flow). CHECK 4 evidence quality (>=3 of 7 criteria cited per step; eyes never eliminate). CHECK 5 skin corroboration. CHECK 6 completeness & confidence calibration. CHECK 7 repeatability (identical inputs -> identical result).

VERDICT: APPROVE / REVISE / REJECT. Escalate to human on empty candidate set, step 1-2 disagreement, or Low confidence.`;

function undertoneOf(palette: string): Undertone {
  const u = PALETTES[palette]?.undertone ?? "Cool";
  return u.toLowerCase().includes("warm") ? "Warm" : "Cool";
}

function evidenceFor(a: {
  hair: string;
  home_season: HomeSeason | null;
  undertone: Undertone | null;
  result: string;
  candidate_set: string[];
}): Evidence {
  const eliminated = 10 - a.candidate_set.length;
  return {
    a_eyes: `Showed potential for ${a.home_season ?? "the home season"}; pattern noted, no season ruled out (hypothesis only).`,
    b_hair: `${a.hair} at 17–20 is consistent with ${a.result}; rule-outs eliminated ${eliminated} palette(s).`,
    c_skin: `Observed complexion matches the ${a.result} profile (skin-characteristics corroboration).`,
    d_drape_steps: [
      { step: 1, winner: a.undertone ?? "Cool", criteria_cited: [1, 2, 4], reasoning: `Cool vs Warm — column resolves to ${a.undertone}.` },
      { step: 2, winner: a.home_season ?? "Winter", criteria_cited: [2, 5, 7], reasoning: `Home season ${a.home_season}: healthy glow, eyes brighter, harmonious balance.` },
      { step: 3, winner: a.result, criteria_cited: [1, 2, 4, 5, 6, 7], reasoning: `Flow ${a.result}: details diminished, jaw lifted, focus drawn up to eyes.` },
    ],
  };
}

interface Seed {
  id: number;
  name: string;
  date: string;
  hair: string;
  fz: string;
  ai: string;
  status: Analysis["status"];
  expert: string | null;
  conf: number;
  tone: string;
  und: Undertone;
  season: HomeSeason;
  pv: string;
  models: string[];
  why: string;
  expertNote: string | null;
  notes?: string;
}

function mk(s: Seed): Analysis {
  const cands = candidateSet(s.hair, s.fz);
  const rec = s.expert ?? s.ai;
  const votes: ModelVote[] = s.models.map((m, i) => {
    // If expert corrected away from AI, show the last model dissenting toward AI.
    const dissent = i === s.models.length - 1 && s.expert && s.expert !== s.ai;
    return { model: m, vote: dissent ? s.ai : rec, raw: "structured drape result" };
  });
  return {
    id: s.id,
    client: s.name,
    date: s.date,
    hair: s.hair,
    fitzpatrick: s.fz,
    notes: s.notes,
    tone: s.tone,
    result_status: s.status === "Conflicting Inputs" ? "CONFLICTING_INPUTS" : s.status === "Needs Human Review" ? "NEEDS_HUMAN_REVIEW" : "OK",
    status: s.status,
    undertone: s.und,
    home_season: s.season,
    ai_result: s.ai,
    expert_result: s.expert,
    confidence: s.conf,
    candidate_set: cands,
    evidence: evidenceFor({ hair: s.hair, home_season: s.season, undertone: s.und, result: rec, candidate_set: cands }),
    model_votes: votes,
    prompt_version: s.pv,
    engine: { mode: ENGINE_SEED.mode, strategy: ENGINE_SEED.strategy, models: s.models },
    why: s.why,
    expert_note: s.expertNote,
  };
}

export const USERS_SEED: User[] = [
  { id: "u1", name: "Prabhu Balakrishnan", email: "prabhu.balakrishnan@resdevtax.com", role: "ADMIN", status: "Active" },
  { id: "u2", name: "Colour Expert", email: "colour.expert@sparkleme.app", role: "EXPERT", status: "Active" },
  { id: "u3", name: "Aisha Verma", email: "aisha.v@sparkleme.app", role: "ANALYST", status: "Active" },
  { id: "u4", name: "Ops Bot", email: "ops@sparkleme.app", role: "VIEWER", status: "Suspended" },
];

export function seedAnalyses(): Analysis[] {
  const raw: Seed[] = [
    { id: 1041, name: "Elena Marchetti", date: "2026-07-24", hair: "Blonde", fz: "II", ai: "True Summer", status: "Approved", expert: "True Summer", conf: 94, tone: "a", und: "Cool", season: "Summer", pv: "v1.3", models: ["claude", "gpt5", "llama4"], why: "Muted complexion, rose-ivory; taupe freckles visible.", expertNote: "Expert: agree — classic soft rose complexion. Approved." },
    { id: 1040, name: "Priya Nair", date: "2026-07-24", hair: "Black", fz: "IV", ai: "Deep", status: "Approved", expert: "Deep", conf: 91, tone: "c", und: "Cool", season: "Winter", pv: "v1.3", models: ["claude", "gpt5"], why: "Rich contrast; face lifts on deep column, greys on light.", expertNote: "Expert: correct. Deep confirmed on overlays." },
    { id: 1039, name: "Sofia Lindqvist", date: "2026-07-23", hair: "Light Blonde", fz: "I", ai: "True Spring", status: "Corrected", expert: "Light", conf: 88, tone: "a", und: "Warm", season: "Spring", pv: "v1.3", models: ["gpt5", "llama4"], why: "High cheek colour, translucent; blonde rule-outs applied.", expertNote: "Expert: overlays show softening on Light, True Spring too intense at jawline. Corrected to Light.", notes: "I flush easily; hair had golden tints; freckles across the cheeks." },
    { id: 1038, name: "Amara Okafor", date: "2026-07-22", hair: "Darkest Brown", fz: "VI", ai: "True Winter", status: "Approved", expert: "True Winter", conf: 96, tone: "f", und: "Cool", season: "Winter", pv: "v1.3", models: ["claude", "gpt5", "llama4"], why: "Cool black-brown skin, reflective quality; eyes sparkle on Winter column.", expertNote: "Expert: textbook True Winter. Approved." },
    { id: 1037, name: "Mei-Ling Chen", date: "2026-07-22", hair: "Dark Brown", fz: "III", ai: "Bright", status: "Pending Review", expert: null, conf: 83, tone: "b", und: "Warm", season: "Winter", pv: "v1.3", models: ["claude", "llama4"], why: "Winter common for background; bright column lifts focus to eyes.", expertNote: null },
    { id: 1036, name: "Ciara O'Brien", date: "2026-07-21", hair: "Obvious Red Hair", fz: "II", ai: "True Autumn", status: "Approved", expert: "True Autumn", conf: 95, tone: "a", und: "Warm", season: "Autumn", pv: "v1.2", models: ["claude", "gpt5"], why: "Red-orange-brown freckling dense; earthy check strongly positive.", expertNote: "Expert: unmistakable True Autumn." },
    { id: 1035, name: "Fatima Al-Rashid", date: "2026-07-20", hair: "Dark Brown", fz: "IV", ai: "Muted", status: "Pending Review", expert: null, conf: 79, tone: "c", und: "Cool", season: "Summer", pv: "v1.2", models: ["gpt5", "llama4"], why: "Split at step 3 between Muted and Cool; melasma noted.", expertNote: null },
    { id: 1034, name: "Johan Petersen", date: "2026-07-19", hair: "Light Brown", fz: "II", ai: "True Summer", status: "Corrected", expert: "True Spring", conf: 81, tone: "a", und: "Warm", season: "Spring", pv: "v1.2", models: ["llama4"], why: "Single model run; step 1 judged cool.", expertNote: "Expert: undertone wrong — jaw drops on cool column. Peaches & cream skin. Corrected to True Spring; correction memory updated." },
    { id: 1033, name: "Rosa Delgado", date: "2026-07-18", hair: "Brown", fz: "III", ai: "Warm", status: "Approved", expert: "Warm", conf: 90, tone: "b", und: "Warm", season: "Autumn", pv: "v1.2", models: ["claude", "gpt5", "llama4"], why: "Golden beige; blend of Autumn/Spring characteristics.", expertNote: "Expert: agree with Warm." },
    { id: 1032, name: "Yuki Tanaka", date: "2026-07-17", hair: "Black", fz: "III", ai: "True Winter", status: "Needs Human Review", expert: null, conf: 58, tone: "b", und: "Cool", season: "Winter", pv: "v1.1", models: ["gpt5"], why: "Low confidence: split drape at step 2; escalated per audit rules.", expertNote: null },
    { id: 1031, name: "Grace Mwangi", date: "2026-07-16", hair: "Black", fz: "V", ai: "True Autumn", status: "Approved", expert: "True Autumn", conf: 92, tone: "e", und: "Warm", season: "Autumn", pv: "v1.1", models: ["claude", "llama4"], why: "Golden black complexion; V/VI rule-outs applied.", expertNote: "Expert: approved with comments — beautiful harmony on autumn column." },
    { id: 1030, name: "Hannah Weiss", date: "2026-07-15", hair: "Very Light Blonde", fz: "I", ai: "Light", status: "Approved", expert: "Light", conf: 89, tone: "a", und: "Warm", season: "Spring", pv: "v1.1", models: ["claude", "gpt5"], why: "Only 3 candidates after hair rule-out; light column diminishes details.", expertNote: "Expert: agree." },
  ];
  return raw.map(mk);
}

export function seedCorrections(): Correction[] {
  return [
    { id: 1039, palette: "Light", note: "True Spring too intense at jawline; Light softens details.", date: "2026-07-23", by: "colour.expert@sparkleme.app" },
    { id: 1034, palette: "True Spring", note: "Undertone warm not cool. Peaches & cream complexion.", date: "2026-07-19", by: "colour.expert@sparkleme.app" },
  ];
}

export function seedPrompts(): Record<"analysis" | "audit", PromptVersion[]> {
  return {
    analysis: [
      { version: "v1.0", date: "2026-05-02", author: "Prabhu", note: "Initial port of expert method", accuracy: 78, body: PROMPT_A_SEED.slice(0, 400) + "…", active: false },
      { version: "v1.1", date: "2026-05-28", author: "Colour Expert", note: "Added earthy-complexion guardrails (Level 3)", accuracy: 84, body: PROMPT_A_SEED.slice(0, 600) + "…", active: false },
      { version: "v1.2", date: "2026-06-20", author: "Colour Expert", note: "7-criteria drape rubric made explicit", accuracy: 91, body: PROMPT_A_SEED, active: false },
      { version: "v1.3", date: "2026-07-10", author: "Prabhu", note: "Hard constraint: result must be inside candidate set", accuracy: 96, body: PROMPT_A_SEED, active: true },
    ],
    audit: [
      { version: "v1.0", date: "2026-06-01", author: "Prabhu", note: "Initial audit checklist", accuracy: null, body: PROMPT_B_SEED.slice(0, 300) + "…", active: false },
      { version: "v1.1", date: "2026-07-10", author: "Colour Expert", note: "Added repeatability check 7 + escalation rules", accuracy: null, body: PROMPT_B_SEED, active: true },
    ],
  };
}

export function seedJobs(): TrainingJob[] {
  return [
    { id: "FT-2026-07-21", model: "Llama 4 70B", method: "DPO preference tuning", examples: 212, status: "Completed", delta: "+2.3% accuracy" },
    { id: "FT-2026-07-14", model: "Kimi K2", method: "SFT on corrected outputs", examples: 180, status: "Completed", delta: "+1.8% accuracy" },
    { id: "FT-2026-07-25", model: "OpenAI GPT-5", method: "Fine-tune API job", examples: 236, status: "Running", delta: "—" },
    { id: "RT-continuous", model: "All models", method: "Real-time correction memory (instant layer)", examples: 2, status: "Live", delta: "100% on reruns" },
  ];
}

/** Demo users the login screen can impersonate when offline. */
export const DEMO_LOGINS: { role: Role; name: string; email: string }[] = [
  { role: "ADMIN", name: "Prabhu Balakrishnan", email: "prabhu.balakrishnan@resdevtax.com" },
  { role: "EXPERT", name: "Colour Expert", email: "colour.expert@sparkleme.app" },
  { role: "ANALYST", name: "Aisha Verma", email: "aisha.v@sparkleme.app" },
];

export { evidenceFor, undertoneOf };
