"use client";
import { useEffect, useState } from "react";
import { BarChartRounded, BusinessCenterRounded, LocationOnRounded, TrendingUpRounded } from "@mui/icons-material";
import { Box, Card, CardContent, Container, Grid, Stack, Typography } from "@mui/material";
import { jobsApi } from "@/api/jobs";
import { PageSkeleton } from "@/components/common/LoadingState";
import { ErrorState } from "@/components/common/StateBlock";
import { StatCard } from "@/components/common/StatCard";

type Data = { total_jobs: number; total_open_roles: number; locations: number; top_skills: { skill: string; count: number }[] };

export default function PublicJobsAnalytics() {
  const [data, setData] = useState<Data | null>(null); const [loading, setLoading] = useState(true); const [error, setError] = useState("");
  useEffect(() => { jobsApi.publicAnalytics().then(setData).catch(e => setError(e instanceof Error ? e.message : "Unable to load job analytics")).finally(() => setLoading(false)); }, []);
  return <Container maxWidth="xl" sx={{ py: { xs: 5, md: 8 } }}><Box sx={{ mb: 4 }}><Typography variant="overline" color="primary.light" fontWeight={850}>Public market snapshot</Typography><Typography variant="h1" sx={{ fontSize: { xs: "2.7rem", md: "4.2rem" } }}>What teams are hiring for.</Typography><Typography color="text.secondary" sx={{ mt: 1, maxWidth: 700 }}>A lightweight view of the live roles published through HireLens. This page is intentionally public and does not require recruiter authentication.</Typography></Box>
    {loading ? <PageSkeleton rows={4} /> : error ? <ErrorState message={error} /> : data ? <Stack spacing={3}><Grid container spacing={2}><Grid size={{ xs: 12, sm: 6, md: 3 }}><StatCard label="Published roles" value={data.total_jobs} icon={<BusinessCenterRounded fontSize="small" />} /></Grid><Grid size={{ xs: 12, sm: 6, md: 3 }}><StatCard label="Open roles" value={data.total_open_roles} icon={<TrendingUpRounded fontSize="small" />} /></Grid><Grid size={{ xs: 12, sm: 6, md: 3 }}><StatCard label="Locations" value={data.locations} icon={<LocationOnRounded fontSize="small" />} /></Grid><Grid size={{ xs: 12, sm: 6, md: 3 }}><StatCard label="Top skill signals" value={data.top_skills.length} icon={<BarChartRounded fontSize="small" />} /></Grid></Grid><Card sx={{ borderRadius: 4 }}><CardContent sx={{ p: 3 }}><Typography variant="h6" fontWeight={850}>Most requested skills</Typography><Typography color="text.secondary" variant="body2">Skills appearing most often across current public roles.</Typography><Stack spacing={1.25} sx={{ mt: 3 }}>{data.top_skills.map((item, i) => <Stack key={item.skill} direction="row" spacing={2} alignItems="center"><Typography sx={{ width: 28 }} color="text.secondary">{String(i + 1).padStart(2, "0")}</Typography><Typography fontWeight={750} sx={{ flex: 1 }}>{item.skill}</Typography><Typography fontWeight={850}>{item.count}</Typography><Box sx={{ width: { xs: 80, sm: 220 }, height: 7, borderRadius: 4, bgcolor: "rgba(255,255,255,.07)" }}><Box sx={{ width: `${Math.min(100, item.count / Math.max(data.top_skills[0]?.count || 1, 1) * 100)}%`, height: "100%", borderRadius: 4, bgcolor: "primary.main" }} /></Box></Stack>)}</Stack></CardContent></Card></Stack> : null}
  </Container>;
}
