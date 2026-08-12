/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Override the engine API base (default same-origin "/api"). */
  readonly VITE_API_BASE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
