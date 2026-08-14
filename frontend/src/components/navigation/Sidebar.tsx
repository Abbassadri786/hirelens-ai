"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Box, Divider, Drawer, List, ListItemButton, ListItemIcon, ListItemText, Stack, Typography } from "@mui/material";
import { mainNavigation, systemNavigation, NavItem } from "@/lib/navigation";

const drawerWidth = 252;

function NavSection({ items, onNavigate }: { items: NavItem[]; onNavigate?: () => void }) {
  const pathname = usePathname();
  return <List disablePadding sx={{ display: "grid", gap: .5 }}>
    {items.map((item) => {
      const active = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(`${item.href}/`));
      const Icon = item.icon;
      return <ListItemButton key={item.href} component={Link} href={item.href} onClick={onNavigate} selected={active} sx={{ borderRadius: 2.5, py: 1.1, px: 1.25, "&.Mui-selected": { background: "rgba(155,140,255,.13)", color: "primary.light", "& .MuiListItemIcon-root": { color: "primary.light" } }, "&:hover": { background: "rgba(255,255,255,.055)" } }}>
        <ListItemIcon sx={{ minWidth: 38, color: "text.secondary" }}><Icon fontSize="small" /></ListItemIcon>
        <ListItemText primary={item.label} primaryTypographyProps={{ fontSize: 14, fontWeight: active ? 800 : 650 }} />
      </ListItemButton>;
    })}
  </List>;
}

export function Sidebar({ mobileOpen, onMobileClose }: { mobileOpen: boolean; onMobileClose: () => void }) {
  const content = <Box sx={{ height: "100%", display: "flex", flexDirection: "column", p: 2 }}>
    <Stack direction="row" spacing={1.25} alignItems="center" sx={{ px: 1, py: 1.25, mb: 2 }}>
      <Box sx={{ width: 36, height: 36, borderRadius: "11px", display: "grid", placeItems: "center", background: "linear-gradient(135deg,#9b8cff,#58d6c1)", color: "#0a0b0f", fontWeight: 950 }}>H</Box>
      <Box>
        <Typography fontWeight={900} lineHeight={1}>HireLens</Typography>
        <Typography variant="caption" color="text.secondary">Recruiting intelligence</Typography>
      </Box>
    </Stack>
    <Typography variant="caption" color="text.secondary" fontWeight={800} sx={{ px: 1, mb: 1 }}>WORKSPACE</Typography>
    <NavSection items={mainNavigation} onNavigate={onMobileClose} />
    <Typography variant="caption" color="text.secondary" fontWeight={800} sx={{ px: 1, mt: 3, mb: 1 }}>SYSTEM</Typography>
    <NavSection items={systemNavigation} onNavigate={onMobileClose} />
    <Box sx={{ mt: "auto", p: 1.5, borderRadius: 3, background: "linear-gradient(135deg, rgba(155,140,255,.10), rgba(88,214,193,.06))", border: "1px solid rgba(255,255,255,.07)" }}>
      <Typography variant="caption" color="primary.light" fontWeight={800}>AI SCREENING</Typography>
      <Typography variant="body2" sx={{ mt: .5 }} fontWeight={700}>Evidence over guesswork.</Typography>
      <Typography variant="caption" color="text.secondary">Scores combine rules, semantic signals and explainable analysis.</Typography>
    </Box>
  </Box>;

  return <>
    <Drawer variant="permanent" sx={{ display: { xs: "none", md: "block" }, width: drawerWidth, flexShrink: 0, "& .MuiDrawer-paper": { width: drawerWidth, boxSizing: "border-box", borderRight: "1px solid rgba(255,255,255,.07)", background: "rgba(8,10,14,.82)", backdropFilter: "blur(22px)" } }}>{content}</Drawer>
    <Drawer anchor="left" open={mobileOpen} onClose={onMobileClose} sx={{ display: { md: "none" }, "& .MuiDrawer-paper": { width: drawerWidth, background: "#0b0d12" } }}>{content}</Drawer>
  </>;
}
