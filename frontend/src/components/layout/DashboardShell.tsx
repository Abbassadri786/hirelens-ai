"use client";
import { ReactNode, useState } from "react";
import { Box } from "@mui/material";
import { Sidebar } from "@/components/navigation/Sidebar";
import { Topbar } from "@/components/navigation/Topbar";
import { BreadcrumbsBar } from "@/components/navigation/BreadcrumbsBar";

export function DashboardShell({ children }: { children: ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  return <Box sx={{ minHeight: "100vh" }}>
    <Sidebar mobileOpen={mobileOpen} onMobileClose={() => setMobileOpen(false)} />
    <Box sx={{ ml: { md: "252px" } }}>
      <Topbar onMenu={() => setMobileOpen(true)} />
      <Box component="main" sx={{ px: { xs: 2, sm: 3, lg: 4 }, py: { xs: 2, md: 3 }, maxWidth: 1680, mx: "auto" }}>
        <BreadcrumbsBar />
        {children}
      </Box>
    </Box>
  </Box>;
}
