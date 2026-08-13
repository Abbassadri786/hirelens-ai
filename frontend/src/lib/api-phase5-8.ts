export type ScreeningQueueStats = Record<string, number>;

export type AuditEvent = {
  id: string;
  event_type: string;
  entity_type: string;
  entity_id: string | null;
  actor_user_id: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function csrf() {
  if (typeof document === "undefined") return null;
  const row = document.cookie.split("; ").find(v => v.startsWith("hirelens_csrf="));
  return row ? decodeURIComponent(row.split("=")[1]) : null;
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}) {
  const headers = new Headers(options.headers);
  const method = (options.method ?? "GET").toUpperCase();
  if (!(options.body instanceof FormData)) headers.set("Content-Type", "application/json");
  if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
    const token = csrf();
    if (token) headers.set("X-CSRF-Token", token);
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
    credentials: "include",
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(
      response.status,
      body.detail ?? response.statusText ?? "Request failed"
    );
  }

  return response.status === 204 ? undefined as T : response.json() as Promise<T>;
}

export const operationsApi = {
  queue: () => request<ScreeningQueueStats>("/api/v1/operations/screening-queue"),
};

export const auditApi = {
  list: (limit = 50) => request<AuditEvent[]>(`/api/v1/audit?limit=${limit}`),
};

export const bulkScreeningApi = {
  enqueueJob: (jobId: string) =>
    request<{ queued: number; job_ids: string[] }>(
      `/api/v1/screening/jobs/${jobId}/enqueue`,
      { method: "POST" }
    ),
  enqueueApplication: (applicationId: string) =>
    request<{ id: string; status: string }>(
      `/api/v1/screening/applications/${applicationId}/enqueue`,
      { method: "POST" }
    ),
};
