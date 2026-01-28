export const API_BASE = "http://localhost:8000/v1";

// 获取认证token
function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("auth_token") || sessionStorage.getItem("auth_token");
}

function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("refresh_token") || sessionStorage.getItem("refresh_token");
}

let isRefreshing = false;
let refreshPromise: Promise<string | null> | null = null;

async function refreshTokenIfNeeded(): Promise<string | null> {
  if (isRefreshing && refreshPromise) {
    return refreshPromise;
  }
  
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    return null;
  }
  
  isRefreshing = true;
  refreshPromise = (async () => {
    try {
      const result = await refreshAccessToken({ refresh_token: refreshToken });
      
      // 更新存储的token
      const storage = localStorage.getItem("auth_token") ? localStorage : sessionStorage;
      storage.setItem("auth_token", result.token);
      storage.setItem("refresh_token", result.refresh_token);
      
      // 更新user store
      const { useUserStore } = await import("../stores/user");
      const userStore = useUserStore();
      userStore.updateTokens(result.token, result.refresh_token);
      
      return result.token;
    } catch (error) {
      // 刷新失败，清除token并跳转到登录页
      const { useUserStore } = await import("../stores/user");
      const userStore = useUserStore();
      userStore.logout();
      
      // 延迟跳转，避免在请求中间跳转
      if (typeof window !== "undefined") {
        setTimeout(() => {
          window.location.href = "/auth";
        }, 100);
      }
      
      return null;
    } finally {
      isRefreshing = false;
      refreshPromise = null;
    }
  })();
  
  return refreshPromise;
}

// 创建带认证的fetch请求
async function authenticatedFetch(url: string, options: RequestInit = {}): Promise<Response> {
  let token = getAuthToken();
  const headers = new Headers(options.headers);
  
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  
  let response = await fetch(url, {
    ...options,
    headers,
  });
  
  // 如果收到401错误，尝试刷新token
  if (response.status === 401 && token) {
    const newToken = await refreshTokenIfNeeded();
    if (newToken) {
      // 使用新token重试请求
      headers.set("Authorization", `Bearer ${newToken}`);
      response = await fetch(url, {
        ...options,
        headers,
      });
    }
  }

  // 统一处理 403（如邮箱未验证导致敏感操作被禁止）
  if (response.status === 403) {
    const text = await response.text();
    try {
      const errorData = JSON.parse(text);
      throw new Error(errorData.detail || text);
    } catch {
      throw new Error(text || "无权限执行该操作");
    }
  }
  
  return response;
}

export type StructuredDoc = {
  document: {
    id: string;
    project_id: string;
    title: string;
    num_pages: number;
    lang_in: string;
    lang_out: string;
    status: string;
    created_at: string;
    updated_at: string;
  };
  pages: Array<{
    index: number;
    width: number;
    height: number;
    regions?: Array<{ type: string; x0: number; y0: number; x1: number; y1: number; score?: number }>;
    blocks: Array<{
      id: string;
      type: string;
      reading_order: number;
      text: string;
      translation: string | null;
      bbox: { page: number; x0: number; y0: number; x1: number; y1: number };
      column_index?: number;
      edited?: boolean;
      edited_at?: string | null;
    }>;
  }>;
};

export async function createProject(name: string): Promise<{ project_id: string }> {
  const body = new FormData();
  body.set("name", name);
  const res = await authenticatedFetch(`${API_BASE}/projects`, { method: "POST", body });
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}

export async function getProjectDocuments(project_id: string): Promise<{
  project_id: string;
  documents: Array<{
    document_id: string;
    title: string;
    num_pages: number;
    lang_in: string;
    lang_out: string;
    status: string;
    created_at: string;
    updated_at: string;
  }>;
}> {
  const res = await authenticatedFetch(`${API_BASE}/projects/${project_id}/documents`);
  if (!res.ok) {
    const text = await res.text();
    if (res.status === 404) {
      throw new Error(`项目 ${project_id} 不存在`);
    }
    throw new Error(text || `获取文档列表失败 (${res.status})`);
  }
  return await res.json();
}

