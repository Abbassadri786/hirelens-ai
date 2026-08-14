import { apiRequest } from "./client";
import type { ScreeningQueueStats } from "@/types/domain";

export const operationsApi = {
  queue: () => apiRequest<ScreeningQueueStats>("/api/v1/operations/screening-queue"),
};
