import type { AmenitySummary } from "@/lib/types";
import { formatKm, titleCase } from "@/lib/format";
import { Badge } from "./ui/badge";
import { Panel } from "./ui/panel";

export function AmenityList({ summary }: { summary: AmenitySummary }) {
  return (
    <Panel title="Amenities And Accessibility">
      <div className="flex flex-wrap gap-2">
        {Object.entries(summary.categoryCounts).map(([category, count]) => (
          <Badge key={category}>
            {titleCase(category)}: {count}
          </Badge>
        ))}
      </div>
      <div className="mt-4 space-y-2">
        {summary.nearbyAmenities.slice(0, 8).map((amenity) => (
          <div key={amenity.id} className="flex items-center justify-between gap-3 rounded border border-line px-3 py-2 text-sm">
            <div>
              <p className="font-medium">{amenity.name}</p>
              <p className="text-xs text-slate-600">{titleCase(amenity.category)}</p>
            </div>
            <span className="whitespace-nowrap text-slate-600">{formatKm(amenity.distanceKm)}</span>
          </div>
        ))}
      </div>
    </Panel>
  );
}
