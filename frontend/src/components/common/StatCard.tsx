import { ReactNode } from "react";
import { Box, Card, CardContent, Stack, Typography } from "@mui/material";

export function StatCard({ label, value, hint, icon }: { label: string; value: string | number; hint?: string; icon?: ReactNode }) {
  return <Card sx={{ height: "100%", borderRadius: 3.5 }}><CardContent sx={{ p: 2.5 }}>
    <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
      <Box>
        <Typography variant="body2" color="text.secondary" fontWeight={650}>{label}</Typography>
        <Typography variant="h3" sx={{ mt: .75, fontSize: { xs: "2rem", md: "2.35rem" } }}>{value}</Typography>
        {hint && <Typography variant="caption" color="text.secondary">{hint}</Typography>}
      </Box>
      {icon && <Box sx={{ width: 40, height: 40, display: "grid", placeItems: "center", borderRadius: 2.5, bgcolor: "rgba(155,140,255,.1)", color: "primary.light" }}>{icon}</Box>}
    </Stack>
  </CardContent></Card>;
}
