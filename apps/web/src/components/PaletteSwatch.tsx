import { paletteHex } from "../palettes";

interface Props {
  name: string | null | undefined;
  /** Show the palette name next to the swatch (default true). */
  label?: boolean;
  className?: string;
}

/** A small colour swatch + palette name. Falls back to a dashed chip for
 *  unknown / null palettes so nothing renders as a silent blank. */
export default function PaletteSwatch({ name, label = true, className = "" }: Props) {
  const hex = paletteHex(name);

  if (!name) {
    return (
      <span className={`inline-flex items-center gap-1.5 text-slate-400 ${className}`}>
        <span className="h-3.5 w-3.5 rounded-sm border border-dashed border-slate-300" />
        {label && <span className="text-sm">—</span>}
      </span>
    );
  }

  return (
    <span className={`inline-flex items-center gap-1.5 ${className}`}>
      <span
        className="h-3.5 w-3.5 shrink-0 rounded-sm border border-slate-300 shadow-sm"
        style={{ backgroundColor: hex ?? "transparent" }}
        title={hex ?? name}
        aria-hidden="true"
      />
      {label && <span className="text-sm text-slate-800">{name}</span>}
    </span>
  );
}
