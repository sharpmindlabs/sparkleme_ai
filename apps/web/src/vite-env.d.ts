/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base URL of the SparkleMe REST API. Default: http://localhost:8000 */
  readonly VITE_API_BASE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
