"use client";

import { useEffect, useState } from "react";
import { Alert, Card, CardContent, Container, Grid, Typography } from "@mui/material";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { operationsApi, ScreeningQueueStats } from "@/lib/api-phase5-8";

function Content() {
  const [stats, setStats] = useState<ScreeningQueueStats | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    operationsApi.queue()
      .then(setStats)
      .catch(e => setError(e instanceof Error ? e.message : "Unable to load queue"));
  }, []);

  return (
    <Container maxWidth="lg" sx={{ py: 5 }}>
      <Typography variant="overline" color="primary" fontWeight={800}>Operations</Typography>
      <Typography variant="h2" fontWeight={850}>Screening queue</Typography>
      {error && <Alert severity="error" sx={{ mt: 3 }}>{error}</Alert>}
      {stats && (
        <Grid container spacing={2} sx={{ mt: 2 }}>
          {Object.entries(stats).map(([status, count]) => (
            <Grid key={status} size={{ xs: 12, sm: 6, md: 3 }}>
              <Card sx={{ borderRadius: 4 }}>
                <CardContent>
                  <Typography color="text.secondary">{status}</Typography>
                  <Typography variant="h3" fontWeight={850}>{count}</Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Container>
  );
}

export default function Page() {
  return <ProtectedRoute><Content /></ProtectedRoute>;
}
