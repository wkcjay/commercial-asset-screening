import type { LocationScore } from "@/lib/types";
import { formatNumber } from "@/lib/format";
import { Badge } from "./ui/badge";
import { Panel } from "./ui/panel";

export function LocationScorePanel({ score }: { score: LocationScore }) {
  return (
    <Panel title="Location Score" action={<Badge tone={score.rating === "strong" ? "good" : score.rating === "moderate" ? "warn" : "danger"}>{score.rating}</Badge>}>
      <div className="flex items-baseline gap-2">
        <span className="text-3xl font-semibold">{formatNumber(score.overall, { maximumFractionDigits: 0 })}</span>
        <span className="text-sm text-slate-500">/ 100</span>
      </div>
      <div className="mt-4 space-y-3">
        {score.components.map((component) => (
          <div key={component.name}>
            <div className="mb-1 flex items-center justify-between text-sm">
              <span className="font-medium">{component.name}</span>
              <span>{formatNumber(component.score, { maximumFractionDigits: 0 })}</span>
            </div>
            <div className="h-2 rounded bg-field">
              <div className="h-2 rounded bg-accent" style={{ width: `${Math.max(0, Math.min(100, component.score))}%` }} />
            </div>
            <p className="mt-1 text-xs text-slate-600">{component.explanation}</p>
          </div>
        ))}
      </div>
    </Panel>
  );
}
