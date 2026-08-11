"use client";

import Link from "next/link";
import {
  ArrowForwardRounded,
  AutoAwesomeRounded,
  SecurityRounded,
  HubRounded,
} from "@mui/icons-material";
import {
  Box,
  Button,
  Chip,
  Container,
  Stack,
  Typography,
} from "@mui/material";

export default function HomePage() {
  return (
    <Box
      sx={{
        minHeight: "100vh",
        background:
          "radial-gradient(circle at 80% 10%, rgba(91, 79, 255, .18), transparent 30%), #08090d",
        color: "white",
      }}
    >
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Stack
          direction="row"
          justifyContent="space-between"
          alignItems="center"
          sx={{ mb: 14 }}
        >
          <Stack direction="row" spacing={1.5} alignItems="center">
            <Box
              sx={{
                width: 38,
                height: 38,
                borderRadius: "12px",
                display: "grid",
                placeItems: "center",
                background: "linear-gradient(135deg,#7c6cff,#35d1b5)",
                fontWeight: 900,
              }}
            >
              H
            </Box>
            <Typography fontWeight={800}>HireLens</Typography>
          </Stack>

          <Stack direction="row" spacing={1}>
            <Button component={Link} href="/login" color="inherit">
              Sign in
            </Button>
            <Button
              component={Link}
              href="/signup"
              variant="contained"
              endIcon={<ArrowForwardRounded />}
              sx={{ borderRadius: 2.5 }}
            >
              Get started
            </Button>
          </Stack>
        </Stack>

        <Box sx={{ maxWidth: 850 }}>
          <Chip
            icon={<AutoAwesomeRounded />}
            label="AI recruitment intelligence"
            sx={{
              mb: 3,
              color: "#d9d5ff",
              backgroundColor: "rgba(124,108,255,.12)",
              border: "1px solid rgba(124,108,255,.25)",
            }}
          />
          <Typography
            component="h1"
            sx={{
              fontSize: { xs: "3.4rem", md: "6.2rem" },
              lineHeight: 0.94,
              letterSpacing: "-.065em",
              fontWeight: 850,
            }}
          >
            Screen smarter.
            <br />
            Hire with evidence.
          </Typography>

          <Typography
            sx={{
              mt: 4,
              maxWidth: 700,
              color: "rgba(255,255,255,.62)",
              fontSize: "1.15rem",
              lineHeight: 1.7,
            }}
          >
            A secure recruitment platform that combines deterministic
            qualification matching, semantic similarity and explainable AI
            analysis to help recruiters review high-volume applications.
          </Typography>

          <Stack direction="row" spacing={2} sx={{ mt: 5 }}>
            <Button
              component={Link}
              href="/signup"
              variant="contained"
              size="large"
              endIcon={<ArrowForwardRounded />}
              sx={{ px: 3, py: 1.5, borderRadius: 3 }}
            >
              Create workspace
            </Button>
            <Button
              component={Link}
              href="/login"
              variant="outlined"
              size="large"
              sx={{
                px: 3,
                py: 1.5,
                borderRadius: 3,
                color: "white",
                borderColor: "rgba(255,255,255,.2)",
              }}
            >
              View demo
            </Button>
          </Stack>
        </Box>

        <Stack
          direction={{ xs: "column", md: "row" }}
          spacing={2}
          sx={{ mt: 16 }}
        >
          {[
            {
              icon: <HubRounded />,
              title: "Hybrid screening",
              text: "Rules + embeddings + LLM reasoning.",
            },
            {
              icon: <SecurityRounded />,
              title: "Security first",
              text: "HttpOnly sessions, RBAC and tenant isolation.",
            },
            {
              icon: <AutoAwesomeRounded />,
              title: "Explainable AI",
              text: "Evidence behind every future match score.",
            },
          ].map((item) => (
            <Box
              key={item.title}
              sx={{
                flex: 1,
                p: 3,
                borderRadius: 4,
                background: "rgba(255,255,255,.035)",
                border: "1px solid rgba(255,255,255,.08)",
                backdropFilter: "blur(18px)",
              }}
            >
              <Box sx={{ color: "#9b91ff", mb: 2 }}>{item.icon}</Box>
              <Typography fontWeight={800}>{item.title}</Typography>
              <Typography
                sx={{ mt: 1, color: "rgba(255,255,255,.55)" }}
              >
                {item.text}
              </Typography>
            </Box>
          ))}
        </Stack>
      </Container>
    </Box>
  );
}
