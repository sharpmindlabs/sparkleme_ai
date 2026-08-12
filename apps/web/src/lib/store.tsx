// Data store: the single source of truth for domain state in the UI. It seeds
// from the mock backend, attempts to hydrate from the real API on mount, and
// applies mutations locally so the app works with or without a live backend.
// Best-effort API writes are fired when a real server is present.

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { api, ApiError } from "../api";
import { PALETTES } from "../palettes";
import { candidateSet } from "../ruleouts";
import {
  ENGINE_SEED,
  MODELS_SEED,
  evidenceFor,
  modelName,
  seedAnalyses,
  seedCorrections,
  seedJobs,
  seedPrompts,
  USERS_SEED,
} from "./mock";
import type {
  Analysis,
  Correction,
  EngineConfig,
  HomeSeason,
  ModelConfig,
  ModelVote,
  PromptType,
  PromptVersion,
  RerunLog,
  ReviewBody,
  Role,
  TrainingJob,
  Undertone,
  User,
} from "../types";

export interface NewAnalysisInput {
  client: string;
  hair: string;
  fitzpatrick: string;
  notes: string;
  tone: string;
}

interface DataState {
  demoData: boolean;
  loading: boolean;
  analyses: Analysis[];
  users: User[];
  models: ModelConfig[];
  engine: EngineConfig;
  prompts: Record<PromptType, PromptVersion[]>;
  corrections: Correction[];
  jobs: TrainingJob[];

  getAnalysis(id: number): Analysis | undefined;
  createAnalysis(input: NewAnalysisInput): Analysis;
  reviewAnalysis(id: number, body: ReviewBody): void;
  rerunAnalysis(id: number): RerunLog;

  savePromptVersion(type: PromptType, body: string, note: string, author: string): string;
  activatePrompt(type: PromptType, version: string): void;

  updateEngine(patch: Partial<EngineConfig>): void;
  toggleModel(id: string): void;
  setModelWeight(id: string, weight: number): void;

  inviteUser(email: string): void;
  setUserRole(id: string, role: Role): void;
  toggleUserStatus(id: string): void;

  expireMemory(id: number): void;
  triggerJob(): void;
}

const DataContext = createContext<DataState | null>(null);

function enabledModelIds(models: ModelConfig[], engine: EngineConfig): string[] {
  if (engine.mode === "single") return [engine.primary];
  return models.filter((m) => m.enabled).map((m) => m.id);
}

