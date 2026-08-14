import { ReactNode } from "react";
import { Box } from "@mui/material";
import { PublicHeader } from "./PublicHeader";
export function PublicShell({ children }: { children: ReactNode }) {
  return <Box sx={{ minHeight: "100vh" }}><PublicHeader />{children}</Box>;
}
