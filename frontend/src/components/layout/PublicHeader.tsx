"use client";
import Link from "next/link";
import { ArrowForwardRounded } from "@mui/icons-material";
import { Box, Button, Container, Stack, Typography } from "@mui/material";
import { useAuth } from "@/components/auth/AuthProvider";

export function PublicHeader() {
  const { user } = useAuth();
  return <Box component="header" sx={{ py: 2.25, position: "sticky", top: 0, zIndex: 20, background: "rgba(7,9,13,.72)", backdropFilter: "blur(20px)", borderBottom: "1px solid rgba(255,255,255,.06)" }}>
    <Container maxWidth="xl">
      <Stack direction="row" alignItems="center" justifyContent="space-between">
        <Stack direction="row" spacing={1.25} alignItems="center" component={Link} href="/" sx={{ textDecoration: "none" }}>
          <Box sx={{ width: 34, height: 34, borderRadius: "10px", display: "grid", placeItems: "center", background: "linear-gradient(135deg,#9b8cff,#58d6c1)", color: "#090b10", fontWeight: 950 }}>H</Box>
          <Box><Typography fontWeight={900} lineHeight={1}>HireLens</Typography><Typography variant="caption" color="text.secondary">AI recruiting workspace</Typography></Box>
        </Stack>
        <Stack direction="row" spacing={1} alignItems="center">
          <Button component={Link} href="/jobs" color="inherit">Open roles</Button>
          {user ? <Button component={Link} href="/dashboard" variant="contained" endIcon={<ArrowForwardRounded />}>Workspace</Button> : <><Button component={Link} href="/login" color="inherit">Sign in</Button><Button component={Link} href="/signup" variant="contained">Get started</Button></>}
        </Stack>
      </Stack>
    </Container>
  </Box>;
}
