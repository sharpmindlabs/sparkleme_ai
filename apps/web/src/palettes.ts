// Palette -> swatch hex, per the UI spec. Keys match the engine's canonical
// palette identifiers (services/inference_engine/app/palettes.py).
export const PALETTE_HEX: Record<string, string> = {
  "True Winter": "#66008D",
  "True Summer": "#875F96",
  "True Spring": "#FCFB58",
  "True Autumn": "#9B710B",
  Cool: "#8535A3",
  Warm: "#E9BA47",
  Deep: "#551455",
  Bright: "#F000FA",
  Light: "#E4DBD3",
  Muted: "#5A4646",
};

// Order used for the confusion matrix axes.
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

export function paletteHex(name: string | null | undefined): string | null {
  if (!name) return null;
  return PALETTE_HEX[name] ?? null;
}
