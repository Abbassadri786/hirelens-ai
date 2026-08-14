import { apiRequest } from "./client";
import type { AuditEvent } from "@/types/domain";

export const auditApi = {
  list: (limit = 50) => apiRequest<AuditEvent[]>(`/api/v1/audit?limit=${limit}`),
};
