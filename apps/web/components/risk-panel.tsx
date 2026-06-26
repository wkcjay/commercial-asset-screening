import { AlertTriangle } from "lucide-react";
import type { SiteAssessment } from "@/lib/types";
import { titleCase } from "@/lib/format";
import { Badge } from "./ui/badge";
import { Panel } from "./ui/panel";

export function RiskPanel({ assessment }: { assessment: SiteAssessment }) {
  return (
    <Panel title="Risks, Assumptions, Limitations">
      <div className="space-y-3">
        {assessment.riskAssessment.items.map((risk) => (
          <div key={risk.id} className="rounded border border-line bg-field p-3 text-sm">
            <div className="mb-1 flex flex-wrap items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber" aria-hidden="true" />
              <p className="font-semibold">{risk.statement}</p>
              <Badge tone={risk.severity === "high" ? "danger" : risk.severity === "medium" ? "warn" : "good"}>
                {risk.severity}
              </Badge>
              <Badge>{titleCase(risk.category)}</Badge>
            </div>
            {risk.mitigation ? <p className="text-slate-600">{risk.mitigation}</p> : null}
          </div>
        ))}
      </div>
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <TextList title="Assumptions" items={assessment.assumptions.map((item) => item.statement)} />
        <TextList title="Limitations" items={assessment.limitations.map((item) => item.statement)} />
      </div>
    </Panel>
  );
}

function TextList({ title, items }: { title: string; items: string[] }) {
  return (
    <div>
      <h3 className="mb-2 text-sm font-semibold">{title}</h3>
      <ul className="space-y-1 text-sm text-slate-600">
        {items.map((item) => (
          <li key={item}>- {item}</li>
        ))}
      </ul>
    </div>
  );
}
