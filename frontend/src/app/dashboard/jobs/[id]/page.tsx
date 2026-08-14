"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { ArrowBackRounded, PublishRounded, QueueRounded } from "@mui/icons-material";
import { Alert, Box, Button, Card, CardContent, Chip, Divider, Stack, Typography } from "@mui/material";
import { jobsApi } from "@/api/jobs";
import { screeningApi } from "@/api/screening";
import type { Job } from "@/types/domain";
import { PageSkeleton } from "@/components/common/LoadingState";
import { StatusChip } from "@/components/common/StatusChip";

export default function ManageJobDetailPage() {
  const params = useParams<{ id: string }>(); const [job, setJob] = useState<Job | null>(null); const [loading, setLoading] = useState(true); const [error, setError] = useState(""); const [message, setMessage] = useState(""); const [busy, setBusy] = useState(false);
  useEffect(() => { jobsApi.get(params.id).then(setJob).catch(e => setError(e instanceof Error ? e.message : "Unable to load role")).finally(() => setLoading(false)); }, [params.id]);
  async function publish() { if (!job) return; setBusy(true); setMessage(""); try { setJob(await jobsApi.update(job.id, { status: "PUBLISHED" })); setMessage("Role published successfully."); } catch(e) { setError(e instanceof Error ? e.message : "Unable to publish role"); } finally { setBusy(false); } }
  async function enqueue() { if (!job) return; setBusy(true); setMessage(""); try { const result = await screeningApi.enqueueJob(job.id); setMessage(`${result.queued} applications added to the screening queue.`); } catch(e) { setError(e instanceof Error ? e.message : "Unable to queue screening"); } finally { setBusy(false); } }
  if (loading) return <PageSkeleton rows={5} />; if (!job) return <Alert severity="error">{error || "Role not found"}</Alert>;
  return <Stack spacing={3}><Button component={Link} href="/dashboard/jobs" startIcon={<ArrowBackRounded />} sx={{ alignSelf: "flex-start" }}>Back to jobs</Button><Card sx={{ borderRadius: 4 }}><CardContent sx={{ p: { xs: 3, md: 4 } }}><Stack direction={{ xs: "column", md: "row" }} justifyContent="space-between" gap={3}><Box><Stack direction="row" spacing={1} alignItems="center"><Typography variant="h3">{job.title}</Typography><StatusChip status={job.status} /></Stack><Typography color="text.secondary" sx={{ mt: .8 }}>{job.location || "Flexible"} · {job.employment_type || "Full-time"} · {job.min_experience_years ?? "Any"}{job.min_experience_years != null ? "+ years" : " experience"}</Typography></Box><Stack direction={{ xs: "column", sm: "row" }} spacing={1}><Button variant="outlined" startIcon={<QueueRounded />} onClick={enqueue} disabled={busy}>Queue screening</Button>{job.status === "DRAFT" && <Button variant="contained" startIcon={<PublishRounded />} onClick={publish} disabled={busy}>Publish role</Button>}</Stack></Stack>{message && <Alert severity="success" sx={{ mt: 3 }}>{message}</Alert>}{error && <Alert severity="error" sx={{ mt: 3 }}>{error}</Alert>}<Divider sx={{ my: 4 }} /><Typography variant="h6" fontWeight={850}>Job description</Typography><Typography color="text.secondary" sx={{ mt: 1.5, whiteSpace: "pre-wrap", lineHeight: 1.9 }}>{job.description}</Typography><Typography variant="h6" fontWeight={850} sx={{ mt: 4 }}>Required skills</Typography><Stack direction="row" gap={1} flexWrap="wrap" sx={{ mt: 1.5 }}>{job.required_skills.map(s => <Chip key={s} label={s} color="primary" variant="outlined" />)}</Stack>{job.preferred_skills.length > 0 && <><Typography variant="h6" fontWeight={850} sx={{ mt: 4 }}>Preferred skills</Typography><Stack direction="row" gap={1} flexWrap="wrap" sx={{ mt: 1.5 }}>{job.preferred_skills.map(s => <Chip key={s} label={s} variant="outlined" />)}</Stack></>}</CardContent></Card></Stack>;
}
