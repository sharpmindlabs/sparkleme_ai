// The ten SparkleMe palettes (Functional Spec §1.1). Keys are the canonical
// palette identifiers used by the engine and across the UI.

export interface PaletteInfo {
  /** Reference swatches from the expert workbook (§1.1). */
  swatches: string[];
  /** Parent home season(s). Flow palettes list two. */
  family: string;
  /** Undertone description. */
  undertone: string;
}

export const PALETTES: Record<string, PaletteInfo> = {
  "True Winter": { swatches: ["#66008D", "#000000", "#A50046", "#FF00A0", "#000AC6"], family: "Winter", undertone: "Cool" },
  "True Summer": { swatches: ["#875F96", "#B7AFB0", "#AA415F", "#DB8FA6", "#6472A0"], family: "Summer", undertone: "Cool" },
  "True Spring": { swatches: ["#FCFB58", "#E19673", "#FF304B", "#FF967D", "#4EFD67"], family: "Spring", undertone: "Warm" },
  "True Autumn": { swatches: ["#9B710B", "#4B2819", "#932516", "#F24C03", "#265E25"], family: "Autumn", undertone: "Warm" },
  Cool: { swatches: ["#8535A3", "#464141", "#B9215C", "#ED4D9A", "#3D429A"], family: "Winter / Summer", undertone: "Cool" },
  Warm: { swatches: ["#E9BA47", "#713F29", "#F42E24", "#DC6F39", "#5BBA4F"], family: "Autumn / Spring", undertone: "Warm" },
  Deep: { swatches: ["#551455", "#3C141E", "#8C002F", "#6E002D", "#073342"], family: "Winter / Autumn", undertone: "Leans cool" },
  Bright: { swatches: ["#F000FA", "#46000F", "#D20046", "#FF3F7F", "#00AAAA"], family: "Spring / Winter", undertone: "Leans warm" },
  Light: { swatches: ["#E4DBD3", "#E13750", "#FAADAD", "#82D9DC"], family: "Spring / Summer", undertone: "Leans warm" },
  Muted: { swatches: ["#5A4646", "#A53C50", "#CD737D", "#3A5D68"], family: "Autumn / Summer", undertone: "Leans cool" },
};

/** Canonical order for grids and confusion axes. */
export const PALETTE_ORDER: string[] = [
  "True Winter",
  "True Summer",
  "True Spring",
  "True Autumn",
  "Cool",
  "Warm",
  "Deep",
  "Bright",
  "Light",
  "Muted",
];

/** Primary swatch hex per palette (first swatch). Retained for compatibility. */
export const PALETTE_HEX: Record<string, string> = Object.fromEntries(
  PALETTE_ORDER.map((p) => [p, PALETTES[p].swatches[0]]),
);

export function paletteHex(name: string | null | undefined): string | null {
  if (!name) return null;
  return PALETTE_HEX[name] ?? null;
}

/** Valid flows per home season (§1.1). */
export const FLOWS_BY_SEASON: Record<string, string[]> = {
  Winter: ["True Winter", "Cool", "Deep", "Bright"],
  Summer: ["True Summer", "Cool", "Light", "Muted"],
  Spring: ["True Spring", "Warm", "Light", "Bright"],
  Autumn: ["True Autumn", "Warm", "Deep", "Muted"],
};

/** CSS gradient built from a palette's swatches, for overlay-card backgrounds. */
export function paletteGradient(name: string): string {
  const sw = PALETTES[name]?.swatches ?? ["#888"];
  const seg = 100 / sw.length;
  const stops = sw.map((c, i) => `${c} ${i * seg}% ${(i + 1) * seg}%`).join(", ");
  return `linear-gradient(90deg, ${stops})`;
}
