"use client";

import { ReactNode } from "react";
import { Box, CircularProgress } from "@mui/material";
import { useAuth } from "./AuthProvider";

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <Box
        sx={{
          minHeight: "70vh",
          display: "grid",
          placeItems: "center",
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  /*
   * AuthProvider is responsible for redirecting
   * when /auth/me returns 401.
   *
   * Do NOT redirect from here again.
   */
  if (!user) {
    return null;
  }

  return <>{children}</>;
}
