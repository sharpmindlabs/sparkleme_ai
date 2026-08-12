import { useMemo, useState } from "react";
import { useAuth } from "../lib/auth";
import { useData } from "../lib/store";
import { Button, Card, Chip, cn, EmptyState, inputClass, Label, SectionTitle } from "../components/ui";
import { useToast } from "../components/Toast";
import type { PromptType } from "../types";

function lineDiff(from: string, to: string) {
  const fromLines = new Set(from.split("\n"));
  const toLines = new Set(to.split("\n"));
  const removed = from.split("\n").filter((l) => !toLines.has(l));
  const added = to.split("\n").filter((l) => !fromLines.has(l));
  return { removed, added };
}

export function Settings() {
  const { session } = useAuth();
  const { prompts, savePromptVersion, activatePrompt } = useData();
  const { toast } = useToast();

  const role = session!.user.role;
  const isExpert = role === "ADMIN" || role === "EXPERT";

  const [tab, setTab] = useState<PromptType>("analysis");
  const [selected, setSelected] = useState<string | null>(null);
  const [body, setBody] = useState<string | null>(null);
  const [note, setNote] = useState("");
  const [diffB, setDiffB] = useState<string | null>(null);

  const list = prompts[tab];
  const active = list.find((p) => p.active)?.version ?? list[list.length - 1].version;
  const selVersion = selected ?? active;
  const ver = list.find((p) => p.version === selVersion) ?? list[list.length - 1];
  const editorBody = body ?? ver.body;

  const diff = useMemo(() => {
    if (!diffB) return null;
    const other = list.find((p) => p.version === diffB);
    if (!other) return null;
    return lineDiff(other.body, ver.body);
  }, [diffB, list, ver]);

  if (!isExpert) return <EmptyState>🔒 Colour Analysis Expert or Admin role required to manage prompts.</EmptyState>;

  function selectVersion(v: string) {
    setSelected(v);
    setBody(null);
  }

  function save() {
    const created = savePromptVersion(tab, editorBody, note, session!.user.name);
    setSelected(created);
    setBody(null);
    setNote("");
    toast(`Saved as ${created} (immutable) — not active until you activate it`);
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold">Settings — Prompts</h1>
        <p className="text-sm text-slate-500">Prompts are version-controlled and immutable; exactly one active version per type. Changes are audit-logged.</p>
      </div>

      <div className="flex gap-1 border-b-2 border-slate-200">
        {(["analysis", "audit"] as PromptType[]).map((t) => (
          <button
            key={t}
            onClick={() => {
              setTab(t);
              setSelected(null);
              setBody(null);
              setDiffB(null);
            }}
            className={cn("rounded-t-lg px-4 py-2 text-sm", tab === t ? "font-semibold text-teal-700 shadow-[inset_0_-2px_0_#0d9488]" : "text-slate-500 hover:text-slate-700")}
          >
            {t === "analysis" ? "Expert Analysis Prompt" : "Audit Review Prompt"}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[320px_1fr]">
        <Card>
          <SectionTitle>Version history</SectionTitle>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs uppercase tracking-wide text-slate-500">
                <th className="py-1 text-left">Ver</th>
                <th className="py-1 text-left">Date</th>
                <th className="py-1 text-left">Author</th>
                <th className="py-1 text-left">Acc.</th>
              </tr>
            </thead>
            <tbody>
              {[...list].reverse().map((v) => (
                <tr key={v.version} className={cn("cursor-pointer hover:bg-teal-50/60", v.version === selVersion && "bg-teal-50")} onClick={() => selectVersion(v.version)}>
                  <td className="py-1 font-semibold">
                    {v.version} {v.active && <Chip tone="ok">ACTIVE</Chip>}
                  </td>
                  <td className="py-1 text-xs text-slate-500">{v.date}</td>
                  <td className="py-1 text-xs text-slate-500">{v.author}</td>
                  <td className="py-1 text-xs text-slate-500">{v.accuracy != null ? `${v.accuracy}%` : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-2 text-xs text-slate-400">Accuracy = first-pass expert approval rate while that version was active (FR-6.3).</p>

          <div className="mt-3 border-t border-slate-100 pt-3">
            <Label>Diff against version</Label>
            <select className={inputClass()} value={diffB ?? ""} onChange={(e) => setDiffB(e.target.value || null)}>
              <option value="">— none —</option>
              {list.filter((p) => p.version !== selVersion).map((p) => (
                <option key={p.version}>{p.version}</option>
              ))}
            </select>
          </div>
        </Card>

        <Card>
          <div className="mb-2 flex items-center justify-between">
            <SectionTitle>{tab === "analysis" ? "Expert Analysis Prompt" : "Audit Review Prompt"} — {ver.version}</SectionTitle>
            <div className="flex gap-2">
              {ver.version !== active && (
                <Button variant="green" sm onClick={() => { activatePrompt(tab, ver.version); toast(`${ver.version} activated — effective on the next analysis run`); }}>
                  Activate {ver.version}
                </Button>
              )}
              <Button sm onClick={save}>
                💾 Save as new version
              </Button>
            </div>
          </div>
          <p className="mb-2 text-xs text-slate-500">
            <b>Change note:</b> {ver.note}
          </p>

          {diff ? (
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 font-mono text-xs">
              <div className="mb-1 text-slate-500">Diff {diffB} → {ver.version}</div>
              {diff.removed.map((l, i) => (
                <div key={`r${i}`} className="text-rose-600">- {l}</div>
              ))}
              {diff.added.map((l, i) => (
                <div key={`a${i}`} className="text-emerald-700">+ {l}</div>
              ))}
              {diff.removed.length === 0 && diff.added.length === 0 && <div className="text-slate-400">No line differences.</div>}
            </div>
          ) : (
            <textarea className={inputClass("font-mono text-xs")} rows={16} value={editorBody} onChange={(e) => setBody(e.target.value)} />
          )}

          <div className="mt-3">
            <Label>Change note for new version</Label>
            <input className={inputClass()} value={note} onChange={(e) => setNote(e.target.value)} placeholder="What changed and why" />
          </div>
        </Card>
      </div>
    </div>
  );
}
