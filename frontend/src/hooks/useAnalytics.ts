"use client";
import { useAsync } from "./useAsync";
import { analyticsApi } from "@/api/analytics";

export function useAnalytics() {
  return useAsync(() => analyticsApi.overview(), []);
}
