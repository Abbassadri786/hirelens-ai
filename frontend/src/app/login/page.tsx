"use client";
import { FormEvent, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Alert, Box, Button, Container, Divider, IconButton, InputAdornment, Stack, TextField, Typography } from "@mui/material";
import { ArrowBackRounded, VisibilityRounded, VisibilityOffRounded } from "@mui/icons-material";
import { authApi } from "@/api/auth";
import { PublicHeader } from "@/components/layout/PublicHeader";

export default function LoginPage() {
  const params = useSearchParams();
  const next = params.get("next") || "/dashboard";
  const [email, setEmail] = useState(""); const [password, setPassword] = useState(""); const [show, setShow] = useState(false); const [error, setError] = useState(""); const [loading, setLoading] = useState(false);
  async function submit(event: FormEvent) { event.preventDefault(); setError(""); setLoading(true); try { await authApi.login(email.trim(), password); window.location.href = next.startsWith("/") ? next : "/dashboard"; } catch (e) { setError(e instanceof Error ? e.message : "Unable to sign in"); } finally { setLoading(false); } }
  return <Box sx={{ minHeight: "100vh" }}><PublicHeader /><Container maxWidth="sm" sx={{ py: { xs: 6, md: 10 } }}>
    <Box sx={{ maxWidth: 460, mx: "auto" }}><Button component={Link} href="/" startIcon={<ArrowBackRounded />} color="inherit" sx={{ mb: 4 }}>Back to home</Button>
      <Typography variant="h2" sx={{ fontSize: "2.8rem" }}>Welcome back.</Typography><Typography color="text.secondary" sx={{ mt: 1, mb: 4 }}>Sign in to your recruiting workspace.</Typography>
      <Box component="form" onSubmit={submit} sx={{ p: { xs: 2.5, sm: 3.5 }, borderRadius: 4, border: "1px solid rgba(255,255,255,.08)", bgcolor: "rgba(255,255,255,.025)" }}>
        <Stack spacing={2}>{error && <Alert severity="error">{error}</Alert>}<TextField label="Work email" type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} /><TextField label="Password" type={show ? "text" : "password"} autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} InputProps={{ endAdornment: <InputAdornment position="end"><IconButton onClick={() => setShow(v => !v)} edge="end" aria-label="toggle password visibility">{show ? <VisibilityOffRounded /> : <VisibilityRounded />}</IconButton></InputAdornment> }} /><Button type="submit" variant="contained" size="large" disabled={loading}>{loading ? "Signing in…" : "Sign in"}</Button></Stack>
        <Divider sx={{ my: 2.5 }} /><Typography variant="body2" color="text.secondary">New to HireLens? <Link href="/signup">Create a workspace</Link></Typography>
      </Box>
    </Box>
  </Container></Box>;
}
