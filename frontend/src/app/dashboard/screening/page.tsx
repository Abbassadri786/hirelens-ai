"use client";
import { useEffect, useState } from "react";
import { Alert, Button, Stack } from "@mui/material";
import { screeningApi } from "@/api/screening";
import type { ScreeningListItem } from "@/types/domain";
import { PageHeader } from "@/components/common/PageHeader";
import { PageSkeleton } from "@/components/common/LoadingState";
import { ScreeningTable } from "@/components/screening/ScreeningTable";

export default function ScreeningPage() {
  const [rows, setRows] = useState<ScreeningListItem[]>([]); const [loading, setLoading] = useState(true); const [error, setError] = useState(""); const [running, setRunning] = useState<string | null>(null);
  const load = () => { setLoading(true); screeningApi.list().then(setRows).catch(e => setError(e instanceof Error ? e.message : "Unable to load screening queue")).finally(() => setLoading(false)); };
  useEffect(() => { load(); }, []);
  async function run(id: string) { setRunning(id); setError(""); try { const result = await screeningApi.run(id); setRows(current => current.map(row => row.application_id === id ? { ...row, overall_score: result.overall_score, recommendation: result.recommendation } : row)); } catch(e) { setError(e instanceof Error ? e.message : "Screening failed"); } finally { setRunning(null); } }
  return <Stack spacing={2}><PageHeader eyebrow="AI screening" title="Candidate screening" description="Review candidate signals, run screening on demand and open the evidence behind every score." action={<Button variant="outlined" onClick={load}>Refresh queue</Button>} />{error && <Alert severity="error">{error}</Alert>}{loading ? <PageSkeleton rows={6} /> : <ScreeningTable rows={rows} running={running} onRun={run} onRefresh={load} />}</Stack>;
}