export async function getUserDocuments(): Promise<{
  documents: Array<{
    document_id: string;
    project_id: string;
    title: string;
    num_pages: number;
    lang_in: string;
    lang_out: string;
    status: string;
    created_at: string;
    updated_at: string;
  }>;
}> {
  const res = await authenticatedFetch(`${API_BASE}/projects/documents`);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `获取用户文档列表失败 (${res.status})`);
  }
  return await res.json();
}

export async function uploadPdf(params: {
  project_id: string;
  file: File;
  lang_in?: string;
  lang_out?: string;
}): Promise<{ project_id: string; document_id: string; parse_job_id?: string; title: string; num_pages: number }> {
  const body = new FormData();
  body.set("file", params.file);
  body.set("lang_in", params.lang_in ?? "en");
  body.set("lang_out", params.lang_out ?? "zh");
  const res = await authenticatedFetch(`${API_BASE}/projects/${params.project_id}/files`, {
    method: "POST",
    body,
  });
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}

export async function getDocument(document_id: string): Promise<StructuredDoc> {
  const res = await fetch(`${API_BASE}/documents/${document_id}`);
  if (!res.ok) {
    const text = await res.text();
    if (res.status === 404) {
      throw new Error(`文档 ${document_id} 不存在`);
    }
    throw new Error(text || `获取文档失败 (${res.status})`);
  }
  return await res.json();
}

export async function deleteDocument(document_id: string): Promise<{ ok: boolean; message?: string }> {
  const res = await authenticatedFetch(`${API_BASE}/documents/${document_id}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const text = await res.text();
    try {
      const errorData = JSON.parse(text);
      throw new Error(errorData.detail || text);
    } catch {
      throw new Error(text || `删除文档失败 (${res.status})`);
    }
  }
  return await res.json();
}

export async function batchDeleteDocuments(document_ids: string[]): Promise<{
  ok: boolean;
  success_count: number;
  failed_count: number;
  success_ids: string[];
  failed_ids: Array<{ document_id: string; reason: string }>;
}> {
  const res = await authenticatedFetch(`${API_BASE}/documents/batch/delete`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ document_ids }),
  });
  if (!res.ok) {
    const text = await res.text();
    try {
      const errorData = JSON.parse(text);
      throw new Error(errorData.detail || text);
    } catch {
      throw new Error(text || `批量删除文档失败 (${res.status})`);
    }
  }
  return await res.json();
}

export function getSourcePdfUrl(document_id: string): string {
  return `${API_BASE}/documents/${document_id}/source`;
}

export async function getDocumentProgress(document_id: string): Promise<{
  document_id: string;
  status: string;
  num_pages: number;
  parse_progress: number;
  parse_job?: {
    id: string;
    stage: string;
    progress: number;
    done?: number;
    total?: number;
    eta_s?: number;
    message?: string;
  };
  translate_job?: any;
}> {
  const res = await fetch(`${API_BASE}/documents/${document_id}/progress`);
  if (!res.ok) {
    const text = await res.text();
    if (res.status === 404) {
      throw new Error(`文档 ${document_id} 不存在`);
    }
    throw new Error(text || `获取文档进度失败 (${res.status})`);
  }
  return await res.json();
}

export async function translateDocument(params: {
  document_id: string;
  lang_in: string;
  lang_out: string;
  provider?: string;
  use_context?: boolean;
  context_window_size?: number;
  use_term_consistency?: boolean;
  use_smart_batching?: boolean;
}): Promise<{ job_id: string }> {
  const res = await fetch(`${API_BASE}/jobs/translate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      document_id: params.document_id,
      lang_in: params.lang_in,
      lang_out: params.lang_out,
      provider: params.provider ?? "ollama",
      use_context: params.use_context,
      context_window_size: params.context_window_size,
      use_term_consistency: params.use_term_consistency,
      use_smart_batching: params.use_smart_batching,
    }),
  });
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}

export async function getJob(job_id: string): Promise<any> {
  const res = await fetch(`${API_BASE}/jobs/${job_id}`);
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}

export async function pauseJob(job_id: string): Promise<any> {
  const res = await fetch(`${API_BASE}/jobs/${job_id}/pause`, { method: "POST" });
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}

export async function resumeJob(job_id: string): Promise<any> {
  const res = await fetch(`${API_BASE}/jobs/${job_id}/resume`, { method: "POST" });
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}

