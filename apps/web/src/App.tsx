import { useCallback, useEffect, useMemo, useState } from "react";
import type { BatchSummary, CaseMeta, EngineConfig } from "./types";
import { fetchCases, fetchConfig, fetchResults, runBatch } from "./api";
import Header from "./components/Header";
import SummaryStrip from "./components/SummaryStrip";
import ResultsTable from "./components/ResultsTable";
import ConfusionView from "./components/ConfusionView";

export default function App() {
  const [config, setConfig] = useState<EngineConfig | null>(null);
  const [cases, setCases] = useState<CaseMeta[]>([]);
  const [summary, setSummary] = useState<BatchSummary | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Load config, case metadata, and any prior results on mount.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [cfg, cs, res] = await Promise.all([
          fetchConfig().catch(() => null),
          fetchCases().catch(() => [] as CaseMeta[]),
          fetchResults().catch(() => null),
        ]);
        if (cancelled) return;
        setConfig(cfg);
        setCases(cs);
        setSummary(res);
        if (!cfg) {
          setError(
            "Could not reach the engine at /api. Is it running on http://localhost:8000?",
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const onRun = useCallback(async () => {
    setRunning(true);
    setError(null);
    try {
      const res = await runBatch({ only_available: true });
      setSummary(res);
      // Refresh case metadata (has_images may reflect the same env, but cheap).
      fetchCases()
        .then(setCases)
        .catch(() => {});
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setRunning(false);
    }
  }, []);

  // client_id -> has_images, for de-emphasising image-less rows.
  const hasImages = useMemo(() => {
    const m: Record<string, boolean> = {};
    for (const c of cases) m[c.client_id] = c.has_images;
    return m;
  }, [cases]);

  return (
    <div className="min-h-screen">
      <Header config={config} running={running} onRun={onRun} />

      <main className="mx-auto max-w-7xl space-y-8 px-4 py-6 sm:px-6">
        {error && (
          <div
            role="alert"
            className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
          >
            {error}
          </div>
        )}

        {loading && (
          <p className="text-sm text-slate-500">Loading engine state…</p>
        )}

        {running && (
          <div className="flex items-center gap-3 rounded-lg border border-indigo-200 bg-indigo-50 px-4 py-3 text-sm text-indigo-800">
            <svg
              className="h-5 w-5 animate-spin text-indigo-600"
              viewBox="0 0 24 24"
              fill="none"
              aria-hidden="true"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
              />
            </svg>
            Analysing… this can take a few minutes with a real model.
          </div>
        )}

        {summary ? (
          <>
            <SummaryStrip summary={summary} />

            <section className="space-y-3">
              <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
                Confusion (Carol primary → predicted)
              </h2>
              <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                <ConfusionView confusion={summary.confusion} />
              </div>
            </section>

            <section className="space-y-3">
              <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
                Cases ({summary.cases.length})
              </h2>
              <ResultsTable cases={summary.cases} hasImages={hasImages} />
            </section>
          </>
        ) : (
          !loading &&
          !running && (
            <div className="rounded-xl border border-dashed border-slate-300 bg-white px-6 py-12 text-center">
              <p className="text-sm text-slate-600">
                No results yet. Press{" "}
                <span className="font-semibold text-indigo-600">Run</span> to
                analyse the {config?.available_count ?? 50} available client
                cases.
              </p>
            </div>
          )
        )}
      </main>

      <footer className="mx-auto max-w-7xl px-4 pb-8 pt-2 text-xs text-slate-400 sm:px-6">
        SparkleMe internal eval tool · engine{" "}
        {config ? `${config.provider}/${config.model}` : "offline"}
      </footer>
    </div>
  );
}
