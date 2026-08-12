import { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { useData } from "../lib/store";
import { modelName } from "../lib/mock";
import { BarChart } from "../components/BarChart";
import { Button, Card, Chip, cn, EmptyState, inputClass, Kpi, Label, Meter, SectionTitle } from "../components/ui";
import { useToast } from "../components/Toast";
import { ROLE_LABELS } from "../types";
import type { Role } from "../types";

const TABS = [
  ["models", "Model Configuration"],
  ["users", "User Management"],
  ["metrics", "Metrics"],
  ["train", "Training Pipeline"],
] as const;
type Tab = (typeof TABS)[number][0];

const STRATEGIES = ["Weighted majority vote", "Auditor-scored best output", "Unanimity else escalate"];
const ROLES: Role[] = ["ADMIN", "EXPERT", "ANALYST", "VIEWER"];

export function Admin() {
  const { session } = useAuth();
  const data = useData();
  const { toast } = useToast();
  const [tab, setTab] = useState<Tab>("models");

  if (session!.user.role !== "ADMIN")
    return <EmptyState>🔒 Admin access required. Sign in as Admin to manage models, users and training.</EmptyState>;

  const { engine, models, users, corrections, jobs, updateEngine, toggleModel, setModelWeight, inviteUser, setUserRole, toggleUserStatus, expireMemory, triggerJob } = data;
  const enabledCount = models.filter((m) => m.enabled).length;

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold">Admin</h1>
        <p className="text-sm text-slate-500">Models · users · metrics · training</p>
      </div>

      <div className="flex flex-wrap gap-1 border-b-2 border-slate-200">
        {TABS.map(([id, label]) => (
          <button key={id} onClick={() => setTab(id)} className={cn("rounded-t-lg px-4 py-2 text-sm", tab === id ? "font-semibold text-teal-700 shadow-[inset_0_-2px_0_#0d9488]" : "text-slate-500 hover:text-slate-700")}>
            {label}
          </button>
        ))}
      </div>

      {tab === "models" && (
        <div className="space-y-4">
          <Card>
            <SectionTitle>Execution mode</SectionTitle>
            <p className="mb-3 text-xs text-slate-500">Platform-wide — analysts and experts cannot choose models per analysis (FR-7.1). Snapshotted per analysis for reproducibility.</p>
            <div className="flex flex-wrap items-end gap-4">
              <div className="w-56">
                <Label>Mode</Label>
                <select className={inputClass()} value={engine.mode} onChange={(e) => updateEngine({ mode: e.target.value as "single" | "consensus" })}>
                  <option value="consensus">Multi-model consensus</option>
                  <option value="single">Single model</option>
                </select>
              </div>
              {engine.mode === "consensus" ? (
                <div className="w-64">
                  <Label>Consensus strategy</Label>
                  <select className={inputClass()} value={engine.strategy} onChange={(e) => { updateEngine({ strategy: e.target.value }); toast("Strategy updated"); }}>
                    {STRATEGIES.map((s) => (
                      <option key={s}>{s}</option>
                    ))}
                  </select>
                </div>
              ) : (
                <div className="w-64">
                  <Label>Primary model</Label>
                  <select className={inputClass()} value={engine.primary} onChange={(e) => { updateEngine({ primary: e.target.value }); toast("Primary model updated"); }}>
                    {models.filter((m) => m.enabled).map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}
              <Chip tone="info">Active: {engine.mode === "single" ? modelName(engine.primary) : `${engine.strategy} · ${enabledCount} models`}</Chip>
            </div>
          </Card>

          <Card>
            <div className="mb-2 flex items-center justify-between">
              <SectionTitle>Model registry</SectionTitle>
              <Button variant="ghost" sm onClick={() => toast("Add model: endpoint, vaulted key, vote weight, provider adapter")}>
                ＋ Add model
              </Button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[760px] text-sm">
                <thead>
                  <tr className="text-xs uppercase tracking-wide text-slate-500">
                    <th className="py-2 text-left">Model</th>
                    <th className="py-2 text-left">Type</th>
                    <th className="py-2 text-left">Status</th>
                    <th className="py-2 text-left">Weight</th>
                    <th className="py-2 text-left">Accuracy</th>
                    <th className="py-2 text-left">Latency</th>
                    <th className="py-2 text-left">Training path</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {models.map((m) => (
                    <tr key={m.id} className="border-t border-slate-100">
                      <td className="py-2 font-semibold">{m.name}</td>
                      <td className="py-2">{m.type}</td>
                      <td className="py-2">
                        <Chip tone={m.enabled ? "ok" : "gray"}>{m.enabled ? "Enabled" : "Disabled"}</Chip>
                      </td>
                      <td className="py-2">
                        <input className={inputClass("w-16")} type="number" step="0.1" value={m.weight} onChange={(e) => setModelWeight(m.id, parseFloat(e.target.value) || 0)} />
                      </td>
                      <td className="py-2">{m.accuracy}%</td>
                      <td className="py-2">{m.latency}</td>
                      <td className="py-2 text-xs text-slate-500">{m.training}</td>
                      <td className="py-2">
                        <Button variant="gray" sm onClick={() => toggleModel(m.id)}>
                          {m.enabled ? "Disable" : "Enable"}
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-2 text-xs text-slate-400">Deterministic rule-outs run outside the models — identical for every engine configuration.</p>
          </Card>
        </div>
      )}

      {tab === "users" && (
        <Card>
          <div className="mb-2 flex items-center justify-between">
            <SectionTitle>Users</SectionTitle>
            <Button sm onClick={() => { const e = window.prompt("Invite email:", "new.reviewer@sparkleme.app"); if (e) { inviteUser(e); toast(`Invitation sent to ${e}`); } }}>
              ＋ Invite user
            </Button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-sm">
              <thead>
                <tr className="text-xs uppercase tracking-wide text-slate-500">
                  <th className="py-2 text-left">Name</th>
                  <th className="py-2 text-left">Email</th>
                  <th className="py-2 text-left">Role</th>
                  <th className="py-2 text-left">Status</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id} className="border-t border-slate-100">
                    <td className="py-2 font-semibold">{u.name}</td>
                    <td className="py-2">{u.email}</td>
                    <td className="py-2">
                      <select className={inputClass("w-48")} value={u.role} onChange={(e) => setUserRole(u.id, e.target.value as Role)}>
                        {ROLES.map((r) => (
                          <option key={r} value={r}>
                            {ROLE_LABELS[r]}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="py-2">
                      <Chip tone={u.status === "Active" ? "ok" : "gray"}>{u.status}</Chip>
                    </td>
                    <td className="py-2">
                      <Button variant="gray" sm onClick={() => toggleUserStatus(u.id)}>
                        {u.status === "Active" ? "Suspend" : "Reactivate"}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {tab === "metrics" && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <Card>
              <SectionTitle>Expert approval rate by model</SectionTitle>
              {models.map((m) => (
                <div key={m.id} className="mb-2 flex items-center gap-3">
                  <span className="w-52 shrink-0 text-sm">{m.name}</span>
                  <Meter pct={m.accuracy} className="flex-1" />
                  <b className="w-12 text-right text-sm">{m.accuracy}%</b>
                </div>
              ))}
              <div className="mb-1 flex items-center gap-3">
                <span className="w-52 shrink-0 text-sm font-semibold">Consensus (production)</span>
                <Meter pct={96.2} className="flex-1" />
                <b className="w-12 text-right text-sm">96.2%</b>
              </div>
            </Card>
            <Card>
              <SectionTitle>Corrections &amp; rerun consistency</SectionTitle>
              <BarChart data={[9, 7, 5, 4, 2, 2, 1, 0]} labels={["W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8"]} color="#e11d48" />
              <p className="mt-1 text-xs text-slate-500">
                Expert corrections/week (declining = models learning). Rerun-after-correction consistency: <b>100%</b> (instant layer).
              </p>
            </Card>
          </div>
          <Card>
            <SectionTitle>Audit outcomes (last 250)</SectionTitle>
            <div className="flex flex-wrap gap-2">
              <Chip tone="ok">APPROVE 226</Chip>
              <Chip tone="warn">REVISE 17</Chip>
              <Chip tone="bad">REJECT 7</Chip>
            </div>
            <p className="mt-2 text-xs text-slate-500">Top failures: 4.2 drape disagreement (11), 5.2 skin-corroboration mismatch (7), 2.2 candidate-set breach (0 since prompt v1.3).</p>
          </Card>
        </div>
      )}

      {tab === "train" && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <Card>
            <SectionTitle>Feedback store</SectionTitle>
            <div className="grid grid-cols-3 gap-3">
              <Kpi label="approved examples" value={248} />
              <Kpi label="corrections" value={30} />
              <Kpi label="live memory entries" value={corrections.length} />
            </div>
            <div className="mt-3 text-xs font-semibold uppercase tracking-wide text-slate-500">Instant layer — correction memory (immediate effect)</div>
            <div className="overflow-x-auto">
              <table className="mt-1 w-full text-sm">
                <thead>
                  <tr className="text-xs uppercase tracking-wide text-slate-500">
                    <th className="py-1 text-left">Analysis</th>
                    <th className="py-1 text-left">Corrected to</th>
                    <th className="py-1 text-left">By</th>
                    <th className="py-1 text-left">Date</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {corrections.map((c) => (
                    <tr key={c.id} className="border-t border-slate-100">
                      <td className="py-1">
                        <Link className="text-teal-700 hover:underline" to={`/analyses/${c.id}`}>
                          #{c.id}
                        </Link>
                      </td>
                      <td className="py-1">
                        <Chip tone="info">{c.palette}</Chip>
                      </td>
                      <td className="py-1 text-xs text-slate-500">{c.by}</td>
                      <td className="py-1 text-xs text-slate-500">{c.date}</td>
                      <td className="py-1">
                        <Button variant="gray" sm onClick={() => { expireMemory(c.id); toast(`Memory entry for #${c.id} expired`); }}>
                          Expire
                        </Button>
                      </td>
                    </tr>
                  ))}
                  {corrections.length === 0 && (
                    <tr>
                      <td colSpan={5} className="py-3 text-center text-slate-400">
                        No live memory entries.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
            <p className="mt-2 text-xs text-slate-400">Every new analysis checks this memory (image embedding + inputs); exact/near matches return the expert-verified result on the 1st and nth attempt.</p>
          </Card>

          <Card>
            <SectionTitle>Background layer — training jobs</SectionTitle>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-xs uppercase tracking-wide text-slate-500">
                    <th className="py-1 text-left">Job</th>
                    <th className="py-1 text-left">Model</th>
                    <th className="py-1 text-left">Method</th>
                    <th className="py-1 text-left">Examples</th>
                    <th className="py-1 text-left">Status</th>
                    <th className="py-1 text-left">Δ</th>
                  </tr>
                </thead>
                <tbody>
                  {jobs.map((j) => (
                    <tr key={j.id} className="border-t border-slate-100">
                      <td className="py-1 text-xs font-semibold">{j.id}</td>
                      <td className="py-1 text-xs">{j.model}</td>
                      <td className="py-1 text-xs">{j.method}</td>
                      <td className="py-1">{j.examples}</td>
                      <td className="py-1">
                        <Chip tone={j.status === "Completed" ? "ok" : j.status === "Running" ? "warn" : "info"}>{j.status}</Chip>
                      </td>
                      <td className="py-1 text-xs">{j.delta}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              <Button sm onClick={() => { triggerJob(); toast("Fine-tune job queued: SFT + DPO on corrections"); }}>
                ▶ Trigger training run
              </Button>
              <Button variant="ghost" sm onClick={() => toast("Golden-set regression: 48/50 passed — promote candidate?")}>
                Run golden-set eval
              </Button>
            </div>
            <p className="mt-2 text-xs text-slate-400">Open-source: SFT + DPO weight updates. Commercial: provider fine-tune APIs + prompt distillation. Promotion gated on golden-set regression (blue/green).</p>
          </Card>
        </div>
      )}
    </div>
  );
}
