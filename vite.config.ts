import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "path";

// @ts-expect-error process is a nodejs global
const host = process.env.TAURI_DEV_HOST;

export default defineConfig(async () => ({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  clearScreen: false,
  server: {
    port: 1421,
    strictPort: true,
    host: host || false,
    hmr: host
      ? { protocol: "ws", host, port: 1422 }
      : undefined,
    watch: { ignored: ["**/src-tauri/**"] },
    proxy: {
      "/api": "http://127.0.0.1:8081",
      "/health": "http://127.0.0.1:8081",
      "/previews": "http://127.0.0.1:8081",
    },
  },
}));
