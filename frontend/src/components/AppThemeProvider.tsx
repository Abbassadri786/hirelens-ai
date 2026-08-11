"use client";

import { CssBaseline, ThemeProvider, createTheme } from "@mui/material";
import { ReactNode, useMemo } from "react";

export function AppThemeProvider({ children }: { children: ReactNode }) {
  const theme = useMemo(
    () =>
      createTheme({
        palette: {
          mode: "dark",
          primary: { main: "#7c6cff" },
          secondary: { main: "#35d1b5" },
          background: {
            default: "#08090d",
            paper: "#11131a",
          },
        },
        typography: {
          fontFamily:
            "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
        },
        shape: { borderRadius: 14 },
        components: {
          MuiButton: {
            styleOverrides: {
              root: {
                textTransform: "none",
                fontWeight: 750,
              },
            },
          },
          MuiTextField: {
            defaultProps: { fullWidth: true },
          },
          MuiCard: {
            styleOverrides: {
              root: {
                backgroundImage: "none",
                border: "1px solid rgba(255,255,255,.07)",
              },
            },
          },
        },
      }),
    [],
  );

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      {children}
    </ThemeProvider>
  );
}
