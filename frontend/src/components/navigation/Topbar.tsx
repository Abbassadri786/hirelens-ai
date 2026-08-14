"use client";
import { useState } from "react";
import { AccountCircleRounded, LogoutRounded, MenuRounded, NotificationsNoneRounded } from "@mui/icons-material";
import { AppBar, Avatar, Box, Divider, IconButton, Menu, MenuItem, Stack, Toolbar, Typography } from "@mui/material";
import { useAuth } from "@/components/auth/AuthProvider";

export function Topbar({ onMenu }: { onMenu: () => void }) {
  const { user, signOut } = useAuth();
  const [anchor, setAnchor] = useState<null | HTMLElement>(null);
  const initials = user?.full_name?.split(" ").map((x) => x[0]).slice(0, 2).join("").toUpperCase() || "U";

  return <AppBar position="sticky" elevation={0} sx={{ background: "rgba(7,9,13,.72)", backdropFilter: "blur(20px)", borderBottom: "1px solid rgba(255,255,255,.07)" }}>
    <Toolbar sx={{ minHeight: 72, px: { xs: 2, md: 3 } }}>
      <IconButton onClick={onMenu} sx={{ display: { md: "none" }, mr: 1 }}><MenuRounded /></IconButton>
      <Box sx={{ flex: 1 }}>
        <Typography variant="body2" color="text.secondary">Workspace</Typography>
        <Typography fontWeight={800} noWrap>{user?.full_name ? `Good to see you, ${user.full_name.split(" ")[0]}` : "Recruiting workspace"}</Typography>
      </Box>
      <IconButton sx={{ mr: 1 }} aria-label="notifications"><NotificationsNoneRounded /></IconButton>
      <Stack direction="row" spacing={1.25} alignItems="center" onClick={(e) => setAnchor(e.currentTarget)} sx={{ cursor: "pointer", pl: 1 }}>
        <Avatar sx={{ width: 36, height: 36, bgcolor: "rgba(155,140,255,.2)", color: "primary.light", fontWeight: 800 }}>{initials}</Avatar>
        <Box sx={{ display: { xs: "none", sm: "block" } }}>
          <Typography variant="body2" fontWeight={800}>{user?.full_name}</Typography>
          <Typography variant="caption" color="text.secondary">{user?.role?.replaceAll("_", " ")}</Typography>
        </Box>
        <AccountCircleRounded sx={{ color: "text.secondary" }} />
      </Stack>
      <Menu anchorEl={anchor} open={Boolean(anchor)} onClose={() => setAnchor(null)} PaperProps={{ sx: { minWidth: 190, mt: 1, border: "1px solid rgba(255,255,255,.08)" } }}>
        <MenuItem disabled>{user?.email}</MenuItem>
        <Divider />
        <MenuItem onClick={() => void signOut()}><LogoutRounded fontSize="small" sx={{ mr: 1.5 }} />Sign out</MenuItem>
      </Menu>
    </Toolbar>
  </AppBar>;
}
