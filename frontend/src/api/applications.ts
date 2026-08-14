import { apiRequest } from "./client";
import type { Application } from "@/types/domain";

export const applicationsApi = {
  list: () => apiRequest<Application[]>("/api/v1/applications"),
  updateStatus: (id: string, status: string) => apiRequest<Application>(`/api/v1/applications/${id}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  }),
  publicApply: (jobId: string, data: FormData) => apiRequest<{ id: string; message?: string }>(`/api/v1/applications/public/jobs/${jobId}`, {
    method: "POST",
    body: data,
  }),
};
