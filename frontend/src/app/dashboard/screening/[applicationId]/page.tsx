"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Alert, Card, CardContent, Chip, Container, Grid, LinearProgress, Stack, Typography } from "@mui/material";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { screeningApi, ScreeningResult } from "@/lib/api-phase3-4";

function Content() {
  const params = useParams<{ applicationId: string }>();
  const [result, setResult] = useState<ScreeningResult | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    screeningApi.get(params.applicationId).then(setResult).catch(e => setError(e instanceof Error ? e.message : "Unable to load result"));
  }, [params.applicationId]);

  if (error) return <Container sx={{ py: 5 }}><Alert severity="error">{error}</Alert></Container>;
  if (!result) return <Container sx={{ py: 5 }}><LinearProgress /></Container>;

  const metrics = [
    ["Keyword", result.keyword_score],
    ["Semantic", result.semantic_score],
    ["Experience", result.experience_score],
    ["Completeness", result.completeness_score],
  ];

  return (
    <Container maxWidth="lg" sx={{ py: 5 }}>
      <Card sx={{ borderRadius: 5 }}><CardContent sx={{ p: { xs: 3, md: 5 } }}>
        <Stack direction={{ xs: "column", md: "row" }} justifyContent="space-between">
          <div>
            <Typography variant="overline" color="primary" fontWeight={800}>Explainable AI screening</Typography>
            <Typography variant="h2" fontWeight={850}>{result.overall_score.toFixed(1)}</Typography>
            <Typography color="text.secondary">Overall score / 100</Typography>
          </div>
          <Chip label={result.recommendation.replace("_", " ")} />
        </Stack>

        <Grid container spacing={2} sx={{ mt: 3 }}>
          {metrics.map(([label, value]) => (
            <Grid key={label} size={{ xs: 12, sm: 6 }}>
              <Typography fontWeight={700}>{label}</Typography>
              <LinearProgress variant="determinate" value={Number(value)} sx={{ mt: 1 }} />
              <Typography variant="caption">{Number(value).toFixed(1)} / 100</Typography>
            </Grid>
          ))}
        </Grid>

        <Grid container spacing={3} sx={{ mt: 2 }}>
          <Grid size={{ xs: 12, md: 4 }}>
            <Typography variant="h6" fontWeight={800}>Matched skills</Typography>
            <Stack direction="row" gap={1} flexWrap="wrap" sx={{ mt: 1 }}>{result.matched_skills.map(x => <Chip key={x} label={x} color="success" variant="outlined" />)}</Stack>
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <Typography variant="h6" fontWeight={800}>Missing required</Typography>
            <Stack direction="row" gap={1} flexWrap="wrap" sx={{ mt: 1 }}>{result.missing_required_skills.map(x => <Chip key={x} label={x} color="error" variant="outlined" />)}</Stack>
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <Typography variant="h6" fontWeight={800}>Strengths</Typography>
            {result.strengths.map((x, i) => <Typography key={i}>• {x}</Typography>)}
          </Grid>
          <Grid size={{ xs: 12 }}>
            <Typography variant="h6" fontWeight={800}>Explanation</Typography>
            <Typography color="text.secondary" sx={{ mt: 1, lineHeight: 1.8 }}>{result.explanation}</Typography>
          </Grid>
          <Grid size={{ xs: 12 }}>
            <Typography variant="h6" fontWeight={800}>Concerns & suggestions</Typography>
            {[...result.concerns, ...result.improvement_suggestions].map((x, i) => <Typography key={i}>• {x}</Typography>)}
          </Grid>
        </Grid>
      </CardContent></Card>
    </Container>
  );
}

export default function Page() {
  return <ProtectedRoute><Content /></ProtectedRoute>;
}
