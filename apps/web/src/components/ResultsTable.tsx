import { useState } from "react";
import type { CaseResult } from "../types";
import PaletteSwatch from "./PaletteSwatch";
import MatchBadge from "./MatchBadge";
import Thumbnails from "./Thumbnails";

interface Props {
  cases: CaseResult[];
  /** client_id -> whether drape images exist in this environment. */
  hasImages: Record<string, boolean>;
}

function fmtLatency(ms: number | null): string {
  if (ms == null) return "—";
  if (ms < 1000) return `${ms} ms`;
  return `${(ms / 1000).toFixed(1)} s`;
}

function StepList({ c }: { c: CaseResult }) {
  const r = c.result;
  return (
    <div className="space-y-3 bg-slate-50 px-4 py-4 text-sm">
      {c.error && (
        <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-red-700">
          Engine error: {c.error}
        </div>
      )}

      {r && (
        <>
          <div className="flex flex-wrap gap-x-6 gap-y-1 text-slate-600">
            <span>
              Home season: <span className="font-medium text-slate-800">{r.home_season ?? "—"}</span>
            </span>
            <span className="inline-flex items-center gap-1.5">
              Flow result: <PaletteSwatch name={r.flow_result} />
            </span>
            {r.leaning && (
              <span className="inline-flex items-center gap-1.5">
                Leaning: <PaletteSwatch name={r.leaning} />
              </span>
            )}
            <span>
              Confidence: <span className="font-medium text-slate-800">{r.confidence ?? "—"}</span>
            </span>
            {!r.valid && (
              <span className="text-red-600">
                ⚠ invalid: {r.validation_error ?? "failed sanity check"}
              </span>
            )}
          </div>

          {r.steps.length > 0 ? (
            <ol className="space-y-2">
              {r.steps.map((s, i) => (
                <li
                  key={i}
                  className="rounded-md border border-slate-200 bg-white p-3"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded bg-slate-100 px-1.5 py-0.5 text-xs font-medium text-slate-600">
                      {s.step}
                    </span>
                    <span className="text-slate-400">→</span>
                    <PaletteSwatch name={s.winner} />
                    {s.criteria_cited.length > 0 && (
                      <span className="text-xs text-slate-400">
                        criteria {s.criteria_cited.join(", ")}
                      </span>
                    )}
                  </div>
                  {s.reasoning && (
                    <p className="mt-1.5 text-slate-600">{s.reasoning}</p>
                  )}
                </li>
              ))}
            </ol>
          ) : (
            <p className="text-slate-400">No per-step reasoning recorded.</p>
          )}

          {r.final_reasoning && (
            <div>
              <div className="text-xs font-medium uppercase tracking-wide text-slate-500">
                Final reasoning
              </div>
              <p className="mt-1 text-slate-700">{r.final_reasoning}</p>
            </div>
          )}
        </>
      )}

      {!r && !c.error && (
        <p className="text-slate-400">No structured result recorded for this case.</p>
      )}
    </div>
  );
}

function Row({ c, hasImages }: { c: CaseResult; hasImages: boolean }) {
  const [open, setOpen] = useState(false);
  const dim = !hasImages;

  return (
    <>
      <tr
        className={`border-t border-slate-100 transition hover:bg-slate-50/70 ${
          dim ? "opacity-60" : ""
        }`}
      >
        <td className="px-3 py-2 align-middle">
          <button
            type="button"
            onClick={() => setOpen((o) => !o)}
            aria-expanded={open}
            aria-label={open ? "Collapse reasoning" : "Expand reasoning"}
            className="flex h-6 w-6 items-center justify-center rounded text-slate-400 hover:bg-slate-200 hover:text-slate-700"
          >
            <span className={`transition-transform ${open ? "rotate-90" : ""}`}>▶</span>
          </button>
        </td>
        <td className="px-3 py-2 align-middle tabular-nums text-slate-500">
          {c.test_id ?? "—"}
        </td>
        <td className="px-3 py-2 align-middle font-medium text-slate-800">
          {c.client_id}
        </td>
        <td className="px-3 py-2 align-middle">
          {hasImages ? (
            <Thumbnails clientId={c.client_id} />
          ) : (
            <span className="text-xs italic text-slate-400">
              images not available in this environment
            </span>
          )}
        </td>
        <td className="px-3 py-2 align-middle">
          <PaletteSwatch name={c.predicted} />
        </td>
        <td className="px-3 py-2 align-middle text-slate-600">
          {c.carol_result ?? <span className="text-slate-300">—</span>}
        </td>
        <td className="px-3 py-2 align-middle">
          <MatchBadge kind={c.match_kind} />
        </td>
        <td className="px-3 py-2 align-middle text-slate-600">
          {c.confidence ?? "—"}
        </td>
        <td className="px-3 py-2 align-middle tabular-nums text-slate-500">
          {fmtLatency(c.latency_ms)}
        </td>
      </tr>
      {open && (
        <tr>
          <td colSpan={9} className="p-0">
            <StepList c={c} />
          </td>
        </tr>
      )}
    </>
  );
}

export default function ResultsTable({ cases, hasImages }: Props) {
  if (cases.length === 0) {
    return (
      <p className="text-sm text-slate-500">No cases in the latest batch.</p>
    );
  }
  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
      <table className="min-w-full text-left text-sm">
        <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
          <tr>
            <th className="px-3 py-2 font-medium" />
            <th className="px-3 py-2 font-medium">Test</th>
            <th className="px-3 py-2 font-medium">Client</th>
            <th className="px-3 py-2 font-medium">Drapes</th>
            <th className="px-3 py-2 font-medium">Predicted</th>
            <th className="px-3 py-2 font-medium">Carol</th>
            <th className="px-3 py-2 font-medium">Match</th>
            <th className="px-3 py-2 font-medium">Conf.</th>
            <th className="px-3 py-2 font-medium">Latency</th>
          </tr>
        </thead>
        <tbody>
          {cases.map((c) => (
            <Row
              key={c.client_id}
              c={c}
              hasImages={hasImages[c.client_id] ?? false}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}
