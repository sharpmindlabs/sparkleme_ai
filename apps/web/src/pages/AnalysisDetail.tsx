import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { useData } from "../lib/store";
import { modelName } from "../lib/mock";
import { PALETTE_ORDER } from "../palettes";
import { criterionLabel } from "../ruleouts";
import { Button, Card, Chip, cn, EmptyState, inputClass, SectionTitle, StatusChip } from "../components/ui";
import { FaceSvg, PaletteCard, SwatchRow } from "../components/PaletteViz";
import { useToast } from "../components/Toast";
import { confidenceLabel } from "../types";

const PENDING: string[] = ["Pending Review", "Needs Human Review", "Conflicting Inputs"];

export function AnalysisDetail() {
  const { id } = useParams();
  const { session } = useAuth();
  const { getAnalysis, reviewAnalysis } = useData();
  const { toast } = useToast();
  const navigate = useNavigate();

  const a = getAnalysis(Number(id));
  const [zoom, setZoom] = useState<string | null>(null);
  const [cmpA, setCmpA] = useState<string>(PALETTE_ORDER[0]);
  const [cmpB, setCmpB] = useState<string>(PALETTE_ORDER[1]);

  if (!a) return <EmptyState>Analysis not found. <Link className="text-teal-700 underline" to="/analyses">Back to list</Link></EmptyState>;

  const role = session!.user.role;
  const isExpert = role === "ADMIN" || role === "EXPERT";
  const rec = a.expert_result ?? a.ai_result ?? a.candidate_set[0] ?? "—";
  const pending = PENDING.includes(a.status);

  function approve() {
    const comments = window.prompt("Approval comments:", "Overlays confirm the recommendation.");
    if (comments === null) return;
    reviewAnalysis(a!.id, { verdict: "APPROVE", comments });
    toast("Approved ✓ — stored as a positive training example");
  }

  return (
    <div className="space-y-4">
      {/* header + actions */}
      <div className="flex flex-wrap items-start justify-between gap-3 print:hidden">
        <div>
          <h1 className="text-xl font-bold">
            Analysis #{a.id} — {a.client}
          </h1>
          <p className="text-sm text-slate-500">
            {a.date} · prompt {a.prompt_version} · engine {a.engine.mode}
            {a.engine.models ? ` · ${a.engine.models.map((m) => modelName(m).split(" ")[0]).join(", ")}` : ""}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="gray" onClick={() => toast(`Report emailed to ${a.client.split(" ")[0].toLowerCase()}@client.example ✉`)}>
            ✉ Email Report
          </Button>
          <Button variant="gray" onClick={() => window.print()}>
            ⬇ Export PDF
          </Button>
          {isExpert ? (
            pending ? (
              <>
                <Button variant="green" onClick={approve}>
                  ✓ Approve &amp; Finalize
                </Button>
                <Button variant="amber" onClick={() => navigate(`/analyses/${a.id}/review`)}>
                  ✎ Correct / Refine
                </Button>
              </>
            ) : (
              <Button variant="ghost" onClick={() => navigate(`/analyses/${a.id}/review`)}>
                ↻ Rerun / Refine
              </Button>
            )
          ) : pending ? (
            <Chip tone="warn">Awaiting expert review — read only</Chip>
          ) : (
            <Chip tone="ok">Finalized by expert</Chip>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[300px_1fr]">
        {/* left column: result / inputs / votes */}
        <div className="space-y-4">
          <Card>
            <SectionTitle>Result</SectionTitle>
            {a.result_status === "OK" ? (
              <>
                <div className="flex items-center gap-3">
                  <FaceSvg tone={a.tone} className="h-16 w-14" />
                  <div>
                    <div className="text-lg font-bold">{rec}</div>
                    <SwatchRow palette={rec} className="mt-1 w-32" />
                    <div className="mt-1 flex gap-1">
                      <StatusChip status={a.status} />
                      <Chip tone="gray">{a.confidence}% · {confidenceLabel(a.confidence)}</Chip>
                    </div>
                  </div>
                </div>
                <table className="mt-3 w-full text-sm">
                  <tbody>
                    <tr><td className="py-0.5 text-slate-500">Undertone</td><td className="font-semibold">{a.undertone}</td></tr>
                    <tr><td className="py-0.5 text-slate-500">Home season</td><td className="font-semibold">{a.home_season}</td></tr>
                    <tr><td className="py-0.5 text-slate-500">Flow result</td><td className="font-semibold">{rec}</td></tr>
                  </tbody>
                </table>
              </>
            ) : (
              <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
                <b>{a.result_status}</b> — {a.why}
              </div>
            )}
          </Card>

          <Card>
            <SectionTitle>Inputs</SectionTitle>
            <table className="w-full text-sm">
              <tbody>
                <tr><td className="py-0.5 text-slate-500">Hair @ 17–20</td><td className="font-semibold">{a.hair}</td></tr>
                <tr><td className="py-0.5 text-slate-500">Fitzpatrick</td><td className="font-semibold">Type {a.fitzpatrick}</td></tr>
              </tbody>
            </table>
            {a.notes && (
              <>
                <div className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Client-provided details</div>
                <p className="text-sm">{a.notes}</p>
                <p className="text-xs text-slate-400">(weak signal — never overrides rule-outs)</p>
              </>
            )}
            <div className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Candidate set after rule-outs</div>
            <div className="mt-1 flex flex-wrap gap-1">
              {a.candidate_set.length ? (
                a.candidate_set.map((c) => (
                  <Chip key={c} tone={c === rec ? "ok" : "plain"}>
                    {c}
                  </Chip>
                ))
              ) : (
                <Chip tone="bad">EMPTY</Chip>
              )}
            </div>
            <p className="mt-1 text-xs text-slate-400">Level 1 (hair) ∩ Level 2 (Fitzpatrick). The result is constrained to this set.</p>
          </Card>

          {a.model_votes.length > 0 && (
            <Card>
              <SectionTitle>Model votes</SectionTitle>
              {a.model_votes.map((v, i) => (
                <div key={i} className="flex items-center justify-between py-1 text-sm">
                  <span>{modelName(v.model)}</span>
                  <Chip tone={v.vote === rec ? "ok" : "warn"}>{v.vote}</Chip>
                </div>
              ))}
              <p className="mt-1 text-xs text-slate-500">
                Consensus ({a.engine.strategy ?? a.engine.mode}) → <b>{a.ai_result}</b>. Votes outside the candidate set are discarded and logged.
              </p>
            </Card>
          )}
        </div>

        {/* right column: overlays + evidence */}
        <div className="space-y-4">
          <Card>
            <SectionTitle>Overlay on all 10 palettes</SectionTitle>
            <p className="mb-3 text-xs text-slate-500">Cropped face composited on each palette (placeholder visuals). Click a card to zoom.</p>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
              {PALETTE_ORDER.map((p) => (
                <PaletteCard key={p} palette={p} tone={a.tone} recommended={p === rec} onClick={() => setZoom(p)} />
              ))}
            </div>

            {/* side-by-side compare */}
            <div className="mt-4 border-t border-slate-100 pt-3">
              <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Compare any two</div>
              <div className="grid grid-cols-2 gap-3">
                {[[cmpA, setCmpA] as const, [cmpB, setCmpB] as const].map(([val, set], i) => (
                  <div key={i}>
                    <select className={inputClass("mb-2")} value={val} onChange={(e) => set(e.target.value)}>
                      {PALETTE_ORDER.map((p) => (
                        <option key={p}>{p}</option>
                      ))}
                    </select>
                    <PaletteCard palette={val} tone={a.tone} recommended={val === rec} />
                  </div>
                ))}
              </div>
            </div>
          </Card>

          <Card>
            <SectionTitle>Why {rec}?</SectionTitle>
            <p className="mb-3 text-sm">{a.why}</p>
            <table className="w-full text-sm">
              <tbody>
                <tr className="align-top">
                  <td className="w-44 py-1 text-slate-500">a) Eyes (hypothesis only)</td>
                  <td className="py-1">{a.evidence.a_eyes}</td>
                </tr>
                <tr className="align-top">
                  <td className="py-1 text-slate-500">b) Hair + rule-out</td>
                  <td className="py-1">{a.evidence.b_hair}</td>
                </tr>
                <tr className="align-top">
                  <td className="py-1 text-slate-500">c) Skin characteristics</td>
                  <td className="py-1">{a.evidence.c_skin}</td>
                </tr>
                <tr className="align-top">
                  <td className="py-1 text-slate-500">d) Drape steps</td>
                  <td className="py-1">
                    <div className="space-y-2">
                      {a.evidence.d_drape_steps.map((s) => (
                        <div key={s.step}>
                          <div>
                            <b>Step {s.step}:</b> {s.winner}
                          </div>
                          {s.reasoning && <div className="text-slate-600">{s.reasoning}</div>}
                          <div className="mt-0.5 flex flex-wrap gap-1">
                            {s.criteria_cited.map((c) => (
                              <Chip key={c} tone="gray" className="text-[10px]">
                                {c}. {criterionLabel(c)}
                              </Chip>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
            {a.expert_note && (
              <div className="mt-3 rounded-lg border border-dashed border-slate-300 bg-slate-50 p-3 text-sm">
                <b>Expert review:</b> {a.expert_note}
              </div>
            )}
          </Card>
        </div>
      </div>

      {/* zoom modal */}
      {zoom && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-6 print:hidden" onClick={() => setZoom(null)}>
          <div className={cn("w-full max-w-sm")} onClick={(e) => e.stopPropagation()}>
            <PaletteCard palette={zoom} tone={a.tone} recommended={zoom === rec} />
            <div className="mt-3 rounded-xl bg-white p-3 text-sm">
              <div className="font-semibold">{zoom}</div>
              <SwatchRow palette={zoom} className="mt-1" />
              <Button variant="gray" sm className="mt-3" onClick={() => setZoom(null)}>
                Close
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
