import type { ComparableSummary } from "@/lib/types";
import { formatPsf, formatNumber, formatRegistrationMonth, titleCase } from "@/lib/format";
import { Panel } from "./ui/panel";
import { Badge } from "./ui/badge";

export function ComparableMetrics({ summary }: { summary: ComparableSummary }) {
  return (
    <Panel title="Comparable Transaction Summary" action={<Badge>{titleCase(summary.trend.label)}</Badge>}>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Metric label="Median" value={formatPsf(summary.medianPricePsf)} />
        <Metric label="Range" value={`${formatPsf(summary.minPricePsf)} - ${formatPsf(summary.maxPricePsf)}`} />
        <Metric label="Candidates" value={String(summary.candidateCount)} />
        <Metric label="Latest Month" value={formatRegistrationMonth(summary.latestTransactionDate)} />
      </div>
      <p className="mt-3 text-sm text-slate-600">{summary.trend.basis}</p>
      {summary.trend.percentChange !== undefined ? (
        <p className="mt-1 text-sm text-slate-600">
          Recent versus earlier median shift: {formatNumber(summary.trend.percentChange * 100, { maximumFractionDigits: 1 })}%.
        </p>
      ) : null}
    </Panel>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs font-medium uppercase text-slate-500">{label}</p>
      <p className="mt-1 text-sm font-semibold">{value}</p>
    </div>
  );
}
