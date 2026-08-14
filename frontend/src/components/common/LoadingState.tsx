import { Box, CircularProgress, Skeleton, Stack } from "@mui/material";

export function PageSkeleton({ rows = 4 }: { rows?: number }) {
  return <Stack spacing={2}>
    <Skeleton variant="rounded" height={90} />
    {Array.from({ length: rows }).map((_, i) => <Skeleton key={i} variant="rounded" height={72} />)}
  </Stack>;
}

export function CenterLoader() {
  return <Box sx={{ minHeight: 320, display: "grid", placeItems: "center" }}><CircularProgress size={30} /></Box>;
}
