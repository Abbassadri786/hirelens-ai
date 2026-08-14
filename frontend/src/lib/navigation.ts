import {
  AssessmentRounded,
  BarChartRounded,
  BusinessCenterRounded,
  DashboardRounded,
  HistoryRounded,
  SettingsRounded,
  WorkspacesRounded,
} from "@mui/icons-material";
import type { SvgIconComponent } from "@mui/icons-material";

export type NavItem = { label: string; href: string; icon: SvgIconComponent; description?: string };

export const mainNavigation: NavItem[] = [
  { label: "Overview", href: "/dashboard", icon: DashboardRounded },
  { label: "Jobs", href: "/dashboard/jobs", icon: BusinessCenterRounded },
  { label: "Screening", href: "/dashboard/screening", icon: AssessmentRounded },
  { label: "Analytics", href: "/dashboard/analytics", icon: BarChartRounded },
];

export const systemNavigation: NavItem[] = [
  { label: "Operations", href: "/dashboard/operations", icon: WorkspacesRounded },
  { label: "Audit trail", href: "/dashboard/audit", icon: HistoryRounded },
];

export const publicNavigation: NavItem[] = [
  { label: "Open roles", href: "/jobs", icon: BusinessCenterRounded },
];
