import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  // When building for Electron, use relative paths so file:// protocol works
  const isElectronBuild = env.BUILD_TARGET === "electron";

  return {
    // relative base so Electron file:// loads assets correctly
    base: isElectronBuild ? "./" : "/",

    plugins: [react()],

    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },

    server: {
      port: 5173,
      proxy: {
        "/api": {
          target: env.VITE_API_BASE_URL?.replace("/api/v1", "") || "http://localhost:8000",
          changeOrigin: true,
        },
      },
    },

    build: {
      outDir: "dist",
      sourcemap: false,
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ["react", "react-dom", "react-router-dom"],
            query: ["@tanstack/react-query"],
            charts: ["recharts"],
          },
        },
      },
    },

    define: {
      __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
    },
  };
});
