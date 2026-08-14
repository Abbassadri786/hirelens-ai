"use client";
import { FormEvent, useState } from "react";
import Link from "next/link";
import { Alert, Box, Button, Container, Stack, TextField, Typography } from "@mui/material";
import { ArrowBackRounded, CheckCircleRounded } from "@mui/icons-material";
import { authApi } from "@/api/auth";
import { PublicHeader } from "@/components/layout/PublicHeader";

export default function SignupPage() {
  const [form, setForm] = useState({ fullName: "", email: "", organization: "", password: "" }); const [error, setError] = useState(""); const [loading, setLoading] = useState(false);
  const update = (key: keyof typeof form, value: string) => setForm((current) => ({ ...current, [key]: value }));
  async function submit(event: FormEvent) { event.preventDefault(); setError(""); if (form.password.length < 12) { setError("Use at least 12 characters for your password."); return; } setLoading(true); try { await authApi.register(form); window.location.href = "/dashboard"; } catch (e) { setError(e instanceof Error ? e.message : "Unable to create workspace"); } finally { setLoading(false); } }
  return <Box sx={{ minHeight: "100vh" }}><PublicHeader /><Container maxWidth="md" sx={{ py: { xs: 5, md: 8 } }}><Box sx={{ maxWidth: 900, mx: "auto", display: "grid", gridTemplateColumns: { xs: "1fr", md: "1fr .85fr" }, gap: 4, alignItems: "center" }}>
    <Box><Button component={Link} href="/" startIcon={<ArrowBackRounded />} color="inherit" sx={{ mb: 4 }}>Back to home</Button><Typography variant="h2" sx={{ fontSize: { xs: "2.5rem", md: "3.2rem" } }}>Build a sharper hiring workflow.</Typography><Typography color="text.secondary" sx={{ mt: 1.5, lineHeight: 1.75 }}>Create a workspace for jobs, candidate screening, analytics and audit-ready review.</Typography><Stack spacing={1.5} sx={{ mt: 3 }}>{["Multi-tenant workspace", "Explainable screening signals", "Protected recruiter routes"].map(x => <Stack direction="row" spacing={1} alignItems="center" key={x}><CheckCircleRounded color="success" fontSize="small" /><Typography>{x}</Typography></Stack>)}</Stack></Box>
    <Box component="form" onSubmit={submit} sx={{ p: { xs: 2.5, sm: 3.5 }, borderRadius: 4, border: "1px solid rgba(255,255,255,.08)", bgcolor: "rgba(255,255,255,.025)" }}><Typography variant="h5" fontWeight={850}>Create workspace</Typography><Typography variant="body2" color="text.secondary" sx={{ mt: .5, mb: 3 }}>Set up your recruiter account.</Typography><Stack spacing={2}>{error && <Alert severity="error">{error}</Alert>}<TextField label="Full name" required autoComplete="name" value={form.fullName} onChange={e => update("fullName", e.target.value)} /><TextField label="Work email" required type="email" autoComplete="email" value={form.email} onChange={e => update("email", e.target.value)} /><TextField label="Organization" required value={form.organization} onChange={e => update("organization", e.target.value)} /><TextField label="Password" required type="password" autoComplete="new-password" value={form.password} onChange={e => update("password", e.target.value)} helperText="Use at least 12 characters." /><Button type="submit" variant="contained" size="large" disabled={loading}>{loading ? "Creating…" : "Create workspace"}</Button><Typography variant="body2" color="text.secondary">Already registered? <Link href="/login">Sign in</Link></Typography></Stack></Box>
  </Box></Container></Box>;
}
