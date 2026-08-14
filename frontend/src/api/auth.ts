import { apiRequest } from "./client";
import type { Organization, User } from "@/types/domain";

export const authApi = {
  register: (payload: { fullName: string; email: string; organization: string; password: string }) =>
    apiRequest<User>("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify({
        full_name: payload.fullName,
        email: payload.email,
        organization_name: payload.organization,
        password: payload.password,
      }),
    }),

  login: (email: string, password: string) =>
    apiRequest<User>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  me: () => apiRequest<User>("/api/v1/auth/me"),

  organization: () => apiRequest<Organization>("/api/v1/organizations/me"),

  csrf: () => apiRequest<{ csrf_token?: string }>("/api/v1/auth/csrf"),

  logout: () => apiRequest<{ message: string }>("/api/v1/auth/logout", { method: "POST" }),
};
