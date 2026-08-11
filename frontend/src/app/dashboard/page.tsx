"use client";

import { useEffect, useState } from "react";
import {
  Box,
  Card,
  CardContent,
  Chip,
  Container,
  Grid,
  Stack,
  Typography,
} from "@mui/material";
import { api, User } from "@/lib/api";

export default function DashboardPage() {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    api.me().then(setUser).catch(() => {
      window.location.href = "/login";
    });
  }, []);

  return (
    <Box sx={{ minHeight: "100vh", background: "background.default", py: 5 }}>
      <Container maxWidth="xl">
        <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 5 }}>
          <Box>
            <Typography variant="overline" color="primary" fontWeight={800}>Workspace</Typography>
            <Typography variant="h2" fontWeight={850} letterSpacing="-.05em">Recruitment overview</Typography>
            <Typography color="text.secondary" sx={{ mt: 1 }}>
              {user ? `Welcome, ${user.full_name}` : "Loading your workspace…"}
            </Typography>
          </Box>
          {user && <Chip label={user.role.replaceAll("_", " ")} color="primary" />}
        </Stack>

        <Grid container spacing={2}>
          {[
            ["Active jobs", "0", "Create your first job in Phase 2."],
            ["Applications", "0", "Application pipeline arrives next."],
            ["Screened", "0", "AI screening is Phase 3."],
            ["Shortlisted", "0", "Evidence-based ranking is coming."],
          ].map(([title, value, caption]) => (
            <Grid key={title} size={{ xs: 12, sm: 6, lg: 3 }}>
              <Card sx={{ height: "100%", borderRadius: 4 }}>
                <CardContent sx={{ p: 3 }}>
                  <Typography color="text.secondary" variant="body2">{title}</Typography>
                  <Typography variant="h2" fontWeight={850} sx={{ mt: 1 }}>{value}</Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>{caption}</Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>

        <Card sx={{ mt: 2, borderRadius: 4 }}>
          <CardContent sx={{ p: { xs: 3, md: 5 } }}>
            <Typography variant="h5" fontWeight={800}>Phase 1 foundation is live</Typography>
            <Typography color="text.secondary" sx={{ mt: 1, maxWidth: 760, lineHeight: 1.7 }}>
              Authentication, organization tenancy, role-based access, PostgreSQL,
              secure cookies, CSRF protection and the frontend shell are now in place.
              The next milestone is the real candidate and job domain.
            </Typography>
          </CardContent>
        </Card>
      </Container>
    </Box>
  );
}
