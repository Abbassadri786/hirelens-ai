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
    let message = "Request failed";
    try {
      const body = await response.json();
      message = body.detail ?? message;
    } catch {
      // Keep generic message for non-JSON errors.
    }
    throw new Error(message);
  }

  return response.json() as Promise<T>;
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
