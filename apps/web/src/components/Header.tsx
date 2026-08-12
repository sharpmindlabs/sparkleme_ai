import type { EngineConfig } from "../types";

interface Props {
  config: EngineConfig | null;
  running: boolean;
  onRun: () => void;
}

export default function Header({ config, running, onRun }: Props) {
  const isMock = config?.provider === "mock";

  return (
    <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/90 backdrop-blur">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3 sm:px-6">
        <div className="flex items-center gap-2">
          <span className="text-lg" aria-hidden="true">
            ✨
          </span>
          <h1 className="text-base font-semibold tracking-tight text-slate-900">
            SparkleMe — Inference Review
          </h1>
        </div>

        {/* Live provider + model badge */}
        <div className="flex items-center gap-2">
          <span
            className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-medium text-slate-700"
            title={config ? `images: ${config.images_root}` : undefined}
          >
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" aria-hidden="true" />
            {config ? (
              <>
                <span className="text-slate-500">{config.provider}</span>
                <span className="text-slate-300">/</span>
                <span>{config.model}</span>
              </>
            ) : (
              <span className="text-slate-400">connecting…</span>
            )}
          </span>

          {config && (
            <span className="hidden text-xs text-slate-400 sm:inline">
              {config.available_count} of 50 with images
            </span>
          )}
        </div>

        <div className="ml-auto flex items-center gap-3">
          {isMock && (
            <span className="hidden max-w-xs text-xs text-amber-700 md:inline">
              Mock provider — placeholder results; configure a real model in{" "}
              <code className="rounded bg-amber-50 px-1">.env</code>.
            </span>
          )}
          <button
            type="button"
            onClick={onRun}
            disabled={running}
            className="inline-flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-500 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:bg-indigo-300"
          >
            {running && (
              <svg
                className="h-4 w-4 animate-spin text-white"
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
            )}
            {running ? "Analysing…" : "Run"}
          </button>
        </div>
      </div>

      {/* Mobile mock note */}
      {isMock && (
        <div className="border-t border-amber-100 bg-amber-50 px-4 py-1.5 text-center text-xs text-amber-700 md:hidden">
          Mock provider — placeholder results; configure a real model in .env.
        </div>
      )}
    </header>
  );
}
