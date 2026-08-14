import Link from "next/link";
import { ArrowForwardRounded, LocationOnOutlined, ScheduleRounded } from "@mui/icons-material";
import { Box, Button, Card, CardContent, Chip, Stack, Typography } from "@mui/material";
import type { Job } from "@/types/domain";
import { StatusChip } from "@/components/common/StatusChip";

export function JobCard({ job, manage = false, onPublish }: { job: Job; manage?: boolean; onPublish?: (job: Job) => void }) {
  return <Card sx={{ height: "100%", borderRadius: 3.5, transition: "transform .18s ease, border-color .18s ease", "&:hover": { transform: "translateY(-2px)", borderColor: "rgba(155,140,255,.28)" } }}>
    <CardContent sx={{ p: 2.75, height: "100%", display: "flex", flexDirection: "column" }}>
      <Stack direction="row" justifyContent="space-between" alignItems="flex-start" gap={2}><Box><Typography variant="h6" fontWeight={850}>{job.title}</Typography><Stack direction="row" spacing={1.5} sx={{ mt: .75 }}><Typography variant="caption" color="text.secondary" sx={{ display: "flex", alignItems: "center", gap: .4 }}><LocationOnOutlined sx={{ fontSize: 15 }} />{job.location || "Flexible"}</Typography><Typography variant="caption" color="text.secondary" sx={{ display: "flex", alignItems: "center", gap: .4 }}><ScheduleRounded sx={{ fontSize: 15 }} />{job.employment_type || "Full-time"}</Typography></Stack></Box><StatusChip status={job.status} /></Stack>
      <Typography variant="body2" color="text.secondary" sx={{ mt: 2, lineHeight: 1.7, display: "-webkit-box", WebkitLineClamp: 3, WebkitBoxOrient: "vertical", overflow: "hidden" }}>{job.description}</Typography>
      <Stack direction="row" gap={.75} flexWrap="wrap" sx={{ mt: 2 }}>{job.required_skills.slice(0, 5).map((skill) => <Chip key={skill} label={skill} size="small" variant="outlined" />)}{job.required_skills.length > 5 && <Chip label={`+${job.required_skills.length - 5}`} size="small" />}</Stack>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mt: "auto", pt: 2.5 }}>
        <Typography variant="caption" color="text.secondary">{job.min_experience_years != null ? `${job.min_experience_years}+ years experience` : "Experience flexible"}</Typography>
        {manage ? <Stack direction="row" spacing={1}>{job.status === "DRAFT" && <Button size="small" variant="contained" onClick={() => onPublish?.(job)}>Publish</Button>}<Button size="small" component={Link} href={`/dashboard/jobs/${job.id}`}>Open</Button></Stack> : <Button component={Link} href={`/jobs/${job.id}`} size="small" endIcon={<ArrowForwardRounded />}>View role</Button>}
      </Stack>
    </CardContent>
  </Card>;
}
