import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@features": "/src/features",
      "@shared": "/src/shared",
      "@lib": "/src/lib",
      "@app": "/src/app"
    },
  },
});
