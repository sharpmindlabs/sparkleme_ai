import { Link } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { useData } from "../lib/store";
import { BarChart } from "../components/BarChart";
import { Card, Chip, Kpi, Meter, SectionTitle, StatusChip } from "../components/ui";

export function Dashboard() {
  const { session } = useAuth();
  const { analyses, models, prompts, corrections } = useData();
  const role = session!.user.role;

  const total = analyses.length;
  const pending = analyses.filter((a) => a.status === "Pending Review").length;
  const decided = analyses.filter((a) => ["Approved", "Corrected"].includes(a.status));
  const approvedFirst = decided.filter((a) => a.status === "Approved").length;
  const approvalRate = decided.length ? Math.round((approvedFirst / decided.length) * 100) : 0;
  const conflicts = analyses.filter((a) => a.status === "Conflicting Inputs").length;
  const needsReview = analyses.filter((a) => a.status === "Needs Human Review").length;
  const activePrompt = prompts.analysis.find((p) => p.active)?.version ?? "—";
  const pv = prompts.analysis;

  const title =
    role === "ADMIN" ? "Admin dashboard" : role === "EXPERT" ? "Expert dashboard" : "Analyst dashboard";

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">{title}</h1>
          <p className="text-sm text-slate-500">Role-scoped metrics · active analysis prompt {activePrompt}</p>
        </div>
        <Link to="/start">
          <span className="inline-flex items-center gap-1.5 rounded-lg bg-gradient-to-br from-teal-600 to-cyan-500 px-3.5 py-2 text-sm font-medium text-white shadow-sm hover:brightness-110">
            ＋ New Analysis
          </span>
        </Link>
      </div>

      {/* KPI row — varies by role */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {role === "ANALYST" && (
          <>
            <Kpi label="Submissions this week" value={total} sub="▲ 3 vs prior week" subTone="up" />
            <Kpi label="Awaiting review" value={pending} sub="oldest: 2 days" subTone="muted" />
            <Kpi label="First-pass approval" value={`${approvalRate}%`} sub="your submissions" subTone="up" />
            <Kpi label="Conflicting inputs" value={conflicts} sub="need input fixes" subTone="muted" />
          </>
        )}
        {role === "EXPERT" && (
          <>
            <Kpi label="Queue depth" value={pending + needsReview} sub={`oldest ${pending ? "2 days" : "—"}`} subTone="muted" />
            <Kpi label="AI first-pass accuracy" value={`${approvalRate}%`} sub="approved without correction" subTone="up" />
            <Kpi label="Instant-memory entries" value={corrections.length} sub="active corrections" subTone="muted" />
            <Kpi label="Rerun consistency" value="100%" sub="post-correction" subTone="up" />
          </>
        )}
        {role === "ADMIN" && (
          <>
            <Kpi label="Total analyses" value={total + 236} sub="▲ 18% vs last month" subTone="up" />
            <Kpi label="Active users" value={3} sub="1 suspended" subTone="muted" />
            <Kpi label="Cost / analysis" value="$0.11" sub="consensus mode" subTone="muted" />
            <Kpi label="Consensus accuracy" value="96.2%" sub="expert-verified" subTone="up" />
          </>
        )}
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <SectionTitle>Accuracy by prompt version</SectionTitle>
          <p className="mb-2 text-xs text-slate-500">First-pass expert approval rate per analysis-prompt version</p>
          <BarChart data={pv.map((v) => v.accuracy ?? 0)} labels={pv.map((v) => v.version)} suffix="%" />
        </Card>
        <Card>
          <SectionTitle>Analysis volume — last 8 weeks</SectionTitle>
          <p className="mb-2 text-xs text-slate-500">Completed analyses per week</p>
          <BarChart data={[18, 22, 25, 31, 28, 36, 41, 47]} labels={["W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8"]} color="#06b6d4" />
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <SectionTitle>{role === "EXPERT" ? "AI ↔ expert agreement by model" : "Model accuracy (expert-verified)"}</SectionTitle>
          {models.map((m) => (
            <div key={m.id} className="mb-2 flex items-center gap-3">
              <span className="w-48 shrink-0 text-sm">
                {m.name} <Chip tone={m.enabled ? "ok" : "gray"}>{m.enabled ? "on" : "off"}</Chip>
              </span>
              <Meter pct={m.accuracy} className="flex-1" />
              <b className="w-12 text-right text-sm">{m.accuracy}%</b>
            </div>
          ))}
          <p className="mt-1 text-xs text-slate-500">
            Consensus (weighted vote) accuracy: <b>96.2%</b>
          </p>
        </Card>
        <Card>
          <SectionTitle>Recent analyses</SectionTitle>
          {analyses.slice(0, 6).map((a) => (
            <div key={a.id} className="flex items-center justify-between border-b border-slate-100 py-1.5 text-sm last:border-0">
              <Link to={`/analyses/${a.id}`} className="text-teal-700 hover:underline">
                <b>#{a.id}</b> {a.client}
              </Link>
              <span className="flex items-center gap-1.5">
                {(a.expert_result ?? a.ai_result) && <Chip>{a.expert_result ?? a.ai_result}</Chip>}
                <StatusChip status={a.status} />
              </span>
            </div>
          ))}
          <Link to="/analyses" className="mt-2 inline-block text-sm text-teal-700 hover:underline">
            View all →
          </Link>
        </Card>
      </div>

      {role === "ANALYST" && (
        <Card>
          <SectionTitle>Input-quality tips</SectionTitle>
          <ul className="list-disc space-y-1 pl-5 text-sm text-slate-600">
            <li>Use an indoor-light face photo with even lighting and no colour cast; face height ≥ 800px.</li>
            <li>Hair colour is the age 17–20 natural colour — the single most reliable input.</li>
            <li>Free-form notes are weak context only; blush/flush claims are ignored by methodology.</li>
          </ul>
        </Card>
      )}
    </div>
  );
}
