"use client";
import { FormEvent, useState } from "react";
import { Button, Dialog, DialogActions, DialogContent, DialogTitle, Stack, TextField } from "@mui/material";
import { jobsApi } from "@/api/jobs";
import type { Job } from "@/types/domain";

const initial = { title: "", description: "", location: "", employment_type: "Full-time", min: "", required: "", preferred: "" };

export function JobFormDialog({ open, onClose, onCreated }: { open: boolean; onClose: () => void; onCreated: (job: Job) => void }) {
  const [form, setForm] = useState(initial);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const update = (key: keyof typeof form, value: string) => setForm((current) => ({ ...current, [key]: value }));

  async function submit(event: FormEvent) {
    event.preventDefault(); setSaving(true); setError("");
    try {
      const job = await jobsApi.create({ title: form.title, description: form.description, location: form.location || undefined, employment_type: form.employment_type || undefined, min_experience_years: form.min ? Number(form.min) : undefined, required_skills: form.required.split(",").map((x) => x.trim()).filter(Boolean), preferred_skills: form.preferred.split(",").map((x) => x.trim()).filter(Boolean) });
      onCreated(job); setForm(initial); onClose();
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to create job"); }
    finally { setSaving(false); }
  }

  return <Dialog open={open} onClose={saving ? undefined : onClose} fullWidth maxWidth="md">
    <DialogTitle sx={{ fontWeight: 850 }}>Create a recruitment role</DialogTitle>
    <DialogContent dividers><Stack component="form" id="create-job-form" onSubmit={submit} spacing={2} sx={{ pt: 1 }}>
      {error && <TextField error value={error} helperText="Please fix the request and try again." InputProps={{ readOnly: true }} />}
      <TextField label="Job title" placeholder="Senior Backend Engineer" required value={form.title} onChange={(e) => update("title", e.target.value)} />
      <TextField label="Job description" placeholder="What will this person own?" required multiline minRows={8} value={form.description} onChange={(e) => update("description", e.target.value)} />
      <Stack direction={{ xs: "column", sm: "row" }} spacing={2}><TextField label="Location" placeholder="Remote / Indore" value={form.location} onChange={(e) => update("location", e.target.value)} /><TextField label="Employment type" value={form.employment_type} onChange={(e) => update("employment_type", e.target.value)} /><TextField label="Minimum experience" type="number" inputProps={{ min: 0, max: 50 }} value={form.min} onChange={(e) => update("min", e.target.value)} /></Stack>
      <TextField label="Required skills" placeholder="Python, FastAPI, PostgreSQL" helperText="Comma-separated. These drive deterministic qualification checks." value={form.required} onChange={(e) => update("required", e.target.value)} />
      <TextField label="Preferred skills" placeholder="AWS, Docker, React" helperText="Comma-separated. Preferred skills contribute to the matching signal." value={form.preferred} onChange={(e) => update("preferred", e.target.value)} />
    </Stack></DialogContent>
    <DialogActions sx={{ p: 2 }}><Button onClick={onClose} disabled={saving}>Cancel</Button><Button form="create-job-form" type="submit" variant="contained" disabled={saving}>{saving ? "Creating…" : "Create role"}</Button></DialogActions>
  </Dialog>;
}
