import { apiRequest } from "./client";
import type { ScreeningListItem, ScreeningResult } from "@/types/domain";

export const screeningApi = {
  list: () => apiRequest<ScreeningListItem[]>("/api/v1/screening"),
  get: (id: string) => apiRequest<ScreeningResult>(`/api/v1/screening/applications/${id}`),
  run: (id: string) => apiRequest<ScreeningResult>(`/api/v1/screening/applications/${id}/run`, { method: "POST" }),
  enqueueApplication: (id: string) => apiRequest<{ id: string; status: string }>(`/api/v1/screening/applications/${id}/enqueue`, { method: "POST" }),
  enqueueJob: (jobId: string) => apiRequest<{ queued: number; job_ids: string[] }>(`/api/v1/screening/jobs/${jobId}/enqueue`, { method: "POST" }),
};
