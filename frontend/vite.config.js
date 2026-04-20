// vite.config.js — Vite build configuration.
// The proxy routes /api/* to the FastAPI backend during development,
// so the frontend never hard-codes the backend URL in browser code.

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Forward all /api calls to the FastAPI backend
      "/api": {
        target: "http://localhost:30000",
        changeOrigin: true,
      },
    },
  },
});
