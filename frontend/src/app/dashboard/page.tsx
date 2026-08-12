"use client";
import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { AddRounded, ArrowBackRounded } from "@mui/icons-material";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Container,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { Job, jobsApi } from "@/lib/api";
export default function Jobs() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [open, setOpen] = useState(false);
  const [error, setError] = useState("");
  const [f, setF] = useState({
    title: "",
    description: "",
    location: "",
    employment_type: "Full-time",
    min: "",
    required: "",
    preferred: "",
  });
  const load = async () => {
    try {
      setJobs(await jobsApi.list());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to load jobs");
    }
  };
  useEffect(() => {
    void load();
  }, []);
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await jobsApi.create({
        title: f.title,
        description: f.description,
        location: f.location || undefined,
        employment_type: f.employment_type || undefined,
        min_experience_years: f.min ? Number(f.min) : undefined,
        required_skills: f.required
          .split(",")
          .map((x) => x.trim())
          .filter(Boolean),
        preferred_skills: f.preferred
          .split(",")
          .map((x) => x.trim())
          .filter(Boolean),
      });
      setOpen(false);
      setF({
        title: "",
        description: "",
        location: "",
        employment_type: "Full-time",
        min: "",
        required: "",
        preferred: "",
      });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to create job");
    }
  };
  const publish = async (j: Job) => {
    try {
      await jobsApi.update(j.id, { status: "PUBLISHED" });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to publish");
    }
  };
  return (
    <Container maxWidth="xl" sx={{ py: 5 }}>
      <Stack
        direction="row"
        justifyContent="space-between"
        alignItems="center"
        sx={{ mb: 5 }}
      >
        <Box>
          <Button
            component={Link}
            href="/dashboard"
            startIcon={<ArrowBackRounded />}
          >
            Dashboard
          </Button>
          <Typography variant="h2" fontWeight={850}>
            Jobs
          </Typography>
          <Typography color="text.secondary">
            Create and publish recruitment requirements.
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddRounded />}
          onClick={() => setOpen(true)}
        >
          Create job
        </Button>
      </Stack>
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}
      <Stack spacing={2}>
        {jobs.map((j) => (
          <Card key={j.id} sx={{ borderRadius: 4 }}>
            <CardContent sx={{ p: 3 }}>
              <Stack
                direction={{ xs: "column", md: "row" }}
                justifyContent="space-between"
              >
                <Box>
                  <Stack direction="row" gap={1} alignItems="center">
                    <Typography variant="h5" fontWeight={800}>
                      {j.title}
                    </Typography>
                    <Chip
                      size="small"
                      label={j.status}
                      color={j.status === "PUBLISHED" ? "success" : "default"}
                    />
                  </Stack>
                  <Typography color="text.secondary">
                    {j.location || "Flexible"} ·{" "}
                    {j.employment_type || "Not specified"}
                    {j.min_experience_years !== null
                      ? ` · ${j.min_experience_years}+ years`
                      : ""}
                  </Typography>
                </Box>
                {j.status === "DRAFT" && (
                  <Button onClick={() => publish(j)} variant="contained">
                    Publish
                  </Button>
                )}
              </Stack>
              <Stack direction="row" gap={1} flexWrap="wrap" sx={{ mt: 2 }}>
                {j.required_skills.map((s) => (
                  <Chip key={s} label={s} color="primary" variant="outlined" />
                ))}
                {j.preferred_skills.map((s) => (
                  <Chip
                    key={`p-${s}`}
                    label={`${s} · preferred`}
                    variant="outlined"
                  />
                ))}
              </Stack>
            </CardContent>
          </Card>
        ))}
      </Stack>
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        fullWidth
        maxWidth="md"
      >
        <Box component="form" onSubmit={submit}>
          <DialogTitle>Create recruitment role</DialogTitle>
          <DialogContent>
            <Stack spacing={2} sx={{ pt: 1 }}>
              <TextField
                label="Job title"
                required
                value={f.title}
                onChange={(e) => setF({ ...f, title: e.target.value })}
              />
              <TextField
                label="Job description"
                required
                multiline
                minRows={7}
                value={f.description}
                onChange={(e) => setF({ ...f, description: e.target.value })}
              />
              <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
                <TextField
                  label="Location"
                  value={f.location}
                  onChange={(e) => setF({ ...f, location: e.target.value })}
                />
                <TextField
                  label="Employment type"
                  value={f.employment_type}
                  onChange={(e) =>
                    setF({ ...f, employment_type: e.target.value })
                  }
                />
                <TextField
                  label="Min experience"
                  type="number"
                  value={f.min}
                  onChange={(e) => setF({ ...f, min: e.target.value })}
                />
              </Stack>
              <TextField
                label="Required skills"
                helperText="Comma-separated"
                value={f.required}
                onChange={(e) => setF({ ...f, required: e.target.value })}
              />
              <TextField
                label="Preferred skills"
                helperText="Comma-separated"
                value={f.preferred}
                onChange={(e) => setF({ ...f, preferred: e.target.value })}
              />
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpen(false)}>Cancel</Button>
            <Button type="submit" variant="contained">
              Create
            </Button>
          </DialogActions>
        </Box>
      </Dialog>
    </Container>
  );
}
