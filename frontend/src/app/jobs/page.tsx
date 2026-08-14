"use client";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { ArrowForwardRounded, SearchRounded } from "@mui/icons-material";
import { Box, Button, Chip, Container, InputAdornment, Stack, TextField, Typography } from "@mui/material";
import { jobsApi } from "@/api/jobs";
import type { Job } from "@/types/domain";
import { JobCard } from "@/components/jobs/JobCard";
import { PageSkeleton } from "@/components/common/LoadingState";
import { EmptyState, ErrorState } from "@/components/common/StateBlock";

export default function PublicJobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]); const [query, setQuery] = useState(""); const [loading, setLoading] = useState(true); const [error, setError] = useState("");
  useEffect(() => { jobsApi.publicList().then(setJobs).catch(e => setError(e instanceof Error ? e.message : "Unable to load open roles")).finally(() => setLoading(false)); }, []);
  const filtered = useMemo(() => { const q = query.trim().toLowerCase(); if (!q) return jobs; return jobs.filter(j => [j.title, j.location ?? "", j.description, ...j.required_skills].join(" ").toLowerCase().includes(q)); }, [jobs, query]);
  return <Container maxWidth="xl" sx={{ py: { xs: 5, md: 8 } }}>
    <Stack direction={{ xs: "column", md: "row" }} justifyContent="space-between" alignItems={{ xs: "flex-start", md: "flex-end" }} gap={3} sx={{ mb: 4 }}><Box><Typography variant="overline" color="primary.light" fontWeight={850} letterSpacing=".12em">Open roles</Typography><Typography variant="h1" sx={{ fontSize: { xs: "2.7rem", md: "4.2rem" } }}>Find a role worth applying for.</Typography><Typography color="text.secondary" sx={{ mt: 1, maxWidth: 680 }}>Explore live opportunities and apply with a resume. HireLens handles the structured intake so hiring teams can review candidates consistently.</Typography></Box><Button component={Link} href="/jobs/analytics" variant="outlined" endIcon={<ArrowForwardRounded />}>Market snapshot</Button></Stack>
    <TextField placeholder="Search roles, skills or locations…" value={query} onChange={e => setQuery(e.target.value)} InputProps={{ startAdornment: <InputAdornment position="start"><SearchRounded /></InputAdornment> }} sx={{ maxWidth: 640, mb: 4 }} />
    {loading ? <PageSkeleton rows={5} /> : error ? <ErrorState message={error} onRetry={() => window.location.reload()} /> : filtered.length === 0 ? <EmptyState title="No matching roles" description="Try a different skill, role title or location." /> : <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "repeat(2, 1fr)", xl: "repeat(3, 1fr)" }, gap: 2 }}>{filtered.map(job => <JobCard key={job.id} job={job} />)}</Box>}
  </Container>;
}
