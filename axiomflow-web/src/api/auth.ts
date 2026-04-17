import { api } from "./client";
import { API_BASE_URL } from "./baseUrl";

export type TokenResponse = {
  access_token: string;
  access_expires_at: string;
  token_type: "Bearer";
};

export type SlideCaptchaIssue = {
  captcha_id: string;
  image_base64: string;
  piece_image_base64: string;
  scene_width: number;
  scene_height: number;
};

export type MathCaptchaIssue = {
  captcha_id: string;
  left: number;
  right: number;
};

export async function issueSlideCaptcha(sceneWidth: number, sceneHeight: number) {
  const { data } = await api.post<SlideCaptchaIssue>(
    `/auth/captcha/slide-issue?scene_width=${encodeURIComponent(String(sceneWidth))}&scene_height=${encodeURIComponent(String(sceneHeight))}`,
    {},
  );
  return data;
}

export function oauthStartUrl(provider: "google" | "github"): string {
  return `${API_BASE_URL}/auth/oauth/${provider}/start`;
}

export async function issueMathCaptcha() {
  const { data } = await api.post<MathCaptchaIssue>("/auth/captcha/math-issue", {});
  return data;
}

export async function register(params: {
  email: string;
  username: string;
  password: string;
  captcha_id: string;
  piece_final_x: number;
}) {
  const { data } = await api.post<{ ok: boolean; message?: string }>("/auth/register", params);
  return data;
}

export async function login(params: {
  email: string;
  password: string;
  captcha_id: string;
  piece_final_x: number;
}) {
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

export async function requestPasswordReset(params: {
  email: string;
  captcha_id: string;
  captcha_answer: number;
}) {
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

export async function changePassword(params: { current_password: string; new_password: string }) {
  const { data } = await api.post<{ ok: boolean }>("/auth/change-password", params);
  return data;
}

export async function getMe() {
  const { data } = await api.get<{
    id: string;
    email: string;
    username?: string | null;
    avatar_url?: string | null;
    is_email_verified: boolean;
  }>("/auth/me");
  return data;
}
