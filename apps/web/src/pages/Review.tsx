import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { useData } from "../lib/store";
import { Button, Card, Chip, EmptyState, inputClass, Label, SectionTitle, StatusChip } from "../components/ui";
import { PaletteCard } from "../components/PaletteViz";
import { useToast } from "../components/Toast";
import { confidenceLabel } from "../types";

export function Review() {
  const { id } = useParams();
  const { session } = useAuth();
  const { getAnalysis, reviewAnalysis, rerunAnalysis } = useData();
  const { toast } = useToast();

  const a = getAnalysis(Number(id));
  const role = session!.user.role;
  const isExpert = role === "ADMIN" || role === "EXPERT";

  const [verdict, setVerdict] = useState<"APPROVE" | "CORRECT">("APPROVE");
  const [palette, setPalette] = useState<string>(a?.candidate_set[0] ?? "");
  const [comments, setComments] = useState<string>(a?.expert_note ?? "");
  const [influence, setInfluence] = useState("");
  const [log, setLog] = useState<string[]>([]);

  if (!isExpert)
    return (
      <EmptyState>
        🔒 Colour Analysis Expert role required. Analysts submit for review; only experts refine and finalize results.
      </EmptyState>
    );
  if (!a) return <EmptyState>Analysis not found. <Link className="text-teal-700 underline" to="/analyses">Back to list</Link></EmptyState>;

  const rec = a.expert_result ?? a.ai_result ?? "—";

  function save() {
    if (verdict === "CORRECT") {
      if (!a!.candidate_set.includes(palette)) {
        toast(`Blocked — ${palette} is outside the candidate set. Fix the inputs and start a new analysis instead.`);
        return;
      }
      reviewAnalysis(a!.id, { verdict: "CORRECT", palette, comments, influence });
      toast("Correction saved → instant memory updated + queued for model training");
    } else {
      reviewAnalysis(a!.id, { verdict: "APPROVE", comments });
      toast("Approved with comments → positive training example stored");
    }
  }

  function rerun() {
    const result = rerunAnalysis(a!.id);
    setLog([]);
    result.lines.forEach((line, i) => {
      window.setTimeout(() => setLog((prev) => [...prev, line]), i * 420);
    });
    window.setTimeout(() => toast(`Rerun complete — memory ${result.memory}${result.memory === "HIT" ? " (instant feedback verified)" : ""}`), result.lines.length * 420);
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold">
          Correct / Refine / Rerun — #{a.id} {a.client}
        </h1>
        <p className="text-sm text-slate-500">Expert feedback feeds the instant correction memory and the background training pipeline.</p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <SectionTitle>Current AI result</SectionTitle>
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <Chip className="text-sm">{a.ai_result}</Chip>
            <Chip tone="gray">{a.confidence}% · {confidenceLabel(a.confidence)}</Chip>
            <StatusChip status={a.status} />
          </div>
          <p className="mb-3 text-xs text-slate-500">Candidate set: {a.candidate_set.join(", ") || "—"}</p>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            {a.candidate_set.map((p) => (
              <PaletteCard key={p} palette={p} tone={a.tone} recommended={p === rec} />
            ))}
          </div>
        </Card>

        <Card>
          <SectionTitle>Expert assessment</SectionTitle>
          <div className="mb-3">
            <Label>Verdict</Label>
            <select className={inputClass()} value={verdict} onChange={(e) => setVerdict(e.target.value as "APPROVE" | "CORRECT")}>
              <option value="APPROVE">Correct — approve with comments</option>
              <option value="CORRECT">Incorrect — correct the palette</option>
            </select>
          </div>
          {verdict === "CORRECT" && (
            <div className="mb-3">
              <Label>Correct palette (constrained to candidate set)</Label>
              <select className={inputClass()} value={palette} onChange={(e) => setPalette(e.target.value)}>
                {a.candidate_set.map((p) => (
                  <option key={p}>{p}</option>
                ))}
              </select>
              <p className="mt-1 text-xs text-slate-500">Palettes outside the candidate set are not selectable — a result outside the set is a hard failure (§1.2).</p>
            </div>
          )}
          <div className="mb-3">
            <Label>Comments (visible on report &amp; stored for training)</Label>
            <textarea className={inputClass()} rows={3} value={comments} onChange={(e) => setComments(e.target.value)} />
          </div>
          <div className="mb-3">
            <Label>Additional prompt influence (injected into the analysis prompt for this case class)</Label>
            <textarea className={inputClass()} rows={3} value={influence} onChange={(e) => setInfluence(e.target.value)} placeholder="e.g. For translucent, high-cheek-colour blondes prefer Light over True Spring when the jawline drops on the bright column…" />
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="green" onClick={save}>
              💾 Save feedback (instant)
            </Button>
            <Button onClick={rerun}>↻ Rerun analysis now</Button>
          </div>
          <p className="mt-2 text-xs text-slate-500">
            Saving writes to ① real-time correction memory (takes effect immediately, 1st → nth rerun) and ② the feedback store → SFT/DPO for open-source models, fine-tune API + prompt distillation for commercial models.
          </p>
        </Card>
      </div>

      <Card>
        <SectionTitle>Rerun log</SectionTitle>
        <div className="rounded-lg bg-slate-900 p-3 font-mono text-xs text-emerald-300">
          {log.length === 0 ? <span className="text-slate-500">No rerun yet in this session.</span> : log.map((l, i) => <div key={i}>{l}</div>)}
        </div>
      </Card>
    </div>
  );
}