export async function cancelJob(job_id: string): Promise<any> {
  const res = await fetch(`${API_BASE}/jobs/${job_id}/cancel`, { method: "POST" });
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}

export async function retryJob(job_id: string): Promise<{ job_id: string }> {
  const res = await fetch(`${API_BASE}/jobs/${job_id}/retry`, { method: "POST" });
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}

export async function patchBlockTranslation(params: {
  document_id: string;
  block_id: string;
  translation: string;
  apply_all_same_source?: boolean;
}): Promise<{ ok: boolean }> {
  const res = await fetch(`${API_BASE}/documents/${params.document_id}/blocks/${params.block_id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ translation: params.translation, apply_all_same_source: params.apply_all_same_source ?? false }),
  });
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}

export async function exportDocument(params: {
  document_id: string;
  format: "markdown" | "html" | "html-hifi" | "pdf" | "pdf-mono" | "pdf-dual" | "docx";
  bilingual?: boolean;
  subset_fonts?: boolean;
  convert_to_pdfa?: boolean;
  pdfa_part?: 1 | 2 | 3;
  pdfa_conformance?: "A" | "B" | "U";
}): Promise<any> {
  const res = await fetch(`${API_BASE}/export`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}

export async function suggestTerms(params: { document_id: string; top_k?: number }): Promise<{ terms: Array<{ term: string; count: number }> }> {
  const url = new URL(`${API_BASE}/documents/${params.document_id}/terms`);
  if (params.top_k) url.searchParams.set("top_k", String(params.top_k));
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}

export async function getGlossary(params: { project_id: string }): Promise<{ glossary: Record<string, string> }> {
  const res = await fetch(`${API_BASE}/projects/${params.project_id}/glossary`);
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}

export async function upsertGlossary(params: { project_id: string; term: string; translation: string }): Promise<{ ok: boolean }> {
  const res = await fetch(`${API_BASE}/projects/${params.project_id}/glossary`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ term: params.term, translation: params.translation }),
  });
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}

export async function deleteGlossaryTerm(params: { project_id: string; term: string }): Promise<{ ok: boolean }> {
  const url = new URL(`${API_BASE}/projects/${params.project_id}/glossary`);
  url.searchParams.set("term", params.term);
  const res = await fetch(url.toString(), { method: "DELETE" });
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}

export async function extractAssets(params: { document_id: string }): Promise<{ assets: Array<{ kind: string; download_url: string }> }> {
  const res = await fetch(`${API_BASE}/documents/${params.document_id}/assets/extract`, { method: "POST" });
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}

export async function batchUpload(params: {
  project_name: string;
  files: File[];
  lang_in?: string;
  lang_out?: string;
  provider?: string;
}): Promise<{ batch_id: string; project_id: string; documents: Array<{ document_id: string; title: string; num_pages: number }> }> {
  const body = new FormData();
  body.set("project_name", params.project_name);
  body.set("lang_in", params.lang_in ?? "en");
  body.set("lang_out", params.lang_out ?? "zh");
  body.set("auto_translate", "true");
  body.set("provider", params.provider ?? "ollama");
  for (const f of params.files) body.append("files", f);
  const res = await authenticatedFetch(`${API_BASE}/batches/upload`, { method: "POST", body });
  if (!res.ok) {
    const text = await res.text();
    try {
      const errorData = JSON.parse(text);
      throw new Error(errorData.detail || text);
    } catch {
      throw new Error(text || `批量上传失败 (${res.status})`);
    }
  }
  return await res.json();
}

export async function getBatch(params: { batch_id: string }): Promise<any> {
  const res = await fetch(`${API_BASE}/batches/${params.batch_id}`);
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}

export interface AuthResponse {
  token?: string;
  refresh_token?: string;
  user?: { id: string; email: string; name: string; avatar?: string; provider: string; has_password?: boolean; email_verified?: boolean };
  last_login?: { time?: string; ip?: string; user_agent?: string } | null;
  requires_2fa?: boolean;
  challenge_token?: string;
  two_fa_methods?: string[];
}

export async function googleLogin(token: string): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE}/auth/google`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Google登录失败 (${res.status})`);
  }
  return await res.json();
}

export async function getCaptcha(): Promise<{ session_id: string; image: string | null; code?: string }> {
  const res = await fetch(`${API_BASE}/auth/captcha`);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `获取验证码失败 (${res.status})`);
  }
  return await res.json();
}

export async function emailRegister(params: {
  name: string;
  email: string;
  password: string;
  captcha_code?: string;
  captcha_session?: string;
}): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const text = await res.text();
    try {
      const errorData = JSON.parse(text);
      throw new Error(errorData.detail || text);
    } catch {
      throw new Error(text || `注册失败 (${res.status})`);
    }
  }
  return await res.json();
}

export async function emailLogin(params: {
  email: string;
  password: string;
  captcha_code?: string;
  captcha_session?: string;
}): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const text = await res.text();
    try {
      const errorData = JSON.parse(text);
      throw new Error(errorData.detail || text);
    } catch {
      throw new Error(text || `登录失败 (${res.status})`);
    }
  }
  return await res.json();
}

export async function verify2FALogin(params: {
  challenge_token: string;
  code: string;
}): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE}/auth/2fa/verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const text = await res.text();
    try {
      const errorData = JSON.parse(text);
      throw new Error(errorData.detail || text);
    } catch {
      throw new Error(text || `2FA 验证失败 (${res.status})`);
    }
  }
  return await res.json();
}

export async function forgotPassword(params: { email: string }): Promise<{ message: string; session_id: string; code?: string }> {
  const res = await fetch(`${API_BASE}/auth/forgot-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const text = await res.text();
    try {
      const errorData = JSON.parse(text);
      throw new Error(errorData.detail || text);
    } catch {
      throw new Error(text || `请求失败 (${res.status})`);
    }
  }
  return await res.json();
}

