import { Badge } from "./ui/badge";

export function ConfidenceBadge({ level }: { level: "high" | "medium" | "low" }) {
  return <Badge tone={level === "high" ? "good" : level === "medium" ? "warn" : "danger"}>{level} confidence</Badge>;
}

export function CacheBadge({ hit }: { hit?: boolean }) {
  if (hit === undefined) return <Badge>not cached</Badge>;
  return <Badge tone={hit ? "good" : "neutral"}>{hit ? "cache hit" : "computed"}</Badge>;
}

export function RiskBadge({ level }: { level: "low" | "medium" | "high" }) {
  return <Badge tone={level === "low" ? "good" : level === "medium" ? "warn" : "danger"}>{level} risk</Badge>;
}
