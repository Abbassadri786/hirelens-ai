"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Breadcrumbs, Link as MuiLink, Typography } from "@mui/material";
import { titleCase } from "@/lib/format";

export function BreadcrumbsBar() {
  const pathname = usePathname();
  const parts = pathname.split("/").filter(Boolean);
  return <Breadcrumbs sx={{ mb: 1.5 }}>
    <MuiLink component={Link} underline="hover" color="text.secondary" href="/dashboard" variant="body2">Workspace</MuiLink>
    {parts.slice(1).map((part, index, array) => {
      const href = `/${parts.slice(0, index + 2).join("/")}`;
      const isLast = index === array.length - 1;
      return isLast ? <Typography key={href} variant="body2" fontWeight={700}>{titleCase(part)}</Typography> : <MuiLink key={href} component={Link} href={href} underline="hover" color="text.secondary" variant="body2">{titleCase(part)}</MuiLink>;
    })}
  </Breadcrumbs>;
}
