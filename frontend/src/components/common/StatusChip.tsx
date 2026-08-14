import { Chip } from "@mui/material";
import { titleCase } from "@/lib/format";

export function StatusChip({ status }: { status: string }) {
  const color = status === "PUBLISHED" || status === "STRONG_MATCH" || status === "SHORTLISTED" ? "success" : status === "REVIEW" || status === "UNDER_REVIEW" || status === "DRAFT" ? "warning" : status === "REJECTED" || status === "LOW_MATCH" ? "error" : "default";
  return <Chip size="small" label={titleCase(status)} color={color} variant={color === "default" ? "outlined" : "filled"} />;
}
