import { Box, CircularProgress, Typography } from "@mui/material";
import { scoreTone } from "@/lib/format";

export function ScoreRing({ score, size = 96 }: { score: number; size?: number }) {
  const tone = scoreTone(score);
  const color = tone === "success" ? "success.main" : tone === "warning" ? "warning.main" : "error.main";
  return <Box sx={{ position: "relative", display: "inline-grid", placeItems: "center", width: size, height: size }}>
    <CircularProgress variant="determinate" value={score} size={size} thickness={4} sx={{ color }} />
    <Box sx={{ position: "absolute", inset: 0, display: "grid", placeItems: "center" }}><Typography fontWeight={900} fontSize={size / 4.2}>{Math.round(score)}</Typography></Box>
  </Box>;
}
