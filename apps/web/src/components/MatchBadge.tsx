import type { MatchKind } from "../types";

const STYLES: Record<MatchKind, { label: string; cls: string }> = {
  exact: { label: "exact", cls: "bg-green-100 text-green-800 ring-green-600/20" },
  boundary: { label: "boundary", cls: "bg-amber-100 text-amber-800 ring-amber-600/20" },
  miss: { label: "miss", cls: "bg-red-100 text-red-800 ring-red-600/20" },
  error: { label: "error", cls: "bg-slate-200 text-slate-700 ring-slate-500/20" },
  no_ground_truth: {
    label: "no ground truth",
    cls: "bg-slate-100 text-slate-500 ring-slate-400/20",
  },
};

export default function MatchBadge({ kind }: { kind: MatchKind }) {
  const s = STYLES[kind] ?? STYLES.miss;
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${s.cls}`}
    >
      {s.label}
    </span>
  );
}
