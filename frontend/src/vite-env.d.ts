/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Override the API origin in a production build. Empty in dev (Vite proxies /api). */
  readonly VITE_API_BASE?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
