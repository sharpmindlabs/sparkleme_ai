import type { BatchSummary } from "../types";
import { PALETTE_ORDER } from "../palettes";
import PaletteSwatch from "./PaletteSwatch";

interface Props {
  confusion: BatchSummary["confusion"];
}

/** Compact Carol-primary -> predicted matrix. Rows = Carol's ground-truth
 *  primary palette, columns = what the model predicted. The diagonal is
 *  tinted green (agreement); off-diagonal cells are amber-tinted by weight so
 *  boundary confusions (e.g. True Summer ↔ Muted) stand out. */
export default function ConfusionView({ confusion }: Props) {
  const rows = PALETTE_ORDER.filter((p) => confusion[p]);
  if (rows.length === 0) {
    return (
      <p className="text-sm text-slate-500">
        No confusion data yet — run a batch with ground-truth cases.
      </p>
    );
  }

  // Columns: union of every predicted palette seen, kept in canonical order.
  const predictedSeen = new Set<string>();
  for (const r of rows) {
    for (const p of Object.keys(confusion[r])) predictedSeen.add(p);
  }
  const cols = PALETTE_ORDER.filter((p) => predictedSeen.has(p));
  // Any predicted labels not in the canonical list (defensive).
  for (const p of predictedSeen) {
    if (!PALETTE_ORDER.includes(p)) cols.push(p);
  }

  const maxCell = Math.max(
    1,
    ...rows.flatMap((r) => cols.map((c) => confusion[r][c] ?? 0)),
  );

  return (
    <div className="overflow-x-auto">
      <table className="border-collapse text-sm">
        <thead>
          <tr>
            <th className="sticky left-0 z-10 bg-white p-2 text-left text-xs font-medium text-slate-500">
              Carol ↓ / Predicted →
            </th>
            {cols.map((c) => (
              <th key={c} className="p-2 align-bottom">
                <div className="flex flex-col items-center gap-1">
                  <PaletteSwatch name={c} label={false} />
                  <span className="whitespace-nowrap text-[11px] text-slate-500">{c}</span>
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r} className="border-t border-slate-100">
              <th className="sticky left-0 z-10 whitespace-nowrap bg-white p-2 text-left font-normal">
                <PaletteSwatch name={r} />
              </th>
              {cols.map((c) => {
                const n = confusion[r][c] ?? 0;
                const onDiag = r === c;
                let bg = "transparent";
                if (n > 0) {
                  const t = n / maxCell; // 0..1
                  bg = onDiag
                    ? `rgba(16, 185, 129, ${0.15 + t * 0.5})` // emerald
                    : `rgba(245, 158, 11, ${0.12 + t * 0.5})`; // amber
                }
                return (
                  <td
                    key={c}
                    className="p-2 text-center tabular-nums"
                    style={{ backgroundColor: bg }}
                    title={`Carol ${r} → predicted ${c}: ${n}`}
                  >
                    <span className={n === 0 ? "text-slate-300" : "font-semibold text-slate-800"}>
                      {n === 0 ? "·" : n}
                    </span>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-2 text-xs text-slate-400">
        Green diagonal = agreement · amber off-diagonal = confusion (weight by count)
      </p>
    </div>
  );
}
