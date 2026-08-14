import { apiRequest } from "./client";
import type { AnalyticsOverview } from "@/types/domain";

export const analyticsApi = {
  overview: () => apiRequest<AnalyticsOverview>("/api/v1/analytics/overview"),
};
