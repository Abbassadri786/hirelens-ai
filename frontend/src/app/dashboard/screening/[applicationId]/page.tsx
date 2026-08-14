"use client";
import Link from "next/link";
import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { ArrowBackRounded, CheckCircleRounded, ErrorOutlineRounded, TipsAndUpdatesRounded } from "@mui/icons-material";
import { Alert, Box, Card, CardContent, Chip, Divider, Grid, LinearProgress, Stack, Typography } from "@mui/material";
import { screeningApi } from "@/api/screening";
import type { ScreeningResult } from "@/types/domain";
import { PageSkeleton } from "@/components/common/LoadingState";
import { ScoreRing } from "@/components/common/ScoreRing";
import { StatusChip } from "@/components/common/StatusChip";

function ListBlock({ title, icon, items, tone }: { title: string; icon: ReactNode; items: string[]; tone: "success" | "error" | "warning" }) {
  return <Card sx={{ height: "100%", borderRadius: 3.5 }}><CardContent sx={{ p: 2.75 }}><Stack direction="row" spacing={1} alignItems="center"><Box sx={{ color: `${tone}.main`, display: "grid", placeItems: "center" }}>{icon}</Box><Typography fontWeight={850}>{title}</Typography></Stack>{items.length === 0 ? <Typography color="text.secondary" variant="body2" sx={{ mt: 2 }}>Nothing flagged.</Typography> : <Stack spacing={1.25} sx={{ mt: 2 }}>{items.map((item, index) => <Stack direction="row" spacing={1} key={`${item}-${index}`}><Typography color={`${tone}.main`}>•</Typography><Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.65 }}>{item}</Typography></Stack>)}</Stack>}</CardContent></Card>;
}

export default function ScreeningResultPage() {
  const params = useParams<{ applicationId: string }>(); const [result, setResult] = useState<ScreeningResult | null>(null); const [error, setError] = useState(""); const [loading, setLoading] = useState(true);
  useEffect(() => { screeningApi.get(params.applicationId).then(setResult).catch(e => setError(e instanceof Error ? e.message : "Unable to load screening result")).finally(() => setLoading(false)); }, [params.applicationId]);
  if (loading) return <PageSkeleton rows={7} />; if (error) return <Alert severity="error">{error}</Alert>; if (!result) return null;
  const metrics = [["Keyword match", result.keyword_score], ["Semantic similarity", result.semantic_score], ["Experience fit", result.experience_score], ["Completeness", result.completeness_score]] as const;
  return <Stack spacing={3}><Box><Link href="/dashboard/screening" style={{ display: "inline-flex", alignItems: "center", gap: 6, color: "inherit", marginBottom: 12 }}><ArrowBackRounded fontSize="small" /> Back to screening</Link><Stack direction={{ xs: "column", md: "row" }} justifyContent="space-between" alignItems={{ xs: "flex-start", md: "center" }} gap={2}><Box><Typography variant="overline" color="primary.light" fontWeight={850}>Explainable screening</Typography><Typography variant="h2">Screening evidence</Typography></Box><StatusChip status={result.recommendation} /></Stack></Box>
    <Card sx={{ borderRadius: 4, background: "linear-gradient(135deg, rgba(155,140,255,.12), rgba(16,19,26,.96))" }}><CardContent sx={{ p: { xs: 3, md: 4 } }}><Grid container spacing={4} alignItems="center"><Grid size={{ xs: 12, md: 3 }} sx={{ textAlign: "center" }}><ScoreRing score={result.overall_score} size={156} /><Typography variant="h6" fontWeight={850} sx={{ mt: 1 }}>Overall match</Typography><Typography variant="caption" color="text.secondary">This is a decision-support signal, not an automatic hiring decision.</Typography></Grid><Grid size={{ xs: 12, md: 9 }}><Typography variant="h5" fontWeight={850}>Why this candidate scored {result.overall_score.toFixed(1)}</Typography><Typography color="text.secondary" sx={{ mt: 1, lineHeight: 1.8 }}>{result.explanation}</Typography><Grid container spacing={2} sx={{ mt: 1 }}>{metrics.map(([label, value]) => <Grid key={label} size={{ xs: 12, sm: 6 }}><Stack spacing={.7}><Stack direction="row" justifyContent="space-between"><Typography variant="body2" fontWeight={700}>{label}</Typography><Typography variant="body2" color="text.secondary">{value.toFixed(1)}</Typography></Stack><LinearProgress variant="determinate" value={value} sx={{ height: 7, borderRadius: 4 }} /></Stack></Grid>)}</Grid></Grid></Grid></CardContent></Card>
    <Grid container spacing={2}><Grid size={{ xs: 12, md: 4 }}><ListBlock title="Matched skills" icon={<CheckCircleRounded />} items={result.matched_skills} tone="success" /></Grid><Grid size={{ xs: 12, md: 4 }}><ListBlock title="Missing required" icon={<ErrorOutlineRounded />} items={result.missing_required_skills} tone="error" /></Grid><Grid size={{ xs: 12, md: 4 }}><ListBlock title="Improvement suggestions" icon={<TipsAndUpdatesRounded />} items={result.improvement_suggestions} tone="warning" /></Grid></Grid>
    <Grid container spacing={2}><Grid size={{ xs: 12, md: 6 }}><ListBlock title="Strengths" icon={<CheckCircleRounded />} items={result.strengths} tone="success" /></Grid><Grid size={{ xs: 12, md: 6 }}><ListBlock title="Concerns" icon={<ErrorOutlineRounded />} items={result.concerns} tone="error" /></Grid></Grid>
    <Card sx={{ borderRadius: 3.5 }}><CardContent sx={{ p: 3 }}><Typography variant="h6" fontWeight={850}>Screening provenance</Typography><Divider sx={{ my: 2 }} /><Grid container spacing={2}>{[["Provider", result.provider], ["Model", result.model_name], ["Processing time", result.processing_ms ? `${result.processing_ms} ms` : "—"], ["Created", new Date(result.created_at).toLocaleString("en-IN")]].map(([label, value]) => <Grid key={label} size={{ xs: 12, sm: 6, md: 3 }}><Typography variant="caption" color="text.secondary">{label}</Typography><Typography fontWeight={750} sx={{ mt: .35 }}>{value}</Typography></Grid>)}</Grid></CardContent></Card>
  </Stack>;
}
