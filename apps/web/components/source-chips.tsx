import type { Source } from "@/lib/types";
import { Badge } from "./ui/badge";
import { Panel } from "./ui/panel";

export function SourceChips({ sources }: { sources: Source[] }) {
  return (
    <Panel title="Sources">
      <div className="flex flex-wrap gap-2">
        {sources.map((source) => (
          source.url ? (
            <a key={source.id} href={source.url} target="_blank" rel="noreferrer">
              <Badge tone={source.reliability === "official" || source.reliability === "paid" ? "good" : "warn"}>
                {source.label} · {source.reliability}
              </Badge>
            </a>
          ) : (
            <Badge key={source.id} tone={source.reliability === "official" || source.reliability === "paid" ? "good" : "warn"}>
              {source.label} · {source.reliability}
            </Badge>
          )
        ))}
      </div>
    </Panel>
  );
}
