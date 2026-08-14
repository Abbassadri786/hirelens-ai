"use client";
import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowBackRounded, CheckCircleRounded, CloudUploadRounded, LocationOnOutlined, ScheduleRounded } from "@mui/icons-material";
import { Alert, Box, Button, Card, CardContent, Chip, Divider, Stack, TextField, Typography } from "@mui/material";
import { authApi } from "@/api/auth";
import { applicationsApi } from "@/api/applications";
import { jobsApi } from "@/api/jobs";
import { PageSkeleton } from "@/components/common/LoadingState";
import { ErrorState } from "@/components/common/StateBlock";
import type { Job } from "@/types/domain";

export default function PublicJobDetailPage() {
  const params = useParams<{ id: string }>(); const [job, setJob] = useState<Job | null>(null); const [loading, setLoading] = useState(true); const [error, setError] = useState(""); const [success, setSuccess] = useState(false); const [submitting, setSubmitting] = useState(false); const [file, setFile] = useState<File | null>(null);
  const [form, setForm] = useState({ full_name: "", email: "", phone: "", location: "", cover_letter: "" });
  useEffect(() => { jobsApi.getPublic(params.id).then(setJob).catch(e => setError(e instanceof Error ? e.message : "Role not found")).finally(() => setLoading(false)); }, [params.id]);
  async function submit(event: FormEvent) { event.preventDefault(); setError(""); if (!file) { setError("Attach a PDF or DOCX resume before submitting."); return; } if (file.size > 10 * 1024 * 1024) { setError("Resume must be 10 MB or smaller."); return; } setSubmitting(true); try { await authApi.csrf(); const data = new FormData(); data.append("full_name", form.full_name);
    data.append("email", form.email);
    data.append("phone", form.phone);
    data.append("location", form.location);
    data.append("cover_letter", form.cover_letter); data.append("resume_file", file); await applicationsApi.publicApply(params.id, data); setSuccess(true); } catch (e) { setError(e instanceof Error ? e.message : "Application failed"); } finally { setSubmitting(false); } }
  if (loading) return <Box sx={{ maxWidth: 1100, mx: "auto", py: 7, px: 2 }}><PageSkeleton rows={6} /></Box>;
  if (error && !job) return <Box sx={{ maxWidth: 1100, mx: "auto", py: 7, px: 2 }}><ErrorState message={error} /></Box>;
  if (!job) return null;
  if (success) return <Box sx={{ maxWidth: 720, mx: "auto", py: 10, px: 2 }}><Card sx={{ borderRadius: 5, textAlign: "center" }}><CardContent sx={{ p: { xs: 4, md: 6 } }}><CheckCircleRounded color="success" sx={{ fontSize: 64 }} /><Typography variant="h3" sx={{ mt: 2 }}>Application received.</Typography><Typography color="text.secondary" sx={{ mt: 1.5, lineHeight: 1.7 }}>Your resume has been securely submitted for <strong>{job.title}</strong>. The hiring team can now review your application through their screening workflow.</Typography><Button component={Link} href="/jobs" variant="contained" sx={{ mt: 3 }}>Browse more roles</Button></CardContent></Card></Box>;
  return <Box sx={{ maxWidth: 1200, mx: "auto", py: { xs: 4, md: 7 }, px: { xs: 2, md: 3 } }}>
    <Button component={Link} href="/jobs" startIcon={<ArrowBackRounded />} color="inherit" sx={{ mb: 3 }}>All open roles</Button>
    <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", lg: "1.25fr .75fr" }, gap: 3 }}>
      <Card sx={{ borderRadius: 4 }}><CardContent sx={{ p: { xs: 3, md: 4 } }}><Chip label="OPEN ROLE" color="primary" variant="outlined" size="small" /><Typography variant="h1" sx={{ fontSize: { xs: "2.5rem", md: "4rem" }, mt: 1.5 }}>{job.title}</Typography><Stack direction="row" flexWrap="wrap" gap={2} sx={{ mt: 1.5 }}><Typography color="text.secondary" sx={{ display: "flex", alignItems: "center", gap: .5 }}><LocationOnOutlined fontSize="small" />{job.location || "Flexible"}</Typography><Typography color="text.secondary" sx={{ display: "flex", alignItems: "center", gap: .5 }}><ScheduleRounded fontSize="small" />{job.employment_type || "Full-time"}</Typography></Stack><Divider sx={{ my: 4 }} /><Typography variant="h6" fontWeight={850}>About the role</Typography><Typography color="text.secondary" sx={{ mt: 1.5, whiteSpace: "pre-wrap", lineHeight: 1.9 }}>{job.description}</Typography><Typography variant="h6" fontWeight={850} sx={{ mt: 4 }}>Required skills</Typography><Stack direction="row" gap={1} flexWrap="wrap" sx={{ mt: 1.5 }}>{job.required_skills.map(s => <Chip key={s} label={s} variant="outlined" />)}</Stack>{job.preferred_skills.length > 0 && <><Typography variant="h6" fontWeight={850} sx={{ mt: 4 }}>Nice to have</Typography><Stack direction="row" gap={1} flexWrap="wrap" sx={{ mt: 1.5 }}>{job.preferred_skills.map(s => <Chip key={s} label={s} color="secondary" variant="outlined" />)}</Stack></>}</CardContent></Card>
      <Card component="form" onSubmit={submit} sx={{ borderRadius: 4, alignSelf: "start", position: { lg: "sticky" }, top: { lg: 92 } }}><CardContent sx={{ p: 3 }}><Typography variant="h5" fontWeight={850}>Apply for this role</Typography><Typography color="text.secondary" variant="body2" sx={{ mt: .5 }}>Your resume is used for structured screening and recruiter review.</Typography><Stack spacing={2} sx={{ mt: 3 }}>{error && <Alert severity="error">{error}</Alert>}<TextField label="Full name" required value={form.full_name} onChange={e => setForm({...form,full_name:e.target.value})} /><TextField label="Email" required type="email" value={form.email} onChange={e => setForm({...form,email:e.target.value})} /><Stack direction={{ xs:"column", sm:"row" }} spacing={2}><TextField label="Phone" value={form.phone} onChange={e => setForm({...form,phone:e.target.value})} /><TextField label="Location" value={form.location} onChange={e => setForm({...form,location:e.target.value})} /></Stack><TextField label="Cover letter" multiline minRows={4} value={form.cover_letter} onChange={e => setForm({...form,cover_letter:e.target.value})} /><Button component="label" variant="outlined" startIcon={<CloudUploadRounded />} sx={{ justifyContent:"flex-start", py:1.25 }}>{file ? file.name : "Upload PDF or DOCX"}<input hidden type="file" accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" onChange={e => setFile(e.target.files?.[0] ?? null)} /></Button><Typography variant="caption" color="text.secondary">Maximum 10 MB. Avoid sensitive information unrelated to your application.</Typography><Button type="submit" variant="contained" size="large" disabled={submitting}>{submitting ? "Submitting securely…" : "Submit application"}</Button></Stack></CardContent></Card>
    </Box>
  </Box>;
}
