import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useData } from "../lib/store";
import { MODELS_SEED } from "../lib/mock";
import { PALETTE_ORDER } from "../palettes";
import { Button, Card, Chip, cn, inputClass, StatusChip } from "../components/ui";
import { confidenceLabel } from "../types";
import type { Analysis, AnalysisStatus } from "../types";

const STATUSES: (AnalysisStatus | "All")[] = ["All", "Pending Review", "Approved", "Corrected", "Needs Human Review", "Conflicting Inputs"];
const PAGE_SIZE = 50;
type SortKey = "id" | "client" | "date" | "confidence";

export function AnalysesList() {
  const { analyses } = useData();
  const [q, setQ] = useState("");
  const [status, setStatus] = useState<string>("All");
  const [palette, setPalette] = useState("All");
  const [model, setModel] = useState("All");
  const [dateFrom, setDateFrom] = useState("");
  const [sort, setSort] = useState<SortKey>("date");
  const [dir, setDir] = useState<-1 | 1>(-1);
  const [page, setPage] = useState(0);

  const filtered = useMemo(() => {
    let rows = [...analyses];
    if (q.trim()) {
      const s = q.toLowerCase();
      rows = rows.filter((a) => `${a.client} ${a.id}`.toLowerCase().includes(s));
    }
    if (status !== "All") rows = rows.filter((a) => a.status === status);
    if (palette !== "All") rows = rows.filter((a) => a.ai_result === palette || a.expert_result === palette);
    if (model !== "All") rows = rows.filter((a) => a.model_votes.some((v) => v.model === model));
    if (dateFrom) rows = rows.filter((a) => a.date >= dateFrom);
    rows.sort((x, y) => {
      const a = x[sort];
      const b = y[sort];
      return (a > b ? 1 : a < b ? -1 : 0) * dir;
    });
    return rows;
  }, [analyses, q, status, palette, model, dateFrom, sort, dir]);

  const pages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const current = Math.min(page, pages - 1);
  const rows = filtered.slice(current * PAGE_SIZE, current * PAGE_SIZE + PAGE_SIZE);

  function toggleSort(k: SortKey) {
    if (sort === k) setDir((d) => (d === 1 ? -1 : 1));
    else {
      setSort(k);
      setDir(1);
    }
  }

  function exportCsv() {
    const header = ["ID", "Client", "Date", "Hair", "Fitzpatrick", "AI result", "Expert result", "Confidence", "Status"];
    const lines = filtered.map((a) =>
      [a.id, a.client, a.date, a.hair, a.fitzpatrick, a.ai_result ?? "", a.expert_result ?? "", a.confidence, a.status]
        .map((c) => `"${String(c).replace(/"/g, '""')}"`)
        .join(","),
    );
    const blob = new Blob([[header.join(","), ...lines].join("\n")], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "analyses.csv";
    link.click();
    URL.revokeObjectURL(url);
  }

  function reset() {
    setQ("");
    setStatus("All");
    setPalette("All");
    setModel("All");
    setDateFrom("");
    setPage(0);
  }

  const th = (key: SortKey, label: string) => (
    <th className="cursor-pointer select-none px-2 py-2 text-left" onClick={() => toggleSort(key)}>
      {label} {sort === key ? (dir === 1 ? "▲" : "▼") : "⇅"}
    </th>
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">Analyses</h1>
          <p className="text-sm text-slate-500">{filtered.length} records</p>
        </div>
        <div className="flex gap-2">
          <Button variant="ghost" sm onClick={exportCsv}>
            ⬇ Export CSV
          </Button>
          <Link to="/start">
            <span className="inline-flex items-center gap-1.5 rounded-lg bg-gradient-to-br from-teal-600 to-cyan-500 px-3.5 py-2 text-sm font-medium text-white shadow-sm hover:brightness-110">
              ＋ New Analysis
            </span>
          </Link>
        </div>
      </div>

      <Card>
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <input className={inputClass("w-56")} placeholder="Search name or ID…" value={q} onChange={(e) => { setQ(e.target.value); setPage(0); }} />
          <select className={inputClass("w-44")} value={status} onChange={(e) => { setStatus(e.target.value); setPage(0); }}>
            {STATUSES.map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
          <select className={inputClass("w-40")} value={palette} onChange={(e) => { setPalette(e.target.value); setPage(0); }}>
            <option>All</option>
            {PALETTE_ORDER.map((p) => (
              <option key={p}>{p}</option>
            ))}
          </select>
          <select className={inputClass("w-44")} value={model} onChange={(e) => { setModel(e.target.value); setPage(0); }}>
            <option value="All">All models</option>
            {MODELS_SEED.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name}
              </option>
            ))}
          </select>
          <input type="date" className={inputClass("w-40")} value={dateFrom} onChange={(e) => { setDateFrom(e.target.value); setPage(0); }} title="From date" />
          <Button variant="ghost" sm onClick={reset}>
            Reset
          </Button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[820px] border-collapse text-sm">
            <thead>
              <tr className="border-b-2 border-slate-200 text-xs uppercase tracking-wide text-slate-500">
                {th("id", "ID")}
                {th("client", "Client")}
                {th("date", "Date")}
                <th className="px-2 py-2 text-left">Inputs</th>
                <th className="px-2 py-2 text-left">AI result</th>
                <th className="px-2 py-2 text-left">Expert result</th>
                {th("confidence", "Conf.")}
                <th className="px-2 py-2 text-left">Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((a: Analysis) => (
                <tr key={a.id} className="border-b border-slate-100 hover:bg-teal-50/50">
                  <td className="px-2 py-2 font-semibold">
                    <Link to={`/analyses/${a.id}`} className="text-teal-700 hover:underline">
                      #{a.id}
                    </Link>
                  </td>
                  <td className="px-2 py-2">{a.client}</td>
                  <td className="px-2 py-2 text-slate-500">{a.date}</td>
                  <td className="px-2 py-2 text-xs text-slate-500">
                    {a.hair} · Fitz {a.fitzpatrick}
                  </td>
                  <td className="px-2 py-2">{a.ai_result ? <Chip>{a.ai_result}</Chip> : "—"}</td>
                  <td className="px-2 py-2">{a.expert_result ? <Chip tone="info">{a.expert_result}</Chip> : "—"}</td>
                  <td className="px-2 py-2">
                    {a.confidence ? (
                      <span title={confidenceLabel(a.confidence)}>{a.confidence}%</span>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td className="px-2 py-2">
                    <StatusChip status={a.status} />
                  </td>
                </tr>
              ))}
              {rows.length === 0 && (
                <tr>
                  <td colSpan={8} className="px-2 py-8 text-center text-slate-400">
                    No analyses match the current filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {pages > 1 && (
          <div className="mt-3 flex items-center justify-between text-sm">
            <span className="text-slate-500">
              Page {current + 1} of {pages} · {PAGE_SIZE}/page
            </span>
            <div className="flex gap-2">
              <button className={cn("rounded-lg px-2.5 py-1 text-sm", current === 0 ? "text-slate-300" : "text-teal-700 hover:bg-teal-50")} disabled={current === 0} onClick={() => setPage(current - 1)}>
                ← Prev
              </button>
              <button className={cn("rounded-lg px-2.5 py-1 text-sm", current >= pages - 1 ? "text-slate-300" : "text-teal-700 hover:bg-teal-50")} disabled={current >= pages - 1} onClick={() => setPage(current + 1)}>
                Next →
              </button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
