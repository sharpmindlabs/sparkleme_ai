import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev proxy: forward /api and /api/image to the FastAPI engine on :8000.
// In production the built UI is served by the engine itself (same origin),
// so requests to /api resolve without a proxy. Override the base at runtime
// with VITE_API_BASE if the engine lives elsewhere.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
