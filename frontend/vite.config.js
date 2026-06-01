import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The backend base URL is read from VITE_API_BASE at build/run time.
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/test/setup.js",
  },
});
