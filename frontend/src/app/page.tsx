"use client";
import Link from "next/link";
import { ArrowForwardRounded, AutoAwesomeRounded, CheckCircleRounded, SecurityRounded, SpeedRounded, InsightsRounded } from "@mui/icons-material";
import { Box, Button, Chip, Container, Grid, Stack, Typography } from "@mui/material";
import { PublicHeader } from "@/components/layout/PublicHeader";

export default function HomePage() {
  return <Box sx={{ minHeight: "100vh", overflow: "hidden", background: "radial-gradient(circle at 72% 5%, rgba(155,140,255,.20), transparent 30%), radial-gradient(circle at 15% 50%, rgba(88,214,193,.08), transparent 28%)" }}>
    <PublicHeader />
    <Container maxWidth="xl" sx={{ pt: { xs: 8, md: 13 }, pb: 12 }}>
      <Grid container spacing={8} alignItems="center">
        <Grid size={{ xs: 12, lg: 7 }}>
          <Chip icon={<AutoAwesomeRounded />} label="AI recruiting intelligence · built for evidence" color="primary" variant="outlined" sx={{ mb: 3 }} />
          <Typography variant="h1" sx={{ fontSize: { xs: "3.25rem", sm: "4.7rem", md: "6rem" }, lineHeight: .94, maxWidth: 850 }}>Your shortlist.<br /><Box component="span" sx={{ color: "primary.light" }}>Without the guesswork.</Box></Typography>
          <Typography sx={{ mt: 3, maxWidth: 720, color: "text.secondary", fontSize: { xs: "1rem", md: "1.15rem" }, lineHeight: 1.8 }}>HireLens helps recruiting teams turn high-volume applications into a transparent review queue using qualification rules, semantic matching and explainable AI.</Typography>
          <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5} sx={{ mt: 4 }}><Button component={Link} href="/signup" size="large" variant="contained" endIcon={<ArrowForwardRounded />}>Create workspace</Button><Button component={Link} href="/jobs" size="large" variant="outlined">Explore open roles</Button></Stack>
          <Stack direction="row" flexWrap="wrap" gap={2.5} sx={{ mt: 4 }}>
            {["Deterministic scoring", "Local semantic signals", "Audit-ready decisions"].map((item) => <Stack key={item} direction="row" spacing={.7} alignItems="center"><CheckCircleRounded sx={{ color: "secondary.main", fontSize: 17 }} /><Typography variant="body2" color="text.secondary">{item}</Typography></Stack>)}
          </Stack>
        </Grid>
        <Grid size={{ xs: 12, lg: 5 }}>
          <Box sx={{ p: 2, borderRadius: 5, background: "linear-gradient(145deg, rgba(255,255,255,.08), rgba(255,255,255,.025))", border: "1px solid rgba(255,255,255,.09)", boxShadow: "0 30px 100px rgba(0,0,0,.35)" }}>
            <Box sx={{ borderRadius: 4, p: 2.25, background: "#0d1016", border: "1px solid rgba(255,255,255,.07)" }}>
              <Stack direction="row" justifyContent="space-between" alignItems="center"><Box><Typography variant="caption" color="text.secondary">SCREENING QUEUE</Typography><Typography fontWeight={850}>Backend Engineer · 148 applicants</Typography></Box><Chip label="Live" size="small" color="success" /></Stack>
              <Stack spacing={1} sx={{ mt: 2 }}>{[["Aarav Sharma", 94, "Strong match"], ["Meera Patel", 86, "Strong match"], ["Rohan Shah", 72, "Review"], ["Ishita Rao", 61, "Review"]].map(([name, score, label]) => <Box key={name} sx={{ p: 1.4, borderRadius: 2.5, background: "rgba(255,255,255,.035)", border: "1px solid rgba(255,255,255,.055)" }}><Stack direction="row" alignItems="center" spacing={1.5}><Box sx={{ width: 34, height: 34, borderRadius: "50%", display: "grid", placeItems: "center", bgcolor: "rgba(155,140,255,.12)", color: "primary.light", fontWeight: 800, fontSize: 12 }}>{String(name).split(" ").map(x => x[0]).join("")}</Box><Box sx={{ flex: 1 }}><Typography variant="body2" fontWeight={750}>{name}</Typography><Typography variant="caption" color="text.secondary">{label}</Typography></Box><Typography fontWeight={900} color={Number(score) >= 80 ? "success.main" : "warning.main"}>{score}</Typography></Stack></Box>)}</Stack>
              <Stack direction="row" spacing={1} sx={{ mt: 2 }}><Box sx={{ flex: 1, p: 1.5, borderRadius: 2.5, bgcolor: "rgba(82,214,155,.06)" }}><Typography variant="caption" color="text.secondary">Strong matches</Typography><Typography variant="h5" fontWeight={900}>42</Typography></Box><Box sx={{ flex: 1, p: 1.5, borderRadius: 2.5, bgcolor: "rgba(245,189,104,.06)" }}><Typography variant="caption" color="text.secondary">Needs review</Typography><Typography variant="h5" fontWeight={900}>29</Typography></Box></Stack>
            </Box>
          </Box>
        </Grid>
      </Grid>

      <Grid container spacing={2} sx={{ mt: 12 }}>
        {[[SecurityRounded, "Security-first sessions", "HttpOnly auth cookies, CSRF protection and tenant-aware APIs."], [SpeedRounded, "Built for volume", "Queue-based screening keeps heavy AI work away from synchronous HTTP requests."], [InsightsRounded, "Explainable by design", "See matched skills, missing requirements and the evidence behind every score."]].map(([Icon, title, text]) => <Grid key={String(title)} size={{ xs: 12, md: 4 }}><Box sx={{ p: 3, height: "100%", borderRadius: 4, border: "1px solid rgba(255,255,255,.07)", background: "rgba(255,255,255,.025)" }}><Icon sx={{ color: "primary.light", mb: 2 }} /><Typography variant="h6" fontWeight={850}>{title}</Typography><Typography color="text.secondary" sx={{ mt: 1, lineHeight: 1.7 }}>{text}</Typography></Box></Grid>)}
      </Grid>
    </Container>
  </Box>;
}
