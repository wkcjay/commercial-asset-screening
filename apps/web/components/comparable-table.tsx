import type { ComparableWithDistance } from "@/lib/types";
import { formatKm, formatPsf, formatRegistrationMonth } from "@/lib/format";
import { Panel } from "./ui/panel";

export function ComparableTable({ comparables }: { comparables: ComparableWithDistance[] }) {
  return (
    <Panel title="Selected Comparables">
      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="border-b border-line text-xs uppercase text-slate-500">
            <tr>
              <th className="whitespace-nowrap py-2 pr-4 font-semibold">Project</th>
              <th className="whitespace-nowrap py-2 pr-4 font-semibold">Registration Month</th>
              <th className="whitespace-nowrap py-2 pr-4 font-semibold">PSF</th>
              <th className="whitespace-nowrap py-2 pr-4 font-semibold">Distance</th>
              <th className="whitespace-nowrap py-2 pr-4 font-semibold">Score</th>
              <th className="whitespace-nowrap py-2 font-semibold">Reasons</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {comparables.map((item) => (
              <tr key={item.id}>
                <td className="max-w-48 py-2 pr-4 font-medium">{item.projectName}</td>
                <td className="whitespace-nowrap py-2 pr-4 text-slate-600">{formatRegistrationMonth(item.transactionDate)}</td>
                <td className="whitespace-nowrap py-2 pr-4">{formatPsf(item.pricePsf)}</td>
                <td className="whitespace-nowrap py-2 pr-4">{formatKm(item.distanceKm)}</td>
                <td className="whitespace-nowrap py-2 pr-4">{item.relevanceScore}</td>
                <td className="min-w-56 py-2 text-slate-600">{item.relevanceReasons.join(", ")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-3 text-xs text-slate-500">
        HDB resale records publish registration month, not exact transaction day.
      </p>
    </Panel>
  );
}
