import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";
import { API_BASE_URL } from "./baseUrl";

export const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  timeout: 15000,
});

const AUTH_SKIP_BEARER_PATHS = [
  "/auth/login",
  "/auth/register",
  "/auth/captcha/slide-issue",
  "/auth/captcha/math-issue",
  "/auth/verify-email",
  "/auth/resend-verification",
  "/auth/request-password-reset",
  "/auth/reset-password",
];

function shouldSkipBearer(url: string): boolean {
  return AUTH_SKIP_BEARER_PATHS.some((p) => url.includes(p));
}

type RetryConfig = InternalAxiosRequestConfig & { _authRetry?: boolean };

api.interceptors.request.use((config) => {
  const rel = config.url || "";
  if (!shouldSkipBearer(rel)) {
    const t = sessionStorage.getItem("axiomflow:accessToken");
    if (t) {
      config.headers = config.headers || {};
      config.headers.Authorization = `Bearer ${t}`;
    }
  } else if (config.headers?.Authorization) {
    delete config.headers.Authorization;
  }
  return config;
});

api.interceptors.response.use(
  (r) => r,
  async (error: AxiosError) => {
    const status = error.response?.status;
    const config = error.config as RetryConfig | undefined;
    if (!config || status !== 401) return Promise.reject(error);

    const url = config.url || "";
    if (
      url.includes("/auth/login") ||
      url.includes("/auth/register") ||
      url.includes("/auth/refresh") ||
      url.includes("/auth/change-password")
    ) {
      return Promise.reject(error);
    }

    if (config._authRetry) return Promise.reject(error);
    config._authRetry = true;

    try {
      const { data } = await axios.post<{ access_token: string; access_expires_at?: string }>(
        `${API_BASE_URL}/auth/refresh`,
        {},
        { withCredentials: true, timeout: 15000 }
      );
      sessionStorage.setItem("axiomflow:accessToken", data.access_token);
      if (data.access_expires_at) {
        sessionStorage.setItem("axiomflow:accessExpiresAt", data.access_expires_at);
      }
      config.headers = config.headers || {};
      config.headers.Authorization = `Bearer ${data.access_token}`;
      return api(config);
    } catch {
      return Promise.reject(error);
    }
  }
);
