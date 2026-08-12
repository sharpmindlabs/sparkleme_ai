// Auth context: holds the current session (decoded from the stored JWT), logs
// in against the API, and falls back to a minted demo token when the backend is
// unreachable so the app remains explorable offline.

import { createContext, useCallback, useContext, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { api, ApiError, getToken, setToken } from "../api";
import { decodeJwt, mintDemoToken } from "./jwt";
import { DEMO_LOGINS, USERS_SEED } from "./mock";
import type { Role, Session } from "../types";

interface AuthState {
  session: Session | null;
  /** True when authenticated via a locally-minted demo token (no backend). */
  demoAuth: boolean;
  login: (email: string, password: string, demoRole?: Role) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

function sessionFromToken(token: string): Session | null {
  const claims = decodeJwt(token);
  if (!claims) return null;
  return { token, user: { name: claims.name, email: claims.email, role: claims.role } };
}

/** Thrown for suspended users so the login screen can show the support message. */
export class SuspendedError extends Error {
  constructor() {
    super("Your account is suspended. Contact support@sparkleme.app to restore access.");
    this.name = "SuspendedError";
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(() => {
    const t = getToken();
    return t ? sessionFromToken(t) : null;
  });
  const [demoAuth, setDemoAuth] = useState(false);

  const login = useCallback(async (email: string, password: string, demoRole?: Role) => {
    try {
      const s = await api.login(email, password);
      setToken(s.token);
      setSession(sessionFromToken(s.token) ?? s);
      setDemoAuth(false);
    } catch (e) {
      // Only fall back to demo auth when the server is unreachable (network),
      // never when it actively rejected the credentials.
      if (e instanceof ApiError && e.network) {
        const role = demoRole ?? "ANALYST";
        const match = DEMO_LOGINS.find((d) => d.role === role);
        const suspended = USERS_SEED.find((u) => u.email === email && u.status === "Suspended");
        if (suspended) throw new SuspendedError();
        const name = match?.name ?? email.split("@")[0];
        const useEmail = match?.email ?? email;
        const token = mintDemoToken({ email: useEmail, name, role, status: "Active" });
        setToken(token);
        setSession({ token, user: { name, email: useEmail, role } });
        setDemoAuth(true);
        return;
      }
      throw e;
    }
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    setSession(null);
    setDemoAuth(false);
  }, []);

  const value = useMemo<AuthState>(
    () => ({ session, demoAuth, login, logout }),
    [session, demoAuth, login, logout],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export function roleAtLeast(role: Role, level: "ANALYST" | "EXPERT" | "ADMIN"): boolean {
  if (level === "ADMIN") return role === "ADMIN";
  if (level === "EXPERT") return role === "ADMIN" || role === "EXPERT";
  return true;
}
