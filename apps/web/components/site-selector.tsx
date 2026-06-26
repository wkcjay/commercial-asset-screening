"use client";

import { Building2 } from "lucide-react";
import type { SiteSummary } from "@/lib/types";
import { Badge } from "./ui/badge";

export function SiteSelector({
  sites,
  selectedSiteId,
  onSelect,
}: {
  sites: SiteSummary[];
  selectedSiteId?: string;
  onSelect: (siteId: string) => void;
}) {
  return (
    <div className="space-y-3">
      <label className="text-xs font-semibold uppercase text-slate-500" htmlFor="site-select">
        Sample site
      </label>
      <div className="flex items-center gap-2 rounded-md border border-line bg-white px-3">
        <Building2 className="h-4 w-4 text-accent" aria-hidden="true" />
        <select
          id="site-select"
          className="h-11 min-w-0 flex-1 bg-transparent text-sm outline-none"
          value={selectedSiteId || ""}
          onChange={(event) => onSelect(event.target.value)}
        >
          <option value="" disabled>
            Select a site
          </option>
          {sites.map((site) => (
            <option key={site.id} value={site.id}>
              {site.name}
            </option>
          ))}
        </select>
      </div>
      {selectedSiteId ? (
        <div className="space-y-2">
          {sites
            .filter((site) => site.id === selectedSiteId)
            .map((site) => (
              <div key={site.id} className="rounded-md border border-line bg-white p-3 text-sm">
                <p className="font-semibold">{site.name}</p>
                <p className="mt-1 text-slate-600">{site.address}</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  <Badge>{site.planningArea}</Badge>
                  <Badge>District {site.district}</Badge>
                  <Badge tone="warn">{site.dataReliability}</Badge>
                </div>
              </div>
            ))}
        </div>
      ) : null}
    </div>
  );
}
