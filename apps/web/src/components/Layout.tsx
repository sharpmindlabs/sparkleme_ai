import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { useData } from "../lib/store";
import { ROLE_LABELS } from "../types";
import { Button, cn } from "./ui";

interface NavItem {
  to: string;
  icon: string;
  label: string;
  minRole: "ANALYST" | "EXPERT" | "ADMIN";
}

const NAV: NavItem[] = [
  { to: "/", icon: "▦", label: "Dashboard", minRole: "ANALYST" },
  { to: "/analyses", icon: "≣", label: "Analyses", minRole: "ANALYST" },
  { to: "/start", icon: "＋", label: "Start Analysis", minRole: "ANALYST" },
  { to: "/settings", icon: "⚙", label: "Settings", minRole: "EXPERT" },
  { to: "/admin", icon: "♛", label: "Admin", minRole: "ADMIN" },
];

function visible(role: string, min: NavItem["minRole"]): boolean {
  if (min === "ADMIN") return role === "ADMIN";
  if (min === "EXPERT") return role === "ADMIN" || role === "EXPERT";
  return true;
}

export function Layout() {
  const { session, logout, demoAuth } = useAuth();
  const { demoData } = useData();
  const navigate = useNavigate();
  if (!session) return null;
  const role = session.user.role;

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-900">
      <aside className="fixed inset-y-0 left-0 flex w-56 flex-col border-r border-white/10 bg-[#063442] px-3 py-5 text-sky-100 print:hidden">
        <div className="px-2 pb-5 text-lg font-bold text-white">
          ✨ Sparkle
          <span className="bg-gradient-to-r from-amber-300 to-cyan-300 bg-clip-text text-transparent">Me</span>
        </div>
        <nav className="flex flex-col gap-0.5">
          {NAV.filter((n) => visible(role, n.minRole)).map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.to === "/"}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm transition",
                  isActive ? "bg-white/10 font-semibold text-white" : "text-sky-200 hover:bg-white/5 hover:text-white",
                )
              }
            >
              <span className="w-4 text-center">{n.icon}</span>
              {n.label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto border-t border-white/10 pt-3 text-xs">
          <b className="block text-white">{session.user.name}</b>
          <span className="text-sky-200">{ROLE_LABELS[role]}</span>
          <br />
          <span className="text-sky-300/80">{session.user.email}</span>
          <Button
            variant="gray"
            sm
            className="mt-2 w-full"
            onClick={() => {
              logout();
              navigate("/login");
            }}
          >
            Sign out
          </Button>
        </div>
      </aside>

      <main className="ml-56 flex-1 px-6 py-6 print:ml-0">
        {(demoData || demoAuth) && (
          <div className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-2 text-xs text-amber-800 print:hidden">
            Demo mode — the API at <code>{import.meta.env.VITE_API_BASE ?? "http://localhost:8000"}</code> is not reachable, so data is served from an in-memory mock. Wiring is live and will use the server the moment it responds.
          </div>
        )}
        <Outlet />
      </main>
    </div>
  );
}
