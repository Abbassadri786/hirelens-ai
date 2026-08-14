import { Box, Card, CardContent, Grid, LinearProgress, Stack, Typography } from "@mui/material";

export function MetricBreakdown({ values }: { values: { keyword: number; semantic: number; experience: number; completeness: number } }) {
  const items = [["Keyword match", values.keyword], ["Semantic similarity", values.semantic], ["Experience fit", values.experience], ["Resume completeness", values.completeness]] as const;
  return <Card sx={{ borderRadius: 3.5 }}><CardContent sx={{ p: 3 }}><Typography variant="h6" fontWeight={850}>Score composition</Typography><Typography variant="body2" color="text.secondary">The score is decomposed into understandable signals.</Typography><Grid container spacing={2.5} sx={{ mt: 1 }}>{items.map(([label, value]) => <Grid key={label} size={{ xs: 12, sm: 6 }}><Stack spacing={.75}><Stack direction="row" justifyContent="space-between"><Typography fontWeight={700}>{label}</Typography><Typography color="text.secondary">{value.toFixed(1)}</Typography></Stack><LinearProgress variant="determinate" value={value} sx={{ height: 8, borderRadius: 4 }} /></Stack></Grid>)}</Grid></CardContent></Card>;
}
