import type { BatchSummary } from "../types";

function pct(x: number): string {
  return `${(x * 100).toFixed(1)}%`;
}

function BigTile({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent?: string;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="text-xs font-medium uppercase tracking-wide text-slate-500">
        {label}
      </div>
      <div className={`mt-1 text-3xl font-semibold tabular-nums ${accent ?? "text-slate-900"}`}>
        {value}
      </div>
    </div>
  );
}

function CountChip({
  label,
  value,
  cls,
}: {
  label: string;
  value: number;
  cls: string;
}) {
  return (
    <div className="flex items-baseline justify-between rounded-lg border border-slate-200 bg-white px-3 py-2">
      <span className="text-xs font-medium text-slate-500">{label}</span>
      <span className={`text-lg font-semibold tabular-nums ${cls}`}>{value}</span>
    </div>
  );
}

export default function SummaryStrip({ summary }: { summary: BatchSummary }) {
  return (
    <section aria-label="Run summary" className="space-y-3">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-2 lg:grid-cols-2">
        <BigTile
          label="Accuracy (exact + boundary)"
          value={pct(summary.accuracy)}
          accent="text-indigo-600"
        />
        <BigTile
          label="Exact accuracy"
          value={pct(summary.exact_accuracy)}
          accent="text-emerald-600"
        />
      </div>

      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5">
        <CountChip label="Scored" value={summary.scored} cls="text-slate-800" />
        <CountChip label="Exact" value={summary.exact} cls="text-green-700" />
        <CountChip label="Boundary" value={summary.boundary} cls="text-amber-700" />
        <CountChip label="Miss" value={summary.misses} cls="text-red-700" />
        <CountChip label="Error" value={summary.errors} cls="text-slate-600" />
      </div>

      <div className="flex flex-wrap items-center gap-3 text-sm">
        <span className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-slate-600">
          <span className="font-medium text-slate-500">Baseline</span>
          Carol first-pass: <span className="font-semibold text-slate-800">32/50 (64%)</span>
        </span>
        <span className="text-xs text-slate-400">
          {summary.provider} / {summary.model} · {summary.total} cases attempted
        </span>
      </div>
    </section>
  );
}
