import { ReactNode } from "react";
import { Box, Stack, Typography } from "@mui/material";

export function PageHeader({ eyebrow, title, description, action }: { eyebrow?: string; title: string; description?: string; action?: ReactNode }) {
  return <Stack direction={{ xs: "column", sm: "row" }} justifyContent="space-between" alignItems={{ xs: "flex-start", sm: "flex-end" }} gap={2} sx={{ mb: 3 }}>
    <Box>
      {eyebrow && <Typography variant="overline" color="primary.light" fontWeight={850} letterSpacing=".12em">{eyebrow}</Typography>}
      <Typography variant="h2" sx={{ fontSize: { xs: "2rem", md: "2.7rem" }, mt: .25 }}>{title}</Typography>
      {description && <Typography color="text.secondary" sx={{ mt: .75, maxWidth: 760 }}>{description}</Typography>}
    </Box>
    {action}
  </Stack>;
}
