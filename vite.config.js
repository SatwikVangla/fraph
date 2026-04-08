import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    chunkSizeWarningLimit: 950,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (
            id.includes("node_modules/three") ||
            id.includes("node_modules/@react-three/fiber") ||
            id.includes("node_modules/@react-three/drei")
          ) {
            return "three-vendor";
          }
          if (id.includes("/src/components/HomeTitleScene.jsx")) {
            return "home-title-scene";
          }
        },
      },
    },
  },
  server: {
    proxy: {
      "/upload": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/fraud": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/compare": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/train": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
