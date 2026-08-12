// Deterministic rule-out tables reproduced client-side for the live preview
// (Functional Spec §5.1 Level 1 hair, §5.2 Level 2 Fitzpatrick). These MUST
// match the server rule engine; they never depend on model output.

import { PALETTE_ORDER } from "./palettes";

/** The 12 canonical hair-colour values at age 17–20 (§5.1 / FR-2.3). */
export const HAIR_COLOURS = [
  "Dark Blonde",
  "Blonde",
  "Light Blonde",
  "Very Light Blonde",
  "Lightest Blonde",
  "Light Brown",
  "Brown",
  "Dark Brown",
  "Darkest Brown",
  "Black",
  "Obvious Red Hair",
  "I Do Not Know",
] as const;

export type HairColour = (typeof HAIR_COLOURS)[number];

/** Fitzpatrick types with short descriptions (FR-2.3). */
export const FITZPATRICK: { type: FitzType; label: string }[] = [
  { type: "I", label: "Always burns, never tans — very fair, often freckled" },
  { type: "II", label: "Usually burns, tans minimally — fair" },
  { type: "III", label: "Sometimes burns, tans gradually — medium" },
  { type: "IV", label: "Rarely burns, tans easily — olive / light brown" },
  { type: "V", label: "Very rarely burns, tans darkly — brown" },
  { type: "VI", label: "Never burns, deeply pigmented — dark brown / black" },
];

export type FitzType = "I" | "II" | "III" | "IV" | "V" | "VI";

const BLONDES = [
  "Dark Blonde",
  "Blonde",
  "Light Blonde",
  "Very Light Blonde",
  "Lightest Blonde",
];

/** Level 1 — remaining possibilities given natural hair colour at 17–20. */
export function level1(hair: string): string[] {
  if (BLONDES.includes(hair)) return ["True Spring", "True Summer", "Light"];
  if (hair === "Light Brown") return ["True Spring", "True Summer", "Light", "Warm"];
  if (hair === "Brown")
    return ["True Autumn", "True Spring", "True Summer", "Warm", "Muted"];
  if (["Dark Brown", "Darkest Brown", "Black"].includes(hair))
    return PALETTE_ORDER.filter((p) => p !== "Light");
  if (hair === "Obvious Red Hair") return ["True Spring", "True Autumn", "Warm"];
  return [...PALETTE_ORDER]; // "I Do Not Know" — all ten
}

/** Level 2 — remaining possibilities given Fitzpatrick type. */
export function level2(fitz: string): string[] {
  if (["V", "VI"].includes(fitz))
    return PALETTE_ORDER.filter(
      (p) => !["True Summer", "True Spring", "Light"].includes(p),
    );
  if (["III", "IV"].includes(fitz)) return PALETTE_ORDER.filter((p) => p !== "Light");
  return [...PALETTE_ORDER]; // I, II — all ten
}

/**
 * Candidate set = Level 1 ∩ Level 2 (§5.2). Order follows PALETTE_ORDER.
 * Empty set → CONFLICTING_INPUTS (Run must be blocked in the UI).
 */
export function candidateSet(hair: string, fitz: string): string[] {
  const a = level1(hair);
  const b = level2(fitz);
  return PALETTE_ORDER.filter((p) => a.includes(p) && b.includes(p));
}

/** The seven drape-comparison judgment criteria (§5.4), 1-indexed. */
export const DRAPE_CRITERIA: string[] = [
  "Facial details emphasized vs diminished",
  "Skin colour unhealthy / grayish / jaundiced vs healthy / rosy / golden glow",
  "Skin consistency patchy vs smooth",
  "Jaw line dropped vs lifted",
  "Eyes dull vs sparkling",
  "Focus pulled to jawline vs up to eyes",
  "Balance disconnected vs harmonious",
];

/** Human label for a criteria index (1-based). */
export function criterionLabel(n: number): string {
  return DRAPE_CRITERIA[n - 1] ?? `Criterion ${n}`;
}
