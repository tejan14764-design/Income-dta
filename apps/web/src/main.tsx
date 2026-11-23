import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, HashRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { Toaster } from "react-hot-toast";
import App from "./App";
import { initApiUrl } from "@/services/api";
import "@/styles/globals.css";

type ErrorBoundaryProps = { children: React.ReactNode };
type ErrorBoundaryState = { error: Error | null };

class AppErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error("INCOME renderer crashed", error, info);
  }

  render() {
    if (this.state.error) {
      return (
        <div
          style={{
            minHeight: "100vh",
            background: "#0f172a",
            color: "#f8fafc",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: 24,
            fontFamily: "system-ui, sans-serif",
          }}
        >
          <div
            style={{
              maxWidth: 720,
              width: "100%",
              background: "#1e293b",
              border: "1px solid #334155",
              borderRadius: 12,
              padding: 24,
            }}
          >
            <h1 style={{ fontSize: 20, marginBottom: 8 }}>Something went wrong</h1>
            <p style={{ color: "#cbd5e1", marginBottom: 12 }}>{this.state.error.message}</p>
            <pre
              style={{
                whiteSpace: "pre-wrap",
                fontSize: 12,
                color: "#94a3b8",
                maxHeight: 240,
                overflow: "auto",
              }}
            >
              {this.state.error.stack}
            </pre>
            <button
              onClick={() => window.location.reload()}
              style={{
                marginTop: 16,
                padding: "8px 16px",
                borderRadius: 8,
                border: "none",
                background: "#2563eb",
                color: "#fff",
                cursor: "pointer",
              }}
            >
              Reload
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Initialise Electron API URL before rendering
initApiUrl();

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      retry: 1,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 0,
    },
  },
});

// Use HashRouter for Electron (file:// protocol) and BrowserRouter for web/PWA
const isElectron = !!(window as Window & { income?: unknown }).income || 
                   navigator.userAgent.toLowerCase().includes("electron");

const Router = isElectron ? HashRouter : BrowserRouter;

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <Router>
        <AppErrorBoundary>
          <App />
        </AppErrorBoundary>
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              borderRadius: "8px",
              background: "#1e293b",
              color: "#f8fafc",
              fontSize: "14px",
            },
            success: {
              iconTheme: { primary: "#059669", secondary: "#fff" },
            },
            error: {
              iconTheme: { primary: "#dc2626", secondary: "#fff" },
            },
          }}
        />
      </Router>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  </React.StrictMode>
);
