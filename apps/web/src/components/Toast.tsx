import { createContext, useCallback, useContext, useState } from "react";
import type { ReactNode } from "react";

interface ToastState {
  toast: (msg: string) => void;
}

const ToastContext = createContext<ToastState | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [msg, setMsg] = useState<string | null>(null);
  const toast = useCallback((m: string) => {
    setMsg(m);
    window.setTimeout(() => setMsg(null), 3200);
  }, []);
  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      {msg && (
        <div
          role="status"
          className="fixed bottom-6 right-6 z-50 max-w-sm rounded-xl bg-slate-900/90 px-4 py-3 text-sm text-white shadow-2xl backdrop-blur"
        >
          {msg}
        </div>
      )}
    </ToastContext.Provider>
  );
}

export function useToast(): ToastState {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}
