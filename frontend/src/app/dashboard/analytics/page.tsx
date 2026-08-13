"use client";

import { useEffect, useState } from "react";
import { Alert, Card, CardContent, Container, Grid, LinearProgress, Stack, Typography } from "@mui/material";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { analyticsApi, AnalyticsOverview } from "@/lib/api-phase3-4";

function Content() {
  const [data, setData] = useState<AnalyticsOverview | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    analyticsApi.overview().then(setData).catch(e => setError(e instanceof Error ? e.message : "Unable to load analytics"));
  }, []);

  return (
    <Container maxWidth="xl" sx={{ py: 5 }}>
      <Typography variant="overline" color="primary" fontWeight={800}>Recruiting intelligence</Typography>
      <Typography variant="h2" fontWeight={850}>Analytics</Typography>
      {error && <Alert severity="error" sx={{ mt: 3 }}>{error}</Alert>}
      {data && (
        <Grid container spacing={2} sx={{ mt: 2 }}>
          {[
            ["Jobs", data.total_jobs],
            ["Applications", data.total_applications],
            ["Screened", data.screened_applications],
            ["Average score", `${data.average_score.toFixed(1)}`],
          ].map(([label, value]) => (
            <Grid key={label as string} size={{ xs: 12, sm: 6, md: 3 }}>
              <Card sx={{ borderRadius: 4 }}><CardContent><Typography color="text.secondary">{label}</Typography><Typography variant="h3" fontWeight={850}>{value}</Typography></CardContent></Card>
            </Grid>
          ))}
          <Grid size={{ xs: 12 }}>
            <Card sx={{ borderRadius: 4 }}><CardContent>
              <Typography variant="h6" fontWeight={800}>Screening distribution</Typography>
              <Stack spacing={2} sx={{ mt: 3, maxWidth: 700 }}>
                {[
                  ["Strong match", data.recommendations.strong_match],
                  ["Review", data.recommendations.review],
                  ["Low match", data.recommendations.low_match],
                ].map(([label, value]) => (
                  <div key={label as string}>
                    <Stack direction="row" justifyContent="space-between"><Typography>{label}</Typography><Typography>{value}</Typography></Stack>
                    <LinearProgress variant="determinate" value={Number(value) / Math.max(data.screened_applications, 1) * 100} />
                  </div>
                ))}
              </Stack>
            </CardContent></Card>
          </Grid>
        </Grid>
      )}
    </Container>
  );
}

export default function Page() {
  return <ProtectedRoute><Content /></ProtectedRoute>;
}
