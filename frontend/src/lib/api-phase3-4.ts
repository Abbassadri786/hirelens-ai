export type ScreeningResult = {
  id: string;
  application_id: string;
  overall_score: number;
  keyword_score: number;
  semantic_score: number;
  experience_score: number;
  completeness_score: number;
  recommendation: "STRONG_MATCH" | "REVIEW" | "LOW_MATCH";
  provider: string;
  model_name: string;
  matched_skills: string[];
  missing_required_skills: string[];
  matched_preferred_skills: string[];
  strengths: string[];
  concerns: string[];
  improvement_suggestions: string[];
  explanation: string;
  resume_sections: Record<string, string>;
  processing_ms: number | null;
  created_at: string;
};

export type ScreeningListItem = {
  application_id: string;
  candidate_name: string;
  job_title: string;
  submitted_at: string;
  overall_score: number | null;
  recommendation: string | null;
  application_status: string;
};

export type AnalyticsOverview = {
  total_jobs: number;
  total_applications: number;
  screened_applications: number;
  average_score: number;
  recommendations: { strong_match: number; review: number; low_match: number };
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function csrf() {
  if (typeof document === "undefined") return null;
  const row = document.cookie.split("; ").find(v => v.startsWith("hirelens_csrf="));
  return row ? decodeURIComponent(row.split("=")[1]) : null;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  const method = (options.method ?? "GET").toUpperCase();
  if (!(options.body instanceof FormData)) headers.set("Content-Type", "application/json");
  if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
    const token = csrf();
    if (token) headers.set("X-CSRF-Token", token);
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options, headers, credentials: "include",
  });

  if (response.status === 401) throw new Error("AUTH_EXPIRED");
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? "Request failed");
  }
  return response.status === 204 ? undefined as T : response.json();
}

export const screeningApi = {
  list: () => request<ScreeningListItem[]>("/api/v1/screening"),
  get: (id: string) => request<ScreeningResult>(`/api/v1/screening/applications/${id}`),
  run: (id: string) => request<ScreeningResult>(`/api/v1/screening/applications/${id}/run`, { method: "POST" }),
};

export const analyticsApi = {
  overview: () => request<AnalyticsOverview>("/api/v1/analytics/overview"),
};
