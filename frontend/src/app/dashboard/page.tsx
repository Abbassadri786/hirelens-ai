import { OverviewContent } from "@/components/dashboard/OverviewContent";
import { PageHeader } from "@/components/common/PageHeader";

export default function DashboardPage() {
  return <><PageHeader eyebrow="Workspace overview" title="Good morning, recruiter." description="A clear view of your hiring funnel, screening signals and the work that needs attention." /><OverviewContent /></>;
}
