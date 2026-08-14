import { Card, CardContent, LinearProgress, Stack, Typography } from "@mui/material";

export function DistributionCard({ strong, review, low }: { strong: number; review: number; low: number }) {
  const total = Math.max(strong + review + low, 1);
  const items = [["Strong match", strong, "success"], ["Needs review", review, "warning"], ["Low match", low, "error"]] as const;
  return <Card sx={{ height: "100%", borderRadius: 3.5 }}><CardContent sx={{ p: 3 }}><Typography variant="h6" fontWeight={850}>Screening distribution</Typography><Typography variant="body2" color="text.secondary">A snapshot of recommendation bands.</Typography><Stack spacing={2.5} sx={{ mt: 3 }}>{items.map(([label, value, color]) => <Stack key={label} spacing={.8}><Stack direction="row" justifyContent="space-between"><Typography fontWeight={700}>{label}</Typography><Typography color="text.secondary">{value} · {Math.round(value / total * 100)}%</Typography></Stack><LinearProgress color={color} variant="determinate" value={value / total * 100} sx={{ height: 9, borderRadius: 5 }} /></Stack>)}</Stack></CardContent></Card>;
}
