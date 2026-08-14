"use client";
import { useEffect, useState } from "react";
import { AddRounded, SearchRounded } from "@mui/icons-material";
import { Alert, Box, Button, InputAdornment, Stack, TextField } from "@mui/material";
import { jobsApi } from "@/api/jobs";
import type { Job } from "@/types/domain";
import { JobCard } from "@/components/jobs/JobCard";
import { JobFormDialog } from "@/components/jobs/JobFormDialog";
import { PageHeader } from "@/components/common/PageHeader";
import { PageSkeleton } from "@/components/common/LoadingState";
import { EmptyState, ErrorState } from "@/components/common/StateBlock";

export default function ManageJobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]); const [open, setOpen] = useState(false); const [query, setQuery] = useState(""); const [loading, setLoading] = useState(true); const [error, setError] = useState("");
  const load = () => { setLoading(true); jobsApi.list().then(setJobs).catch(e => setError(e instanceof Error ? e.message : "Unable to load jobs")).finally(() => setLoading(false)); };
  useEffect(() => { load(); }, []);
  const filtered = jobs.filter(j => `${j.title} ${j.location ?? ""} ${j.status}`.toLowerCase().includes(query.toLowerCase()));
  async function publish(job: Job) { try { const updated = await jobsApi.update(job.id, { status: "PUBLISHED" }); setJobs(current => current.map(j => j.id === updated.id ? updated : j)); } catch(e) { setError(e instanceof Error ? e.message : "Unable to publish role"); } }
  return <><PageHeader eyebrow="Hiring operations" title="Jobs" description="Create roles, publish requirements and keep your recruiting pipeline organized." action={<Button variant="contained" startIcon={<AddRounded />} onClick={() => setOpen(true)}>Create job</Button>} />
    <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5} sx={{ mb: 3 }}><TextField size="small" placeholder="Search roles…" value={query} onChange={e => setQuery(e.target.value)} InputProps={{ startAdornment: <InputAdornment position="start"><SearchRounded fontSize="small" /></InputAdornment> }} sx={{ maxWidth: 420 }} /></Stack>
    {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
    {loading ? <PageSkeleton rows={6} /> : filtered.length === 0 ? <EmptyState title={jobs.length ? "No roles match" : "Your workspace has no roles yet"} description={jobs.length ? "Try another search term." : "Create your first recruitment role to start accepting and screening applications."} action={<Button variant="contained" startIcon={<AddRounded />} onClick={() => setOpen(true)}>Create first role</Button>} /> : <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "repeat(2, 1fr)", xl: "repeat(3, 1fr)" }, gap: 2 }}>{filtered.map(job => <JobCard key={job.id} job={job} manage onPublish={publish} />)}</Box>}
    <JobFormDialog open={open} onClose={() => setOpen(false)} onCreated={job => setJobs(current => [job, ...current])} />
  </>;
}
