import { createTheme } from "@mui/material/styles";

export const theme = createTheme({
  palette: {
    mode: "dark",
    primary: { main: "#9b8cff", light: "#c8c0ff", dark: "#6e5ee8" },
    secondary: { main: "#58d6c1" },
    success: { main: "#52d69b" },
    warning: { main: "#f5bd68" },
    error: { main: "#ff7188" },
    background: { default: "#07090d", paper: "#10131a" },
    divider: "rgba(255,255,255,.08)",
  },
  typography: {
    fontFamily: "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    h1: { fontWeight: 850, letterSpacing: "-.055em" },
    h2: { fontWeight: 820, letterSpacing: "-.045em" },
    h3: { fontWeight: 800, letterSpacing: "-.035em" },
    h4: { fontWeight: 800, letterSpacing: "-.03em" },
    button: { textTransform: "none", fontWeight: 750 },
  },
  shape: { borderRadius: 16 },
  components: {
    MuiCssBaseline: { styleOverrides: { body: { backgroundImage: "radial-gradient(circle at 10% -10%, rgba(155,140,255,.13), transparent 32%), radial-gradient(circle at 90% 0%, rgba(88,214,193,.08), transparent 28%)" } } },
    MuiButton: { styleOverrides: { root: { borderRadius: 12, minHeight: 42 } } },
    MuiCard: { styleOverrides: { root: { backgroundImage: "none", border: "1px solid rgba(255,255,255,.075)", boxShadow: "0 18px 50px rgba(0,0,0,.18)" } } },
    MuiPaper: { styleOverrides: { root: { backgroundImage: "none" } } },
    MuiTextField: { defaultProps: { fullWidth: true } },
    MuiChip: { styleOverrides: { root: { fontWeight: 700 } } },
  },
});
