import { useMemo, useState } from "react";
import type { ChangeEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useData, enabledModelIds } from "../lib/store";
import { modelName } from "../lib/mock";
import { candidateSet, FITZPATRICK, HAIR_COLOURS, level1, level2 } from "../ruleouts";
import { Button, Card, Chip, cn, inputClass, Label, SectionTitle } from "../components/ui";
import { FaceSvg, SKIN_TONES } from "../components/PaletteViz";

const PIPELINE = [
  "Validate image & crop (face only)",
  "Level 1–2 rule-outs → candidate set",
  "Level 3 earthy / Level 4 flush checks (image-derived)",
  "Overlay composites on all palettes",
  "Drape Step 1 — Cool vs Warm",
  "Drape Step 2 — Home season",
  "Drape Step 3 — Flow",
  "Correction-memory lookup (instant layer)",
  "Multi-model consensus & audit pass",
];

export function StartAnalysis() {
  const { engine, models, createAnalysis } = useData();
  const navigate = useNavigate();

  const [hair, setHair] = useState<string>("I Do Not Know");
  const [fitz, setFitz] = useState<string>("III");
  const [notes, setNotes] = useState("");
  const [tone, setTone] = useState("b");
  const [client, setClient] = useState("");
  const [imgPreview, setImgPreview] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [activeStep, setActiveStep] = useState(-1);
  const [resultId, setResultId] = useState<number | null>(null);
  const [resultLabel, setResultLabel] = useState<string | null>(null);

  const l1 = useMemo(() => level1(hair), [hair]);
  const l2 = useMemo(() => level2(fitz), [fitz]);
  const cands = useMemo(() => candidateSet(hair, fitz), [hair, fitz]);
  const engineModelIds = enabledModelIds(models, engine);
  const empty = cands.length === 0;
  const noModels = engineModelIds.length === 0;

  function onFile(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => setImgPreview(reader.result as string);
    reader.readAsDataURL(file);
  }

  function run() {
    if (empty || noModels || running) return;
    setRunning(true);
    setResultId(null);
    setResultLabel(null);
    let i = 0;
    const timer = window.setInterval(() => {
      setActiveStep(i);
      i += 1;
      if (i >= PIPELINE.length) {
        window.clearInterval(timer);
        const a = createAnalysis({ client, hair, fitzpatrick: fitz, notes, tone });
        setRunning(false);
        setActiveStep(PIPELINE.length);
        setResultId(a.id);
        setResultLabel(a.ai_result);
      }
    }, 360);
  }

  const engineBanner =
    engine.mode === "single"
      ? `Single model — ${modelName(engine.primary)}`
      : `${engine.strategy} across ${engineModelIds.map((id) => modelName(id).split(" ")[0]).join(", ")}`;

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold">Start Analysis</h1>
        <p className="text-sm text-slate-500">Upload a face photo and provide the two self-report inputs.</p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Inputs */}
        <Card>
          <SectionTitle>1 · Inputs</SectionTitle>

          <div className="mb-3">
            <Label>Client name (optional)</Label>
            <input className={inputClass()} value={client} onChange={(e) => setClient(e.target.value)} placeholder="e.g. New Client" />
          </div>

          <div className="mb-3">
            <Label>Face photo — auto-cropped to face only (no hair / neck / background)</Label>
            <input type="file" accept="image/jpeg,image/png,image/heic" onChange={onFile} className="block w-full text-sm text-slate-600 file:mr-3 file:rounded-lg file:border-0 file:bg-teal-50 file:px-3 file:py-2 file:text-sm file:text-teal-700" />
            <div className="mt-2 flex items-center gap-3">
              <div className="h-20 w-16 overflow-hidden rounded-lg border border-slate-200 bg-slate-50">
                {imgPreview ? <img src={imgPreview} alt="uploaded face" className="h-full w-full object-cover" /> : <FaceSvg tone={tone} className="h-full w-full" />}
              </div>
              <div className="text-xs text-slate-500">
                Overlay skin-tone (demo placeholder):
                <select className={inputClass("mt-1 w-32")} value={tone} onChange={(e) => setTone(e.target.value)}>
                  {Object.keys(SKIN_TONES).map((k) => (
                    <option key={k} value={k}>
                      Tone {k.toUpperCase()}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          <div className="mb-3">
            <Label>Natural hair colour at age 17–20 (most reliable input)</Label>
            <select className={inputClass()} value={hair} onChange={(e) => setHair(e.target.value)}>
              {HAIR_COLOURS.map((h) => (
                <option key={h}>{h}</option>
              ))}
            </select>
          </div>

          <div className="mb-3">
            <Label>Fitzpatrick skin type</Label>
            <select className={inputClass()} value={fitz} onChange={(e) => setFitz(e.target.value)}>
              {FITZPATRICK.map((f) => (
                <option key={f.type} value={f.type}>
                  Type {f.type} — {f.label}
                </option>
              ))}
            </select>
          </div>

          <div className="mb-3">
            <Label>Additional details — skin, hair, eyes (free form, optional)</Label>
            <textarea className={inputClass()} rows={3} value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="e.g. hair showed reddish tints in sunlight; freckles on cheeks; sunburst eye pattern…" />
            <p className="mt-1 text-xs text-slate-500">
              Weak supporting context only. Per methodology, self-reported traits (blushing, eye pattern) never override rule-outs or overlay comparisons.
            </p>
          </div>

          <div className="mb-3 rounded-lg border border-dashed border-slate-300 bg-slate-50 px-3 py-2 text-sm">
            <b>Engine (admin-configured):</b> {engineBanner}
            <span className="text-slate-400"> · managed under Admin → Model Configuration</span>
          </div>

          <Button className="w-full" disabled={empty || noModels || running} onClick={run}>
            {running ? "Analysing…" : "▶ Run analysis"}
          </Button>
          {empty && (
            <p className="mt-2 text-xs text-rose-600">
              Run disabled — <b>CONFLICTING_INPUTS</b>: the hair and Fitzpatrick rule-outs share no palette. Fix the inputs (this case would go to human review).
            </p>
          )}
          {noModels && !empty && <p className="mt-2 text-xs text-rose-600">No models enabled — ask an Admin to enable a model.</p>}
        </Card>

        {/* Live rule-out preview + pipeline */}
        <Card>
          <SectionTitle>Live rule-out preview</SectionTitle>
          <p className="mb-2 text-xs text-slate-500">Deterministic layers update as you change inputs — the AI result is constrained to this set.</p>

          <Label>Level 1 — hair ({hair})</Label>
          <div className="mb-3 flex flex-wrap gap-1">
            {l1.map((p) => (
              <Chip key={p}>{p}</Chip>
            ))}
          </div>

          <Label>Level 2 — Fitzpatrick (Type {fitz})</Label>
          <div className="mb-3 flex flex-wrap gap-1">
            {l2.map((p) => (
              <Chip key={p}>{p}</Chip>
            ))}
          </div>

          <Label>Candidate set (intersection)</Label>
          <div className="mb-4 flex flex-wrap gap-1">
            {cands.length ? (
              cands.map((p) => (
                <Chip key={p} tone="ok">
                  {p}
                </Chip>
              ))
            ) : (
              <Chip tone="bad">EMPTY — conflicting inputs, human review required</Chip>
            )}
          </div>

          <SectionTitle>Pipeline</SectionTitle>
          <ul className="space-y-1">
            {PIPELINE.map((s, i) => {
              const done = activeStep > i;
              const active = running && activeStep === i;
              return (
                <li key={s} className={cn("flex items-start gap-2 text-sm", done ? "text-emerald-700" : active ? "text-amber-700" : "text-slate-500")}>
                  <span className="mt-0.5 w-4 text-center">{done ? "✓" : active ? "◌" : "○"}</span>
                  {s}
                </li>
              );
            })}
          </ul>

          {resultId && resultLabel && (
            <div className="mt-3 rounded-lg border border-dashed border-emerald-300 bg-emerald-50 px-3 py-2 text-sm text-emerald-800">
              <b>✔ Recommended: {resultLabel}</b> — submitted to the Colour Analysis Expert review queue.
              <div className="mt-2">
                <Button sm onClick={() => navigate(`/analyses/${resultId}`)}>
                  Open analysis #{resultId} →
                </Button>
              </div>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
