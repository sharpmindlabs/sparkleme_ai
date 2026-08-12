import { Navigate, Route, Routes } from "react-router-dom";
import type { ReactNode } from "react";
import { useAuth } from "./lib/auth";
import { Layout } from "./components/Layout";
import { Login } from "./pages/Login";
import { Dashboard } from "./pages/Dashboard";
import { StartAnalysis } from "./pages/StartAnalysis";
import { AnalysesList } from "./pages/AnalysesList";
import { AnalysisDetail } from "./pages/AnalysisDetail";
import { Review } from "./pages/Review";
import { Settings } from "./pages/Settings";
import { Admin } from "./pages/Admin";
import { EmptyState } from "./components/ui";

/** Redirect to /login unless authenticated. */
function RequireAuth({ children }: { children: ReactNode }) {
  const { session } = useAuth();
  if (!session) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

/** Gate a route to a minimum role; render a locked notice otherwise. */
function RequireRole({ level, children }: { level: "EXPERT" | "ADMIN"; children: ReactNode }) {
  const { session } = useAuth();
  const role = session?.user.role;
  const ok = level === "ADMIN" ? role === "ADMIN" : role === "ADMIN" || role === "EXPERT";
  if (!ok) return <EmptyState>🔒 You do not have access to this area.</EmptyState>;
  return <>{children}</>;
}

export default function App() {
  const { session } = useAuth();
  return (
    <Routes>
      <Route path="/login" element={session ? <Navigate to="/" replace /> : <Login />} />
      <Route
        element={
          <RequireAuth>
            <Layout />
          </RequireAuth>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="/analyses" element={<AnalysesList />} />
        <Route path="/analyses/:id" element={<AnalysisDetail />} />
        <Route path="/analyses/:id/review" element={<RequireRole level="EXPERT"><Review /></RequireRole>} />
        <Route path="/start" element={<StartAnalysis />} />
        <Route path="/settings" element={<RequireRole level="EXPERT"><Settings /></RequireRole>} />
        <Route path="/admin" element={<RequireRole level="ADMIN"><Admin /></RequireRole>} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