export async function verifyEmailCode(params: { email: string; code: string; session_id: string }): Promise<{ message: string; token: string }> {
  const res = await fetch(`${API_BASE}/auth/verify-email-code`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const text = await res.text();
    try {
      const errorData = JSON.parse(text);
      throw new Error(errorData.detail || text);
    } catch {
      throw new Error(text || `验证失败 (${res.status})`);
    }
  }
  return await res.json();
}

export async function resetPassword(params: { token: string; new_password: string }): Promise<{ message: string }> {
  const res = await fetch(`${API_BASE}/auth/reset-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const text = await res.text();
    try {
      const errorData = JSON.parse(text);
      throw new Error(errorData.detail || text);
    } catch {
      throw new Error(text || `重置失败 (${res.status})`);
    }
  }
  return await res.json();
}

export async function sendEmailVerification(params: { email: string }): Promise<{ message: string; verification_url?: string }> {
  const res = await fetch(`${API_BASE}/auth/send-email-verification`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const text = await res.text();
    try {
      const errorData = JSON.parse(text);
      throw new Error(errorData.detail || text);
    } catch {
      throw new Error(text || `发送失败 (${res.status})`);
    }
  }
  return await res.json();
}

export async function verifyEmail(params: { token: string }): Promise<{ message: string }> {
  const res = await fetch(`${API_BASE}/auth/verify-email`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const text = await res.text();
    try {
      const errorData = JSON.parse(text);
      throw new Error(errorData.detail || text);
    } catch {
      throw new Error(text || `验证失败 (${res.status})`);
    }
  }
  return await res.json();
}

export async function refreshAccessToken(params: { refresh_token: string }): Promise<{
  token: string;
  refresh_token: string;
  user: { id: string; email: string; name: string; provider: string; email_verified?: boolean };
}> {
  const res = await fetch(`${API_BASE}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const text = await res.text();
    try {
      const errorData = JSON.parse(text);
      throw new Error(errorData.detail || text);
    } catch {
      throw new Error(text || `刷新失败 (${res.status})`);
    }
  }
  return await res.json();
}

