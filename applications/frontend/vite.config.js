import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In development (npm run dev) Vite forwards /api/* to the APIs that Docker Compose publishes on your computer.
// In the container nginx does that job (Compose), or the Kubernetes Ingress does (Kubernetes).
export default defineConfig({
  plugins: [react()],
  define: { __APP_VERSION__: JSON.stringify(process.env.APP_VERSION || "dev") },
  server: {
    port: 5173,
    proxy: {
      "/api/users": "http://localhost:3000",
      "/api/books": "http://localhost:8082",
      "/api/stats": "http://localhost:8000",
      "/api/status": "http://localhost:8083",
    },
  },
});
