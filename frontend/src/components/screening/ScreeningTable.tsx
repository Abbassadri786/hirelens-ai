"use client";
import Link from "next/link";
import { AutoAwesomeRounded, ArrowForwardRounded, RefreshRounded } from "@mui/icons-material";
import { Alert, Avatar, Box, Button, Card, Chip, IconButton, Stack, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Tooltip, Typography } from "@mui/material";
import type { ScreeningListItem } from "@/types/domain";
import { ScoreRing } from "@/components/common/ScoreRing";
import { StatusChip } from "@/components/common/StatusChip";
import { formatDate } from "@/lib/format";

export function ScreeningTable({ rows, running, onRun, onRefresh }: { rows: ScreeningListItem[]; running: string | null; onRun: (id: string) => void; onRefresh: () => void }) {
  return <Card sx={{ borderRadius: 3.5, overflow: "hidden" }}>
    <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ px: 2.5, py: 1.75, borderBottom: "1px solid rgba(255,255,255,.06)" }}><Box><Typography fontWeight={850}>Candidate pipeline</Typography><Typography variant="caption" color="text.secondary">Review the evidence behind each screening signal.</Typography></Box><Tooltip title="Refresh"><IconButton onClick={onRefresh}><RefreshRounded /></IconButton></Tooltip></Stack>
    <TableContainer>
      <Table sx={{ minWidth: 760 }}>
        <TableHead><TableRow><TableCell>Candidate</TableCell><TableCell>Role</TableCell><TableCell>Submitted</TableCell><TableCell>Score</TableCell><TableCell>Signal</TableCell><TableCell align="right">Action</TableCell></TableRow></TableHead>
        <TableBody>{rows.map((row) => <TableRow hover key={row.application_id}>
          <TableCell><Stack direction="row" spacing={1.25} alignItems="center"><Avatar sx={{ width: 34, height: 34, bgcolor: "rgba(155,140,255,.12)", color: "primary.light", fontSize: 13 }}>{row.candidate_name.split(" ").map(x => x[0]).slice(0,2).join("").toUpperCase()}</Avatar><Typography fontWeight={750}>{row.candidate_name}</Typography></Stack></TableCell>
          <TableCell><Typography variant="body2" color="text.secondary">{row.job_title}</Typography></TableCell>
          <TableCell><Typography variant="body2" color="text.secondary">{formatDate(row.submitted_at)}</Typography></TableCell>
          <TableCell>{row.overall_score === null ? <Chip size="small" label="Not screened" variant="outlined" /> : <Stack direction="row" spacing={1} alignItems="center"><ScoreRing score={row.overall_score} size={42} /><Typography fontWeight={850}>{row.overall_score.toFixed(0)}</Typography></Stack>}</TableCell>
          <TableCell>{row.recommendation ? <StatusChip status={row.recommendation} /> : <StatusChip status={row.application_status} />}</TableCell>
          <TableCell align="right"><Stack direction="row" justifyContent="flex-end" spacing={.5}>{row.overall_score === null && <Button size="small" variant="contained" startIcon={<AutoAwesomeRounded />} disabled={running === row.application_id} onClick={() => onRun(row.application_id)}>{running === row.application_id ? "Screening…" : "Screen"}</Button>}{row.overall_score !== null && <Button component={Link} href={`/dashboard/screening/${row.application_id}`} size="small" endIcon={<ArrowForwardRounded />}>Review</Button>}</Stack></TableCell>
        </TableRow>)}</TableBody>
      </Table>
    </TableContainer>
    {rows.length === 0 && <Alert severity="info" sx={{ m: 2 }}>No applications are ready for screening yet.</Alert>}
  </Card>;
}
