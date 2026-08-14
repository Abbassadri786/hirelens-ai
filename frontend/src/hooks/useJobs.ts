"use client";
import { useAsync } from "./useAsync";
import { jobsApi } from "@/api/jobs";

export function useJobs() {
  return useAsync(() => jobsApi.list(), []);
}

export function usePublicJobs() {
  return useAsync(() => jobsApi.publicList(), []);
}
