export const API_BASE = "http://localhost:8000/v1";

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
  const res = await fetch(`${API_BASE}/projects`, { method: "POST", body });
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
  const res = await fetch(`${API_BASE}/projects/${project_id}/documents`);
  if (!res.ok) {
    const text = await res.text();
    if (res.status === 404) {
      throw new Error(`项目 ${project_id} 不存在`);
    }
    throw new Error(text || `获取文档列表失败 (${res.status})`);
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
  const res = await fetch(`${API_BASE}/projects/${params.project_id}/files`, {
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
  const res = await fetch(`${API_BASE}/batches/upload`, { method: "POST", body });
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}

export async function getBatch(params: { batch_id: string }): Promise<any> {
  const res = await fetch(`${API_BASE}/batches/${params.batch_id}`);
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}

export async function googleLogin(token: string): Promise<{ token: string; user: { id: string; email: string; name: string; avatar?: string; provider: string } }> {
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
}): Promise<{ token: string; user: { id: string; email: string; name: string; provider: string } }> {
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
}): Promise<{ token: string; user: { id: string; email: string; name: string; provider: string } }> {
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

export async function forgotPassword(params: { email: string }): Promise<{ message: string; reset_url?: string; token?: string }> {
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


