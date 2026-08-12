// Small, consistent design-system primitives used across every page.

import type { ButtonHTMLAttributes, ReactNode } from "react";
import type { AnalysisStatus } from "../types";

export function cn(...parts: (string | false | null | undefined)[]): string {
  return parts.filter(Boolean).join(" ");
}

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className={cn("rounded-2xl border border-slate-200 bg-white p-4 shadow-sm", className)}>
      {children}
    </div>
  );
}

export function SectionTitle({ children }: { children: ReactNode }) {
  return <h2 className="mb-2 text-base font-semibold text-slate-800">{children}</h2>;
}

export function Label({ children }: { children: ReactNode }) {
  return <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">{children}</div>;
}

type ChipTone = "ok" | "warn" | "bad" | "info" | "plain" | "gray";

const CHIP_TONES: Record<ChipTone, string> = {
  ok: "bg-emerald-100 text-emerald-700",
  warn: "bg-amber-100 text-amber-700",
  bad: "bg-rose-100 text-rose-700",
  info: "bg-sky-100 text-sky-700",
  plain: "bg-teal-100 text-teal-700",
  gray: "bg-slate-100 text-slate-600",
};

export function Chip({ children, tone = "plain", className }: { children: ReactNode; tone?: ChipTone; className?: string }) {
  return (
    <span className={cn("inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold", CHIP_TONES[tone], className)}>
      {children}
    </span>
  );
}

const STATUS_TONES: Record<AnalysisStatus, ChipTone> = {
  Approved: "ok",
  Finalized: "ok",
  "Pending Review": "warn",
  Corrected: "info",
  "Needs Human Review": "bad",
  "Conflicting Inputs": "bad",
  Running: "gray",
};

export function StatusChip({ status }: { status: AnalysisStatus }) {
  return <Chip tone={STATUS_TONES[status] ?? "plain"}>{status}</Chip>;
}

type ButtonVariant = "primary" | "ghost" | "gray" | "green" | "red" | "amber";

const BUTTON_VARIANTS: Record<ButtonVariant, string> = {
  primary: "bg-gradient-to-br from-teal-600 to-cyan-500 text-white shadow-sm hover:brightness-110",
  ghost: "border border-teal-600 text-teal-700 hover:bg-teal-50",
  gray: "bg-slate-100 text-slate-700 hover:bg-slate-200",
  green: "bg-emerald-600 text-white hover:bg-emerald-700",
  red: "bg-rose-600 text-white hover:bg-rose-700",
  amber: "bg-amber-500 text-white hover:bg-amber-600",
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  sm?: boolean;
}

export function Button({ variant = "primary", sm, className, children, ...rest }: ButtonProps) {
  return (
    <button
      {...rest}
      className={cn(
        "inline-flex items-center justify-center gap-1.5 rounded-lg font-medium transition disabled:cursor-not-allowed disabled:opacity-50",
        sm ? "px-2.5 py-1 text-xs" : "px-3.5 py-2 text-sm",
        BUTTON_VARIANTS[variant],
        className,
      )}
    >
      {children}
    </button>
  );
}

export function Kpi({ label, value, sub, subTone }: { label: string; value: ReactNode; sub?: string; subTone?: "up" | "down" | "muted" }) {
  return (
    <Card>
      <div className="text-xs font-medium text-slate-500">{label}</div>
      <div className="mt-1 text-2xl font-bold text-slate-900">{value}</div>
      {sub && (
        <div className={cn("mt-1 text-xs", subTone === "up" ? "text-emerald-600" : subTone === "down" ? "text-rose-600" : "text-slate-400")}>
          {sub}
        </div>
      )}
    </Card>
  );
}

export function EmptyState({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-12 text-center text-sm text-slate-500">
      {children}
    </div>
  );
}

export function Spinner({ className }: { className?: string }) {
  return (
    <svg className={cn("h-5 w-5 animate-spin text-teal-600", className)} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
    </svg>
  );
}

export function Meter({ pct, className }: { pct: number; className?: string }) {
  return (
    <div className={cn("h-2 overflow-hidden rounded-full bg-slate-100", className)}>
      <div className="h-full rounded-full bg-gradient-to-r from-teal-600 to-cyan-500" style={{ width: `${Math.max(0, Math.min(100, pct))}%` }} />
    </div>
  );
}

export function inputClass(extra?: string): string {
  return cn(
    "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-100",
    extra,
  );
}
