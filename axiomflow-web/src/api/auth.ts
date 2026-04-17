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

export async function updateAvatar(params: { avatar_url: string }) {
  const { data } = await api.post<{ ok: boolean; message?: string }>("/auth/avatar", params);
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

export type ProfileStatsResponse = {
  metrics: {
    translated_documents: number;
    translated_words: number;
    credits_balance: number;
    month_delta_pct: number;
    hours_saved: number;
  };
  activity_chart: Array<{ date: string; count: number }>;
  recent_activities: Array<{
    title: string;
    time: string;
    status: string;
    ip: string;
    activity_key?: string;
    document_count?: number;
    word_count?: number;
  }>;
  login_history: Array<{ device: string; ip: string; time: string; status: string }>;
};

export async function getProfileStats() {
  const { data } = await api.get<ProfileStatsResponse>("/auth/profile/stats");
  return data;
}

export type DocumentItem = {
  id: string;
  file_name: string;
  created_at: string;
  file_size_bytes: number;
  document_count: number;
  word_count: number;
  status: string;
};

export async function getMyDocuments() {
  const { data } = await api.get<DocumentItem[]>("/auth/documents");
  return data;
}

export type NotificationPreferencesResponse = {
  notify_email: boolean;
  notify_browser: boolean;
  notify_marketing: boolean;
  updated_at: string;
};

export async function getNotificationPreferences() {
  const { data } = await api.get<NotificationPreferencesResponse>("/auth/notification-preferences");
  return data;
}

export async function updateNotificationPreferences(params: {
  notify_email: boolean;
  notify_browser: boolean;
  notify_marketing: boolean;
}) {
  const { data } = await api.put<NotificationPreferencesResponse>("/auth/notification-preferences", params);
  return data;
}

export async function notifyTranslationCompleted(params: {
  title: string;
  document_count: number;
  word_count: number;
}) {
  const { data } = await api.post<{ ok: boolean; message?: string }>("/auth/notify/translation-completed", params);
  return data;
}

export async function exportMyData() {
  const { data } = await api.get("/auth/export-data");
  return data;
}

export async function deleteMyAccount(params: { current_password: string; confirm_text: string }) {
  const { data } = await api.delete<{ ok: boolean; message?: string }>("/auth/account", { data: params });
  return data;
}

export type UserPreferencesResponse = {
  preferred_target_language: string;
  ui_language: string;
  auto_save_history: boolean;
  enable_shortcuts: boolean;
  updated_at: string;
};

export async function getUserPreferences() {
  const { data } = await api.get<UserPreferencesResponse>("/auth/preferences");
  return data;
}

export async function updateUserPreferences(params: {
  preferred_target_language: string;
  ui_language: string;
  auto_save_history: boolean;
  enable_shortcuts: boolean;
}) {
  const { data } = await api.put<UserPreferencesResponse>("/auth/preferences", params);
  return data;
}

export type UploadOutputPreferencesResponse = {
  upload_size_limit_mb: number;
  auto_import_provider: string;
  default_output_format: string;
  updated_at: string;
};

export async function getUploadOutputPreferences() {
  const { data } = await api.get<UploadOutputPreferencesResponse>("/auth/upload-output-preferences");
  return data;
}

export async function updateUploadOutputPreferences(params: {
  upload_size_limit_mb: number;
  auto_import_provider: string;
  default_output_format: string;
}) {
  const { data } = await api.put<UploadOutputPreferencesResponse>("/auth/upload-output-preferences", params);
  return data;
}

export type PrivacySettingsResponse = {
  data_retention_days: number;
  updated_at: string;
};

export async function getPrivacySettings() {
  const { data } = await api.get<PrivacySettingsResponse>("/auth/privacy-settings");
  return data;
}

export async function updatePrivacySettings(params: { data_retention_days: number }) {
  const { data } = await api.put<PrivacySettingsResponse>("/auth/privacy-settings", params);
  return data;
}

export type ApiKeyItem = {
  id: string;
  masked_key: string;
  created_at: string;
  last_used_at?: string | null;
  revoked_at?: string | null;
};

export type ApiKeyCreateResponse = {
  id: string;
  raw_key: string;
  masked_key: string;
  created_at: string;
};

export async function listApiKeys() {
  const { data } = await api.get<ApiKeyItem[]>("/auth/api-keys");
  return data;
}

export async function createApiKey() {
  const { data } = await api.post<ApiKeyCreateResponse>("/auth/api-keys", {});
  return data;
}

export async function revokeApiKey(apiKeyId: string) {
  const { data } = await api.delete<{ ok: boolean; message?: string }>(`/auth/api-keys/${encodeURIComponent(apiKeyId)}`);
  return data;
}
