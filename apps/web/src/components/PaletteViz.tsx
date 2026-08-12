// Placeholder overlay visuals. Real assets (face-cropped composites on each
// palette) are produced server-side by the Overlay Composer; here we stub the
// face as an SVG on top of the palette's swatch gradient. Noted in the README.

import { PALETTES, paletteGradient } from "../palettes";
import { cn } from "./ui";

/** Demo skin-tone keys → hex, used only for the placeholder face. */
export const SKIN_TONES: Record<string, string> = {
  a: "#f3d9c4",
  b: "#e8b98d",
  c: "#c98a5b",
  d: "#9c6238",
  e: "#6e4226",
  f: "#4a2c18",
};

export function FaceSvg({ tone, className }: { tone: string; className?: string }) {
  const fill = SKIN_TONES[tone] ?? SKIN_TONES.b;
  return (
    <svg viewBox="0 0 100 120" className={className} aria-hidden="true">
      <ellipse cx="50" cy="60" rx="38" ry="48" fill={fill} />
      <ellipse cx="36" cy="52" rx="5" ry="3.4" fill="#3a2a20" />
      <ellipse cx="64" cy="52" rx="5" ry="3.4" fill="#3a2a20" />
      <path d="M30 42 q6 -5 13 -2" stroke="#3a2a20" strokeWidth="2.4" fill="none" />
      <path d="M57 40 q7 -3 13 2" stroke="#3a2a20" strokeWidth="2.4" fill="none" />
      <path d="M50 55 q-3 12 0 16 q2 2 5 1" stroke="rgba(0,0,0,.25)" strokeWidth="2" fill="none" />
      <path d="M38 90 q12 9 24 0" stroke="#8c4a44" strokeWidth="3.4" fill="none" strokeLinecap="round" />
    </svg>
  );
}

export function SwatchRow({ palette, className }: { palette: string; className?: string }) {
  const sw = PALETTES[palette]?.swatches ?? [];
  return (
    <div className={cn("flex h-3.5 overflow-hidden rounded", className)}>
      {sw.map((c, i) => (
        <span key={i} className="flex-1" style={{ background: c }} />
      ))}
    </div>
  );
}

export function PaletteCard({
  palette,
  tone,
  recommended,
  onClick,
  selected,
}: {
  palette: string;
  tone: string;
  recommended?: boolean;
  selected?: boolean;
  onClick?: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={palette}
      className={cn(
        "relative flex aspect-[1/1.15] items-center justify-center overflow-hidden rounded-xl border-2 transition",
        recommended ? "border-amber-400 ring-2 ring-amber-300/50" : selected ? "border-teal-500 ring-2 ring-teal-200" : "border-transparent hover:border-white/70",
        onClick && "cursor-pointer",
      )}
      style={{ background: paletteGradient(palette) }}
    >
      {recommended && (
        <span className="absolute left-2 top-2 z-10 rounded-full bg-amber-400 px-2 py-0.5 text-[10px] font-bold text-amber-900">
          ★ RECOMMENDED
        </span>
      )}
      <FaceSvg tone={tone} className="z-[1] w-1/2 drop-shadow-md" />
      <span className="absolute inset-x-0 bottom-0 bg-black/60 px-1 py-1 text-center text-[11px] font-semibold text-white">
        {palette}
      </span>
    </button>
  );
}
