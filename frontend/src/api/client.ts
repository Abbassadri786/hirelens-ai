const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  readonly status: number;
  readonly details: unknown;

  constructor(status: number, message: string, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

function readCookie(name: string) {
  if (typeof document === "undefined") return null;
  const row = document.cookie.split("; ").find((value) => value.startsWith(`${name}=`));
  return row ? decodeURIComponent(row.slice(name.length + 1)) : null;
}

async function parseError(response: Response) {
  const body = await response.json().catch(() => ({}));
  let message = response.statusText || "Request failed";
  if (typeof body?.detail === "string") message = body.detail;
  else if (Array.isArray(body?.detail)) message = body.detail.map((item: { msg?: string }) => item.msg ?? "Invalid request").join(" · ");
  return new ApiError(response.status, message, body?.detail);
}

export async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  const method = (options.method ?? "GET").toUpperCase();
  const isFormData = options.body instanceof FormData;

  if (!isFormData && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");

  if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) {
    const csrf = readCookie("hirelens_csrf");
    if (csrf) headers.set("X-CSRF-Token", csrf);
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
    credentials: "include",
  });

  if (!response.ok) throw await parseError(response);
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export function apiBaseUrl() {
  return API_URL;
}
