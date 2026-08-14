"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowForwardRounded, AssessmentRounded, BarChartRounded, BusinessCenterRounded, PersonSearchRounded, TrendingUpRounded } from "@mui/icons-material";
import { Box, Button, Card, CardContent, Chip, Grid, LinearProgress, Stack, Typography } from "@mui/material";
import { analyticsApi } from "@/api/analytics";
import { screeningApi } from "@/api/screening";
import type { AnalyticsOverview, ScreeningListItem } from "@/types/domain";
import { ErrorState } from "@/components/common/StateBlock";
import { PageSkeleton } from "@/components/common/LoadingState";
import { StatCard } from "@/components/common/StatCard";
import { StatusChip } from "@/components/common/StatusChip";
import { ScoreRing } from "@/components/common/ScoreRing";
import { formatDate, scoreTone } from "@/lib/format";

export function OverviewContent() {
  const [analytics, setAnalytics] = useState<AnalyticsOverview | null>(null);
  const [screening, setScreening] = useState<ScreeningListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([analyticsApi.overview(), screeningApi.list()])
      .then(([a, s]) => { setAnalytics(a); setScreening(s.slice(0, 5)); })
      .catch((e) => setError(e instanceof Error ? e.message : "Unable to load dashboard"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <PageSkeleton rows={6} />;
  if (error) return <ErrorState message={error} />;
  if (!analytics) return null;

  const distribution = analytics.recommendations;
  const total = Math.max(analytics.screened_applications, 1);

  return <Stack spacing={3}>
    <Card sx={{ borderRadius: 4, overflow: "hidden", position: "relative", background: "linear-gradient(135deg, rgba(155,140,255,.16), rgba(16,19,26,.96) 54%, rgba(88,214,193,.08))" }}>
      <CardContent sx={{ p: { xs: 3, md: 4 } }}>
        <Stack direction={{ xs: "column", md: "row" }} justifyContent="space-between" gap={3}>
          <Box>
            <Chip icon={<TrendingUpRounded />} label="Recruiting pulse" color="primary" variant="outlined" sx={{ mb: 2 }} />
            <Typography variant="h3" sx={{ maxWidth: 720 }}>Turn a thousand resumes into a reviewable shortlist.</Typography>
            <Typography color="text.secondary" sx={{ mt: 1, maxWidth: 680 }}>HireLens combines deterministic qualification checks, semantic matching and explainable AI so recruiters can focus on evidence—not spreadsheet archaeology.</Typography>
            <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5} sx={{ mt: 3 }}>
              <Button component={Link} href="/dashboard/jobs" variant="contained" endIcon={<ArrowForwardRounded />}>Manage jobs</Button>
              <Button component={Link} href="/dashboard/screening" variant="outlined">Review candidates</Button>
            </Stack>
          </Box>
          <Box sx={{ minWidth: { md: 230 }, alignSelf: "center", textAlign: "center" }}>
            <ScoreRing score={analytics.average_score} size={132} />
            <Typography fontWeight={850} sx={{ mt: 1 }}>Average screening score</Typography>
            <Typography variant="caption" color="text.secondary">Across screened applications</Typography>
          </Box>
        </Stack>
      </CardContent>
    </Card>

    <Grid container spacing={2}>
      <Grid size={{ xs: 12, sm: 6, lg: 3 }}><StatCard label="Open roles" value={analytics.total_jobs} hint="Published + active pipeline" icon={<BusinessCenterRounded fontSize="small" />} /></Grid>
      <Grid size={{ xs: 12, sm: 6, lg: 3 }}><StatCard label="Applications" value={analytics.total_applications} hint="Candidate submissions" icon={<PersonSearchRounded fontSize="small" />} /></Grid>
      <Grid size={{ xs: 12, sm: 6, lg: 3 }}><StatCard label="Screened" value={analytics.screened_applications} hint={`${Math.round((analytics.screened_applications / Math.max(analytics.total_applications, 1)) * 100)}% of applications`} icon={<AssessmentRounded fontSize="small" />} /></Grid>
      <Grid size={{ xs: 12, sm: 6, lg: 3 }}><StatCard label="Avg. score" value={analytics.average_score.toFixed(1)} hint="Out of 100" icon={<BarChartRounded fontSize="small" />} /></Grid>
    </Grid>

    <Grid container spacing={2}>
      <Grid size={{ xs: 12, lg: 7 }}>
        <Card sx={{ height: "100%", borderRadius: 3.5 }}><CardContent sx={{ p: 3 }}>
          <Stack direction="row" justifyContent="space-between" alignItems="center"><Box><Typography variant="h6" fontWeight={850}>Candidate signal</Typography><Typography variant="body2" color="text.secondary">How the screened pool is distributed.</Typography></Box><Button component={Link} href="/dashboard/analytics" endIcon={<ArrowForwardRounded />}>Full analytics</Button></Stack>
          <Stack spacing={2.25} sx={{ mt: 3 }}>
            {[["Strong match", distribution.strong_match, "success"], ["Needs review", distribution.review, "warning"], ["Low match", distribution.low_match, "error"]].map(([label, value, color]) => <Box key={label as string}>
              <Stack direction="row" justifyContent="space-between" sx={{ mb: .75 }}><Typography fontWeight={700}>{label}</Typography><Typography color="text.secondary">{value}</Typography></Stack>
              <LinearProgress color={color as "success" | "warning" | "error"} variant="determinate" value={Number(value) / total * 100} sx={{ height: 8, borderRadius: 4 }} />
            </Box>)}
          </Stack>
        </CardContent></Card>
      </Grid>
      <Grid size={{ xs: 12, lg: 5 }}>
        <Card sx={{ height: "100%", borderRadius: 3.5 }}><CardContent sx={{ p: 3 }}>
          <Stack direction="row" justifyContent="space-between" alignItems="center"><Box><Typography variant="h6" fontWeight={850}>Recent screening</Typography><Typography variant="body2" color="text.secondary">Latest candidate signals.</Typography></Box><Button component={Link} href="/dashboard/screening">View all</Button></Stack>
          <Stack spacing={1} sx={{ mt: 2 }}>
            {screening.length === 0 ? <Typography color="text.secondary" sx={{ py: 4 }}>No screening results yet.</Typography> : screening.map((row) => <Stack key={row.application_id} direction="row" alignItems="center" spacing={1.5} sx={{ py: 1.25, borderBottom: "1px solid rgba(255,255,255,.06)" }}>
              <Box sx={{ flex: 1, minWidth: 0 }}><Typography fontWeight={750} noWrap>{row.candidate_name}</Typography><Typography variant="caption" color="text.secondary" noWrap>{row.job_title} · {formatDate(row.submitted_at)}</Typography></Box>
              {row.overall_score !== null ? <Typography fontWeight={850} color={`${scoreTone(row.overall_score)}.main`}>{row.overall_score.toFixed(0)}</Typography> : <StatusChip status="UNDER_REVIEW" />}
            </Stack>)}
          </Stack>
        </CardContent></Card>
      </Grid>
    </Grid>
  </Stack>;
}
