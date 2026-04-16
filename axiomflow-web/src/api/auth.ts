import { api } from "./client";

export type TokenResponse = {
  access_token: string;
  access_expires_at: string;
  token_type: "Bearer";
};

export async function register(params: { email: string; username: string; password: string }) {
  const { data } = await api.post<{ ok: boolean; message?: string }>("/auth/register", params);
  return data;
}

export async function login(params: { email: string; password: string }) {
  const { data } = await api.post<TokenResponse>("/auth/login", params);
  return data;
}

export async function refresh() {
  const { data } = await api.post<TokenResponse>("/auth/refresh", {});
  return data;
}

export async function logout() {
  const { data } = await api.post<{ ok: boolean }>("/auth/logout", {});
  return data;
}

export async function verifyEmail(params: { token: string }) {
  const { data } = await api.post<TokenResponse>("/auth/verify-email", params);
  return data;
}

export async function resendVerification(params: { email: string }) {
  const { data } = await api.post<{ ok: boolean; message?: string }>("/auth/resend-verification", params);
  return data;
}

export async function requestPasswordReset(params: { email: string }) {
  const { data } = await api.post<{ ok: boolean; message?: string }>(
    "/auth/request-password-reset",
    params,
  );
  return data;
}

export async function resetPassword(params: { token: string; new_password: string }) {
  const { data } = await api.post<{ ok: boolean }>("/auth/reset-password", params);
  return data;
}

