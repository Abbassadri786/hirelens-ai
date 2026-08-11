"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { Alert, Box, Button, Container, Stack, TextField, Typography } from "@mui/material";
import { api } from "@/lib/api";

export default function SignupPage() {
  const [form, setForm] = useState({ fullName: "", email: "", organization: "", password: "" });
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");

    try {
      await api.register(form);
      window.location.href = "/dashboard";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create account");
    }
  }

  return (
    <Container maxWidth="sm" sx={{ minHeight: "100vh", display: "grid", placeItems: "center", py: 4 }}>
      <Box component="form" onSubmit={submit} sx={{ width: "100%", p: { xs: 3, md: 5 }, border: "1px solid", borderColor: "divider", borderRadius: 5, background: "background.paper" }}>
        <Typography variant="h3" fontWeight={850} letterSpacing="-.04em">Create workspace</Typography>
        <Typography color="text.secondary" sx={{ mt: 1, mb: 4 }}>Start your recruitment workspace.</Typography>
        <Stack spacing={2.2}>
          {error && <Alert severity="error">{error}</Alert>}
          <TextField label="Full name" required value={form.fullName} onChange={(e) => setForm({ ...form, fullName: e.target.value })} />
          <TextField label="Work email" type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          <TextField label="Organization name" required value={form.organization} onChange={(e) => setForm({ ...form, organization: e.target.value })} />
          <TextField label="Password" type="password" helperText="At least 12 characters" required value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
          <Button type="submit" variant="contained" size="large" sx={{ py: 1.5, borderRadius: 2.5 }}>Create workspace</Button>
          <Typography variant="body2" color="text.secondary">
            Already registered? <Link href="/login">Sign in</Link>
          </Typography>
        </Stack>
      </Box>
    </Container>
  );
}
