import { ReactNode } from "react";
import { Alert, Box, Button, Typography } from "@mui/material";

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return <Alert severity="error" action={onRetry ? <Button color="inherit" size="small" onClick={onRetry}>Retry</Button> : undefined}>{message}</Alert>;
}

export function EmptyState({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return <Box sx={{ py: 9, textAlign: "center", border: "1px dashed rgba(255,255,255,.12)", borderRadius: 4, background: "rgba(255,255,255,.018)" }}>
    <Typography variant="h6" fontWeight={800}>{title}</Typography>
    <Typography color="text.secondary" sx={{ maxWidth: 500, mx: "auto", mt: 1 }}>{description}</Typography>
    {action && <Box sx={{ mt: 3 }}>{action}</Box>}
  </Box>;
}
