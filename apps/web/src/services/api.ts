/**
 * INCOME – Centralized API service using axios.
 * In Electron: reads API URL from the main process via IPC.
 * In browser/PWA: reads from VITE_API_BASE_URL environment variable.
 */

import axios, {
  AxiosError,
  AxiosInstance,
  AxiosRequestConfig,
  InternalAxiosRequestConfig,
} from "axios";
import { useAuthStore } from "@/store/authStore";

// ---------------------------------------------------------------------------
// Determine base URL — Electron IPC or Vite env
// ---------------------------------------------------------------------------
const DEFAULT_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

function getBaseUrl(): string {
  if (typeof window !== "undefined") {
    return localStorage.getItem("income_api_url") ?? DEFAULT_BASE;
  }
  return DEFAULT_BASE;
}

function normalizeApiUrl(url: string): string {
  const trimmed = url.trim().replace(/\/+$/, "");
  if (!/^https?:\/\//i.test(trimmed)) {
    throw new Error("Server URL must start with http:// or https://");
  }
  if (/\/api\/v1$/i.test(trimmed)) return trimmed;
  if (/\/api$/i.test(trimmed)) return `${trimmed}/v1`;
  return `${trimmed}/api/v1`;
}

// Initialise API URL from Electron IPC on startup (async, fire-and-forget)
export async function initApiUrl() {
  const w = window as Window & { income?: { isElectron?: boolean; getApiUrl?: () => Promise<string> } };
  if (w.income?.isElectron && w.income?.getApiUrl) {
    try {
      const url = await w.income.getApiUrl();
      if (url) {
        localStorage.setItem("income_api_url", url);
        apiClient.defaults.baseURL = url;
      }
    } catch {
      // Fall back to default
    }
  }
}

export const apiClient: AxiosInstance = axios.create({
  baseURL: getBaseUrl(),
  headers: { "Content-Type": "application/json" },
  timeout: 30_000,
});

export function getApiBaseUrl(): string {
  return apiClient.defaults.baseURL ?? DEFAULT_BASE;
}

export async function setApiBaseUrl(url: string): Promise<string> {
  const normalized = normalizeApiUrl(url);
  localStorage.setItem("income_api_url", normalized);
  apiClient.defaults.baseURL = normalized;

  const w = window as Window & {
    income?: { isElectron?: boolean; setApiUrl?: (url: string) => Promise<{ success: boolean; error?: string }> };
  };
  if (w.income?.isElectron && w.income.setApiUrl) {
    try {
      await w.income.setApiUrl(normalized);
    } catch {
      // Renderer value is already updated; Electron persistence is best-effort.
    }
  }

  return normalized;
}

// ---- Request interceptor: attach JWT ----
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = useAuthStore.getState().access;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ---- Response interceptor: auto-refresh token ----
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (err: unknown) => void;
}> = [];

function processQueue(error: unknown, token: string | null) {
  failedQueue.forEach((prom) => {
    if (error) prom.reject(error);
    else prom.resolve(token!);
  });
  failedQueue = [];
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          if (originalRequest.headers) {
            (originalRequest.headers as Record<string, string>)[
              "Authorization"
            ] = `Bearer ${token}`;
          }
          return apiClient(originalRequest);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = useAuthStore.getState().refresh;
      if (!refreshToken) {
        useAuthStore.getState().logout();
        isRefreshing = false;
        return Promise.reject(error);
      }

      try {
        const res = await axios.post(`${apiClient.defaults.baseURL}/auth/token/refresh/`, {
          refresh: refreshToken,
        });
        const newAccess = res.data.access;
        useAuthStore.getState().setTokens(newAccess, refreshToken);
        processQueue(null, newAccess);
        if (originalRequest.headers) {
          (originalRequest.headers as Record<string, string>)[
            "Authorization"
          ] = `Bearer ${newAccess}`;
        }
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        useAuthStore.getState().logout();
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

// ---- Typed helper functions ----
export const api = {
  get: <T>(url: string, config?: AxiosRequestConfig) =>
    apiClient.get<T>(url, config).then((r) => r.data),

  post: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    apiClient.post<T>(url, data, config).then((r) => r.data),

  patch: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    apiClient.patch<T>(url, data, config).then((r) => r.data),

  put: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    apiClient.put<T>(url, data, config).then((r) => r.data),

  delete: <T>(url: string, config?: AxiosRequestConfig) =>
    apiClient.delete<T>(url, config).then((r) => r.data),

  upload: <T>(url: string, formData: FormData, config?: AxiosRequestConfig) =>
    apiClient
      .post<T>(url, formData, {
        ...config,
        headers: { "Content-Type": "multipart/form-data" },
      })
      .then((r) => r.data),
};

export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data;
    if (data?.error) return data.error;
    if (data?.detail) return data.detail;
    if (typeof data === "string") return data;
    if (error.code === "ERR_NETWORK")
      return "Cannot reach the server. Make sure the backend is running.";
  }
  if (error instanceof Error) return error.message;
  return "An unexpected error occurred.";
}
