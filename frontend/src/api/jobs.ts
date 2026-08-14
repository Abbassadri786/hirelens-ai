import { apiRequest } from "./client";
import type { Job } from "@/types/domain";

export const jobsApi = {
  list: () => apiRequest<Job[]>("/api/v1/jobs"),
  publicList: () => apiRequest<Job[]>("/api/v1/jobs/public"),
  get: (id: string) => apiRequest<Job>(`/api/v1/jobs/${id}`),
  getPublic: (id: string) => apiRequest<Job>(`/api/v1/jobs/public/${id}`),
  publicAnalytics: () => apiRequest<{ total_jobs: number; total_open_roles: number; locations: number; top_skills: { skill: string; count: number }[] }>("/api/v1/jobs/public/analytics"),
  create: (payload: {
    title: string;
    description: string;
    location?: string;
    employment_type?: string;
    min_experience_years?: number;
    required_skills: string[];
    preferred_skills: string[];
  }) => apiRequest<Job>("/api/v1/jobs", { method: "POST", body: JSON.stringify(payload) }),
  update: (id: string, payload: Record<string, unknown>) => apiRequest<Job>(`/api/v1/jobs/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
};
