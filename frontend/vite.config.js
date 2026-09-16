import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Phase 0: backend runs on 8000; proxy keeps the frontend
      // talking to relative /api paths instead of hard-coding a host.
      "/api": "http://localhost:8000"
    }
  }
});
