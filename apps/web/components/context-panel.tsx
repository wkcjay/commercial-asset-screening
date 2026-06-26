import type { DemographicContext, PlanningContext } from "@/lib/types";
import { formatNumber, titleCase } from "@/lib/format";
import { Badge } from "./ui/badge";
import { Panel } from "./ui/panel";

export function ContextPanel({
  demographic,
  planning,
}: {
  demographic?: DemographicContext | null;
  planning?: PlanningContext | null;
}) {
  return (
    <Panel title="Demographic And Planning Context">
      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <div className="mb-2 flex items-center gap-2">
            <h3 className="text-sm font-semibold">Demographics</h3>
            {demographic ? <Badge>{demographic.planningArea}</Badge> : <Badge tone="warn">missing</Badge>}
          </div>
          {demographic ? (
            <dl className="space-y-1 text-sm">
              <Pair label="Population" value={formatNumber(demographic.population)} />
              <Pair label="Households" value={formatNumber(demographic.residentHouseholds)} />
              <Pair label="Median age" value={formatNumber(demographic.medianAge, { maximumFractionDigits: 1 })} />
              <Pair label="Income band" value={demographic.householdIncomeBand || "n/a"} />
            </dl>
          ) : (
            <p className="text-sm text-slate-600">No demographic context available.</p>
          )}
        </div>
        <div>
          <div className="mb-2 flex items-center gap-2">
            <h3 className="text-sm font-semibold">Planning</h3>
            {planning ? <Badge tone="warn">verification required</Badge> : <Badge tone="warn">missing</Badge>}
          </div>
          {planning ? (
            <dl className="space-y-1 text-sm">
              <Pair label="Zoning" value={titleCase(planning.zoning || "unknown")} />
              <Pair label="GPR" value={formatNumber(planning.grossPlotRatio, { maximumFractionDigits: 1 })} />
              <Pair label="Height control" value={planning.heightControl || "n/a"} />
            </dl>
          ) : (
            <p className="text-sm text-slate-600">No planning context available.</p>
          )}
        </div>
      </div>
    </Panel>
  );
}

function Pair({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4">
      <dt className="text-slate-500">{label}</dt>
      <dd className="text-right font-medium">{value}</dd>
    </div>
  );
}