// 用户账户管理API
export async function changePassword(params: { current_password: string; new_password: string }): Promise<{ message: string }> {
  const res = await authenticatedFetch(`${API_BASE}/users/change-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const text = await res.text();
    try {
      const errorData = JSON.parse(text);
      throw new Error(errorData.detail || text);
    } catch {
      throw new Error(text || `修改失败 (${res.status})`);
    }
  }
  return await res.json();
}

export interface LoginHistoryItem {
  id: string;
  ip: string;
  user_agent: string;
  success: boolean;
  reason: string;
  created_at: string;
  login_method: string;  // 登录方式：email, google, github
  device_type: string;   // 设备类型：Desktop, Mobile, Tablet
  browser: string;       // 浏览器
  os: string;            // 操作系统
}

export async function getLoginHistory(limit: number = 20): Promise<LoginHistoryItem[]> {
  const res = await authenticatedFetch(`${API_BASE}/users/login-history?limit=${limit}`);
  if (!res.ok) {
    const text = await res.text();
    try {
      const errorData = JSON.parse(text);
      throw new Error(errorData.detail || text);
    } catch {
      throw new Error(text || `获取失败 (${res.status})`);
    }
  }
  return await res.json();
}

export interface SessionInfo {
  session_id: string;
  token: string;
  ip: string;
  user_agent: string;
  created_at: string;
  last_used_at: string | null;
  is_current: boolean;
}

export async function getSessions(): Promise<SessionInfo[]> {
  const res = await authenticatedFetch(`${API_BASE}/users/sessions`);
  if (!res.ok) {
    const text = await res.text();
    try {
      const errorData = JSON.parse(text);
      throw new Error(errorData.detail || text);
    } catch {
      throw new Error(text || `获取失败 (${res.status})`);
    }
  }
  return await res.json();
}

export async function revokeSession(sessionIdOrTokenPrefix: string): Promise<{ message: string }> {
  const res = await authenticatedFetch(`${API_BASE}/users/sessions/${encodeURIComponent(sessionIdOrTokenPrefix)}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const text = await res.text();
    try {
      const errorData = JSON.parse(text);
      throw new Error(errorData.detail || text);
    } catch {
      throw new Error(text || `撤销失败 (${res.status})`);
    }
  }
  return await res.json();
}

export async function revokeAllSessions(): Promise<{ message: string }> {
  const res = await authenticatedFetch(`${API_BASE}/users/sessions/revoke-all`, {
    method: "POST",
  });
  if (!res.ok) {
    const text = await res.text();
    try {
      const errorData = JSON.parse(text);
      throw new Error(errorData.detail || text);
    } catch {
      throw new Error(text || `撤销失败 (${res.status})`);
    }
  }
  return await res.json();
}

export async function updateProfile(params: { name: string }): Promise<{ message: string; name: string }> {
  const res = await authenticatedFetch(`${API_BASE}/users/me`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const text = await res.text();
    try {
      const errorData = JSON.parse(text);
      throw new Error(errorData.detail || text);
    } catch {
      throw new Error(text || `更新失败 (${res.status})`);
    }
  }
  return await res.json();
}

export async function uploadAvatar(file: File): Promise<{ message: string; avatar: string }> {
  const body = new FormData();
  body.set("file", file);
  const res = await authenticatedFetch(`${API_BASE}/users/avatar`, {
    method: "POST",
    body,
  });
  if (!res.ok) {
    const text = await res.text();
    try {
      const errorData = JSON.parse(text);
      throw new Error(errorData.detail || text);
    } catch {
      throw new Error(text || `上传头像失败 (${res.status})`);
    }
  }
  return await res.json();
}

export async function sendLoginUnlockCode(params: { email: string }): Promise<{ message: string; session_id: string; code?: string }> {
  const res = await fetch(`${API_BASE}/auth/login-unlock/send`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const text = await res.text();
    try {
      const errorData = JSON.parse(text);
      throw new Error(errorData.detail || text);
    } catch {
      throw new Error(text || `请求失败 (${res.status})`);
    }
  }
  return await res.json();
}

export async function verifyLoginUnlockCode(params: {
  email: string;
  code: string;
  session_id: string;
}): Promise<{ message: string }> {
  const res = await fetch(`${API_BASE}/auth/login-unlock/verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const text = await res.text();
    try {
      const errorData = JSON.parse(text);
      throw new Error(errorData.detail || text);
    } catch {
      throw new Error(text || `验证失败 (${res.status})`);
    }
  }
  return await res.json();
}

// 2FA / 社交账号绑定 / 密码泄露检测相关前端 API 已移除



