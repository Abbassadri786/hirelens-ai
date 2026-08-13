export type UserRole =
  | "ORGANIZATION_ADMIN"
  | "RECRUITER"
  | "HIRING_MANAGER"
  | "CANDIDATE";

export type User = {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function readCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const value = document.cookie
    .split("; ")
    .find((row) => row.startsWith(`${name}=`))
    ?.split("=")[1];
  return value ? decodeURIComponent(value) : null;
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const method = (options.method ?? "GET").toUpperCase();
  const headers = new Headers(options.headers);

  headers.set("Content-Type", "application/json");

  if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
    const csrf = readCookie("hirelens_csrf");
    if (csrf) headers.set("X-CSRF-Token", csrf);
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
    credentials: "include",
  });

  if (!response.ok) {
    const body = await response
      .json()
      .catch(() => ({}));

    throw new ApiError(
      response.status,
      body.detail ??
        response.statusText ??
        "Request failed"
    );
  }

  return response.json() as Promise<T>;
}

export class ApiError extends Error {
  status: number;

  constructor(
    status: number,
    message: string
  ) {
    super(message);

    this.name = "ApiError";
    this.status = status;
  }
}

export const api = {
  register: (payload: {
    fullName: string;
    email: string;
    organization: string;
    password: string;
  }) =>
    request<User>("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify({
        full_name: payload.fullName,
        email: payload.email,
        organization_name: payload.organization,
        password: payload.password,
      }),
    }),

  login: (email: string, password: string) =>
    request<User>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  me: () => request<User>("/api/v1/auth/me"),

  organization: () =>
    request<{ id: string; name: string; slug: string }>(
      "/api/v1/organizations/me",
    ),

  logout: () =>
    request<{ message: string }>("/api/v1/auth/logout", {
      method: "POST",
    }),
};

export type Job = {
  id: string;
  title: string;
  description: string;
  location: string | null;
  employment_type: string | null;
  min_experience_years: number | null;
  status: "DRAFT" | "PUBLISHED" | "CLOSED" | "ARCHIVED";
  is_public: boolean;
  created_at: string;
  required_skills: string[];
  preferred_skills: string[];
};

export type Application = {
  id: string;
  job_id: string;
  candidate_id: string;
  resume_id: string;
  status: string;
  submitted_at: string;

  candidate: {
    id: string;
    full_name: string;
    email: string;
    phone: string | null;
    location: string | null;
    summary: string | null;
    created_at: string;
  };

  resume: {
    id: string;
    original_filename: string;
    file_type: string;
    mime_type: string;
    file_size: number;
    status: string;
    created_at: string;
  };
};

export const jobsApi = {
  list: () => request<Job[]>("/api/v1/jobs"),

  publicList: () => request<Job[]>("/api/v1/jobs/public"),

  getPublic: (id: string) =>
    request<Job>(`/api/v1/jobs/public/${id}`),

  create: (payload: {
    title: string;
    description: string;
    location?: string;
    employment_type?: string;
    min_experience_years?: number;
    required_skills: string[];
    preferred_skills: string[];
  }) =>
    request<Job>("/api/v1/jobs", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  update: (id: string, payload: Record<string, unknown>) =>
    request<Job>(`/api/v1/jobs/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
};

export const applicationsApi = {
  list: () =>
    request<Application[]>("/api/v1/applications"),

  updateStatus: (id: string, status: string) =>
    request<Application>(
      `/api/v1/applications/${id}/status`,
      {
        method: "PATCH",
        body: JSON.stringify({ status }),
      }
    ),
};
