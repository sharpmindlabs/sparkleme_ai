import { useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { SuspendedError, useAuth } from "../lib/auth";
import { ApiError } from "../api";
import { Button, inputClass, Label } from "../components/ui";
import { ROLE_LABELS } from "../types";
import type { Role } from "../types";

const DEMO_ROLES: Role[] = ["ADMIN", "EXPERT", "ANALYST"];

export function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("prabhu.balakrishnan@resdevtax.com");
  const [password, setPassword] = useState("demo1234");
  const [role, setRole] = useState<Role>("ADMIN");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(email, password, role);
      navigate("/");
    } catch (err) {
      if (err instanceof SuspendedError) setError(err.message);
      else if (err instanceof ApiError && err.status === 403) setError("Your account is suspended. Contact support@sparkleme.app.");
      else if (err instanceof ApiError) setError("Sign-in failed. Check your email and password.");
      else setError(err instanceof Error ? err.message : "Sign-in failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[radial-gradient(1200px_600px_at_20%_0%,#0a9396,#023545)] px-4">
      <form
        onSubmit={submit}
        className="w-full max-w-sm rounded-3xl border border-white/60 bg-white/85 p-8 shadow-2xl backdrop-blur"
      >
        <div className="text-2xl font-bold text-slate-900">
          ✨ Sparkle
          <span className="bg-gradient-to-r from-amber-500 to-cyan-500 bg-clip-text text-transparent">Me</span>
        </div>
        <p className="mb-5 text-sm text-slate-500">Virtual colour analysis platform</p>

        {error && (
          <div role="alert" className="mb-3 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
            {error}
          </div>
        )}

        <div className="mb-3">
          <Label>Email</Label>
          <input className={inputClass()} value={email} onChange={(e) => setEmail(e.target.value)} type="email" autoComplete="username" />
        </div>
        <div className="mb-3">
          <Label>Password</Label>
          <input className={inputClass()} value={password} onChange={(e) => setPassword(e.target.value)} type="password" autoComplete="current-password" />
        </div>
        <div className="mb-4">
          <Label>Sign in as (demo role)</Label>
          <select className={inputClass()} value={role} onChange={(e) => setRole(e.target.value as Role)}>
            {DEMO_ROLES.map((r) => (
              <option key={r} value={r}>
                {ROLE_LABELS[r]}
              </option>
            ))}
          </select>
        </div>

        <Button type="submit" className="w-full" disabled={busy}>
          {busy ? "Signing in…" : "Sign in"}
        </Button>
        <p className="mt-3 text-center text-xs text-slate-400">
          SSO-ready · The demo role is used only when the backend is offline; a real JWT's role claim wins.
        </p>
      </form>
    </div>
  );
}
