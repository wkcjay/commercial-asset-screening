import { Database, MapPinned } from "lucide-react";
import type { ApiEnvelopeMeta, SiteAssessment } from "@/lib/types";
import { formatNumber } from "@/lib/format";
import { CacheBadge, ConfidenceBadge, RiskBadge } from "./status-badge";
import { Badge } from "./ui/badge";

export function AssessmentHeader({ assessment, meta }: { assessment: SiteAssessment; meta: ApiEnvelopeMeta }) {
  return (
    <section className="rounded-md border border-line bg-white p-4 shadow-panel">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <MapPinned className="h-5 w-5 text-accent" aria-hidden="true" />
            <h1 className="text-xl font-semibold">{assessment.site.name}</h1>
          </div>
          <p className="mt-1 text-sm text-slate-600">{assessment.site.address}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Badge>{assessment.site.planningArea}</Badge>
            <Badge>District {assessment.site.district}</Badge>
            <Badge>{assessment.site.tenure || "unknown tenure"}</Badge>
          </div>
        </div>
        <div className="flex flex-wrap gap-2 lg:justify-end">
          <ConfidenceBadge level={assessment.confidence.level} />
          <RiskBadge level={assessment.riskAssessment.overallRiskLevel} />
          <CacheBadge hit={meta.cache?.hit} />
          <Badge tone="neutral">
            <Database className="mr-1 h-3.5 w-3.5" aria-hidden="true" />
            {meta.dataVersion || "no data version"}
          </Badge>
        </div>
      </div>
      <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-4">
        <Metric label="Location score" value={`${formatNumber(assessment.locationScore.overall, { maximumFractionDigits: 0 })}/100`} />
        <Metric label="Confidence score" value={`${assessment.confidence.score}/100`} />
        <Metric label="Selected comps" value={String(assessment.comparableSummary.selectedCount)} />
        <Metric label="Sources" value={String(assessment.sources.length)} />
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-line bg-field px-3 py-2">
      <p className="text-xs font-medium uppercase text-slate-500">{label}</p>
      <p className="mt-1 text-lg font-semibold">{value}</p>
    </div>
  );
}
