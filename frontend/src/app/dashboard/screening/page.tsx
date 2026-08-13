"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AutoAwesomeRounded, RefreshRounded } from "@mui/icons-material";
import { Alert, Button, Card, CardContent, Chip, Container, LinearProgress, Stack, Typography } from "@mui/material";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { screeningApi, ScreeningListItem } from "@/lib/api-phase3-4";

function Content() {
  const [rows, setRows] = useState<ScreeningListItem[]>([]);
  const [error, setError] = useState("");
  const [running, setRunning] = useState<string | null>(null);

  async function load() {
    try { setRows(await screeningApi.list()); }
    catch (e) { setError(e instanceof Error ? e.message : "Unable to load screening queue"); }
  }
  useEffect(() => { void load(); }, []);

  async function run(id: string) {
    try { setRunning(id); await screeningApi.run(id); await load(); }
    catch (e) { setError(e instanceof Error ? e.message : "Screening failed"); }
    finally { setRunning(null); }
  }

  return (
    <Container maxWidth="xl" sx={{ py: 5 }}>
      <Stack direction="row" justifyContent="space-between" sx={{ mb: 4 }}>
        <div>
          <Typography variant="overline" color="primary" fontWeight={800}>AI recruitment</Typography>
          <Typography variant="h2" fontWeight={850}>Screening queue</Typography>
          <Typography color="text.secondary">Explainable candidate matching.</Typography>
        </div>
        <Button startIcon={<RefreshRounded />} onClick={() => void load()}>Refresh</Button>
      </Stack>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      <Stack spacing={2}>
        {rows.map(row => (
          <Card key={row.application_id} sx={{ borderRadius: 4 }}>
            <CardContent>
              <Stack direction={{ xs: "column", md: "row" }} justifyContent="space-between" gap={2}>
                <div>
                  <Typography variant="h6" fontWeight={800}>{row.candidate_name}</Typography>
                  <Typography color="text.secondary">{row.job_title}</Typography>
                </div>
                <Stack direction="row" spacing={1}>
                  {row.overall_score !== null && <Chip label={`${row.overall_score.toFixed(1)} / 100`} />}
                  {row.recommendation && <Chip label={row.recommendation.replace("_", " ")} variant="outlined" />}
                  {row.overall_score === null && (
                    <Button variant="contained" startIcon={<AutoAwesomeRounded />} disabled={running === row.application_id} onClick={() => void run(row.application_id)}>
                      {running === row.application_id ? "Screening…" : "Run AI screen"}
                    </Button>
                  )}
                </Stack>
              </Stack>
              {row.overall_score !== null && <LinearProgress variant="determinate" value={row.overall_score} sx={{ mt: 2 }} />}
              <Button component={Link} href={`/dashboard/screening/${row.application_id}`} sx={{ mt: 1 }}>View explanation</Button>
            </CardContent>
          </Card>
        ))}
      </Stack>
    </Container>
  );
}

export default function Page() {
  return <ProtectedRoute><Content /></ProtectedRoute>;
}
