"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { Alert, Box, Button, Container, Stack, TextField, Typography } from "@mui/material";
import { api } from "@/lib/api";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");

    try {
      await api.login(email, password);
      window.location.href = "/dashboard";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to sign in");
    }
  }

  return (
    <Container maxWidth="sm" sx={{ minHeight: "100vh", display: "grid", placeItems: "center", py: 4 }}>
      <Box component="form" onSubmit={submit} sx={{ width: "100%", p: { xs: 3, md: 5 }, border: "1px solid", borderColor: "divider", borderRadius: 5, background: "background.paper" }}>
        <Typography variant="h3" fontWeight={850} letterSpacing="-.04em">Welcome back</Typography>
        <Typography color="text.secondary" sx={{ mt: 1, mb: 4 }}>Sign in to your HireLens workspace.</Typography>
        <Stack spacing={2.2}>
          {error && <Alert severity="error">{error}</Alert>}
          <TextField label="Work email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
          <TextField label="Password" type="password" required value={password} onChange={(e) => setPassword(e.target.value)} />
          <Button type="submit" variant="contained" size="large" sx={{ py: 1.5, borderRadius: 2.5 }}>Sign in</Button>
          <Typography variant="body2" color="text.secondary">
            New workspace? <Link href="/signup">Create an account</Link>
          </Typography>
        </Stack>
      </Box>
    </Container>
  );
}
