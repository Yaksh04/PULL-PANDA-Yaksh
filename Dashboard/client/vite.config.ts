import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
      // This allows access to shared code, assuming it's one level up
      "@shared": path.resolve(__dirname, "../shared"),
    },
  },
  // Since this file is IN client/, the root is the current directory
  root: ".",
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
  server: {
    port: 3000,
  },
});
