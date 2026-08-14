"use client";
import { BarChartRounded, BusinessCenterRounded, PersonSearchRounded, SpeedRounded } from "@mui/icons-material";
import { Grid, Stack } from "@mui/material";
import { useAnalytics } from "@/hooks/useAnalytics";
import { PageHeader } from "@/components/common/PageHeader";
import { PageSkeleton } from "@/components/common/LoadingState";
import { ErrorState } from "@/components/common/StateBlock";
import { StatCard } from "@/components/common/StatCard";
import { DistributionCard } from "@/components/analytics/DistributionCard";

export default function AnalyticsPage() {
  const { data, loading, error, refetch } = useAnalytics();
  return <Stack spacing={3}><PageHeader eyebrow="Recruiting intelligence" title="Analytics" description="Understand the shape of your candidate pool and where screening signals are concentrated." />{loading ? <PageSkeleton rows={5} /> : error ? <ErrorState message={error instanceof Error ? error.message : "Unable to load analytics"} onRetry={() => void refetch()} /> : data ? <><Grid container spacing={2}><Grid size={{ xs: 12, sm: 6, lg: 3 }}><StatCard label="Jobs" value={data.total_jobs} icon={<BusinessCenterRounded fontSize="small" />} /></Grid><Grid size={{ xs: 12, sm: 6, lg: 3 }}><StatCard label="Applications" value={data.total_applications} icon={<PersonSearchRounded fontSize="small" />} /></Grid><Grid size={{ xs: 12, sm: 6, lg: 3 }}><StatCard label="Screened" value={data.screened_applications} icon={<SpeedRounded fontSize="small" />} /></Grid><Grid size={{ xs: 12, sm: 6, lg: 3 }}><StatCard label="Average score" value={data.average_score.toFixed(1)} icon={<BarChartRounded fontSize="small" />} /></Grid></Grid><Grid container spacing={2}><Grid size={{ xs: 12, lg: 7 }}><DistributionCard strong={data.recommendations.strong_match} review={data.recommendations.review} low={data.recommendations.low_match} /></Grid><Grid size={{ xs: 12, lg: 5 }}><StatCard label="Screening coverage" value={`${Math.round(data.screened_applications / Math.max(data.total_applications,1) * 100)}%`} hint="Applications with a screening result" icon={<SpeedRounded fontSize="small" />} /></Grid></Grid></> : null}</Stack>;
}