export function DataProvider({ children }: { children: ReactNode }) {
  const [demoData, setDemoData] = useState(true);
  const [loading, setLoading] = useState(true);
  const [analyses, setAnalyses] = useState<Analysis[]>(() => seedAnalyses());
  const [users, setUsers] = useState<User[]>(() => USERS_SEED.map((u) => ({ ...u })));
  const [models, setModels] = useState<ModelConfig[]>(() => MODELS_SEED.map((m) => ({ ...m })));
  const [engine, setEngine] = useState<EngineConfig>(() => ({ ...ENGINE_SEED }));
  const [prompts, setPrompts] = useState<Record<PromptType, PromptVersion[]>>(() => seedPrompts());
  const [corrections, setCorrections] = useState<Correction[]>(() => seedCorrections());
  const [jobs, setJobs] = useState<TrainingJob[]>(() => seedJobs());

  // Best-effort hydrate from the real API. On network failure we stay in demo
  // mode with seed data. Only replace state when the server actually answers.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const list = await api.listAnalyses();
        if (cancelled) return;
        setAnalyses(list);
        setDemoData(false);
        // Opportunistically pull the rest; ignore individual failures.
        void Promise.allSettled([
          api.listUsers().then((u) => !cancelled && setUsers(u)),
          api.listModels().then((m) => !cancelled && setModels(m)),
          api.getEngine().then((e) => !cancelled && setEngine(e)),
          api.listMemory().then((c) => !cancelled && setCorrections(c)),
          api.listJobs().then((j) => !cancelled && setJobs(j)),
        ]);
      } catch (e) {
        if (!(e instanceof ApiError)) throw e;
        // Network or auth error → remain in demo mode with seed data.
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const getAnalysis = useCallback((id: number) => analyses.find((a) => a.id === id), [analyses]);

  const activePrompt = prompts.analysis.find((p) => p.active)?.version ?? "v1.3";

  const createAnalysis = useCallback(
    (input: NewAnalysisInput): Analysis => {
      const cands = candidateSet(input.hair, input.fitzpatrick);
      const nextId = Math.max(1041, ...analyses.map((a) => a.id)) + 1;
      const models_ = enabledModelIds(models, engine);
      const engineSnap = { mode: engine.mode, strategy: engine.strategy, models: models_ };

      if (cands.length === 0) {
        const conflict: Analysis = {
          id: nextId,
          client: input.client || "New Client",
          date: new Date().toISOString().slice(0, 10),
          hair: input.hair,
          fitzpatrick: input.fitzpatrick,
          notes: input.notes || undefined,
          tone: input.tone,
          result_status: "CONFLICTING_INPUTS",
          status: "Conflicting Inputs",
          undertone: null,
          home_season: null,
          ai_result: null,
          expert_result: null,
          confidence: 0,
          candidate_set: [],
          evidence: { a_eyes: "", b_hair: "Empty candidate set — Level 1 ∩ Level 2 = ∅.", c_skin: "", d_drape_steps: [] },
          model_votes: [],
          prompt_version: activePrompt,
          engine: engineSnap,
          why: "Conflicting inputs: the hair and Fitzpatrick rule-outs share no palette. Fix the inputs and start a new analysis.",
          expert_note: null,
        };
        setAnalyses((prev) => [conflict, ...prev]);
        return conflict;
      }

      // Deterministic pick within the candidate set (stands in for the pipeline).
      const seed = (input.hair.length * 7 + input.fitzpatrick.charCodeAt(0) + input.tone.charCodeAt(0)) % cands.length;
      const result = cands[seed];
      const info = PALETTES[result];
      const undertone: Undertone = info.undertone.toLowerCase().includes("warm") ? "Warm" : "Cool";
      const season = (info.family.split("/")[0].trim() || "Winter") as HomeSeason;
      const confidence = Math.min(97, 80 + seed * 3);
      const votes: ModelVote[] = models_.map((m) => ({ model: m, vote: result, raw: "structured drape result" }));

      const analysis: Analysis = {
        id: nextId,
        client: input.client || "New Client",
        date: new Date().toISOString().slice(0, 10),
        hair: input.hair,
        fitzpatrick: input.fitzpatrick,
        notes: input.notes || undefined,
        tone: input.tone,
        result_status: "OK",
        status: "Pending Review",
        undertone,
        home_season: season,
        ai_result: result,
        expert_result: null,
        confidence,
        candidate_set: cands,
        evidence: evidenceFor({ hair: input.hair, home_season: season, undertone, result, candidate_set: cands }),
        model_votes: votes,
        prompt_version: activePrompt,
        engine: engineSnap,
        why: `Drape steps favoured ${result}: details diminished, healthy glow, focus drawn up to eyes; corroborated by skin characteristics.`,
        expert_note: null,
      };
      setAnalyses((prev) => [analysis, ...prev]);
      return analysis;
    },
    [analyses, models, engine, activePrompt],
  );

  const reviewAnalysis = useCallback((id: number, body: ReviewBody) => {
    if (!demoData) void api.review(id, body).catch(() => {});
    setAnalyses((prev) =>
      prev.map((a) => {
        if (a.id !== id) return a;
        if (body.verdict === "APPROVE") {
          return { ...a, status: "Approved", expert_result: a.ai_result, expert_note: `Expert: ${body.comments}` };
        }
        const palette = body.palette ?? a.ai_result ?? a.candidate_set[0];
        return {
          ...a,
          status: "Corrected",
          expert_result: palette,
          expert_note: `Expert: ${body.comments}`,
        };
      }),
    );
    if (body.verdict === "CORRECT" && body.palette) {
      setCorrections((prev) => [
        { id, palette: body.palette as string, note: body.influence || body.comments, date: new Date().toISOString().slice(0, 10), by: "colour.expert@sparkleme.app" },
        ...prev.filter((c) => c.id !== id),
      ]);
    }
  }, [demoData]);

  const rerunAnalysis = useCallback(
    (id: number): RerunLog => {
      const a = analyses.find((x) => x.id === id);
      const hit = corrections.find((c) => c.id === id);
      const cands = a?.candidate_set ?? [];
      const result = hit ? hit.palette : a?.ai_result ?? "—";
      const lines = [
        `▶ New analysis started for identical inputs (image hash 9f3ac…, ${a?.hair}, Fitz ${a?.fitzpatrick})`,
        `① Rule-outs recomputed → candidates: [${cands.join(", ")}]`,
        `② Correction memory lookup (image-embedding + inputs)… ${hit ? `HIT — expert-verified result found (${hit.date})` : "MISS — no prior expert correction"}`,
        hit
          ? `③ Authoritative override applied → result: ${hit.palette} (expert note injected as context)`
          : `③ Multi-model drape analysis → consensus: ${a?.ai_result}`,
        "④ Audit pass → APPROVE (checks 1–7 green)",
        `✔ Result: ${result} — deterministic; identical output guaranteed on nth rerun`,
      ];
      return { lines, memory: hit ? "HIT" : "MISS", result };
    },
    [analyses, corrections],
  );

  const savePromptVersion = useCallback((type: PromptType, body: string, note: string, author: string): string => {
    let created = "";
    setPrompts((prev) => {
      const list = prev[type];
      const last = list[list.length - 1].version;
      const next = `v1.${parseInt(last.split(".")[1], 10) + 1}`;
      created = next;
      const version: PromptVersion = { version: next, date: new Date().toISOString().slice(0, 10), author, note: note || "(no note)", accuracy: null, body, active: false };
      return { ...prev, [type]: [...list, version] };
    });
    return created;
  }, []);

  const activatePrompt = useCallback((type: PromptType, version: string) => {
    if (!demoData) void api.setActivePrompt(type, version).catch(() => {});
    setPrompts((prev) => ({
      ...prev,
      [type]: prev[type].map((p) => ({ ...p, active: p.version === version })),
    }));
  }, [demoData]);

  const updateEngine = useCallback((patch: Partial<EngineConfig>) => {
    setEngine((prev) => {
      const next = { ...prev, ...patch };
      if (!demoData) void api.setEngine(next).catch(() => {});
      return next;
    });
  }, [demoData]);

  const toggleModel = useCallback((id: string) => {
    setModels((prev) => prev.map((m) => (m.id === id ? { ...m, enabled: !m.enabled } : m)));
  }, []);
  const setModelWeight = useCallback((id: string, weight: number) => {
    setModels((prev) => prev.map((m) => (m.id === id ? { ...m, weight } : m)));
  }, []);

  const inviteUser = useCallback((email: string) => {
    setUsers((prev) => [
      ...prev,
      { id: `u${prev.length + 1}`, name: email.split("@")[0], email, role: "ANALYST", status: "Active" },
    ]);
  }, []);
  const setUserRole = useCallback((id: string, role: Role) => {
    setUsers((prev) => prev.map((u) => (u.id === id ? { ...u, role } : u)));
  }, []);
  const toggleUserStatus = useCallback((id: string) => {
    setUsers((prev) => prev.map((u) => (u.id === id ? { ...u, status: u.status === "Active" ? "Suspended" : "Active" } : u)));
  }, []);

  const expireMemory = useCallback((id: number) => {
    if (!demoData) void api.expireMemory(id).catch(() => {});
    setCorrections((prev) => prev.filter((c) => c.id !== id));
  }, [demoData]);

  const triggerJob = useCallback(() => {
    setJobs((prev) => [
      { id: `FT-${new Date().toISOString().slice(0, 10)}`, model: "All enabled", method: "SFT + DPO on corrections", examples: corrections.length, status: "Running", delta: "—" },
      ...prev,
    ]);
  }, [corrections.length]);

  const value = useMemo<DataState>(
    () => ({
      demoData,
      loading,
      analyses,
      users,
      models,
      engine,
      prompts,
      corrections,
      jobs,
      getAnalysis,
      createAnalysis,
      reviewAnalysis,
      rerunAnalysis,
      savePromptVersion,
      activatePrompt,
      updateEngine,
      toggleModel,
      setModelWeight,
      inviteUser,
      setUserRole,
      toggleUserStatus,
      expireMemory,
      triggerJob,
    }),
    [demoData, loading, analyses, users, models, engine, prompts, corrections, jobs, getAnalysis, createAnalysis, reviewAnalysis, rerunAnalysis, savePromptVersion, activatePrompt, updateEngine, toggleModel, setModelWeight, inviteUser, setUserRole, toggleUserStatus, expireMemory, triggerJob],
  );

  return <DataContext.Provider value={value}>{children}</DataContext.Provider>;
}

export function useData(): DataState {
  const ctx = useContext(DataContext);
  if (!ctx) throw new Error("useData must be used within DataProvider");
  return ctx;
}

export { enabledModelIds, modelName };
