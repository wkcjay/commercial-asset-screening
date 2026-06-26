"use client";

import { FileText, Loader2 } from "lucide-react";
import type { ApiEnvelopeMeta, MemoData } from "@/lib/types";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { CacheBadge } from "./status-badge";
import { Panel } from "./ui/panel";

export type MemoState =
  | { state: "idle" }
  | { state: "generating" }
  | { state: "ready"; data: MemoData; meta: ApiEnvelopeMeta }
  | { state: "error"; message: string };

export function MemoPanel({
  memoState,
  disabled,
  onGenerate,
}: {
  memoState: MemoState;
  disabled: boolean;
  onGenerate: () => void;
}) {
  const action =
    memoState.state === "ready" ? (
      <div className="flex gap-2">
        <CacheBadge hit={memoState.meta.cache?.hit} />
        <Badge tone={memoState.data.generation.usedFallback ? "warn" : "good"}>
          {memoState.data.generation.provider}
        </Badge>
      </div>
    ) : null;

  return (
    <Panel title="Screening Memo" action={action}>
      <Button disabled={disabled || memoState.state === "generating"} onClick={onGenerate} className="w-full">
        {memoState.state === "generating" ? (
          <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
        ) : (
          <FileText className="h-4 w-4" aria-hidden="true" />
        )}
        Generate Memo
      </Button>

      {memoState.state === "idle" ? (
        <p className="mt-4 text-sm text-slate-600">Review the assessment evidence before generating the grounded first-pass memo.</p>
      ) : null}

      {memoState.state === "error" ? <p className="mt-4 text-sm text-danger">{memoState.message}</p> : null}

      {memoState.state === "ready" ? <MemoContent data={memoState.data} /> : null}
    </Panel>
  );
}

function MemoContent({ data }: { data: MemoData }) {
  const memo = data.memo;
  const sections = [
    ["Executive summary", memo.executiveSummary],
    ["Asset context", memo.siteContext],
    ["Market evidence", memo.comparableTransactionView],
    ["Operating context", memo.accessibilityAndAmenities],
    ["Catchment context", memo.demographicContext],
    ["Planning context", memo.planningContext],
    ["Risks and assumptions", memo.risksAndAssumptions],
  ] as const;

  return (
    <div className="mt-4 space-y-4">
      {sections.map(([title, value]) => (
        <section key={title}>
          <h3 className="text-sm font-semibold">{title}</h3>
          <p className="mt-1 text-sm leading-6 text-slate-700">{value}</p>
        </section>
      ))}
      <section className="rounded border border-line bg-field p-3">
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <h3 className="text-sm font-semibold">Recommendation</h3>
          <Badge tone={memo.recommendation.stance === "proceed-to-further-diligence" ? "good" : "warn"}>
            {memo.recommendation.stance}
          </Badge>
          <Badge>{memo.confidenceLevel} confidence</Badge>
        </div>
        <p className="text-sm leading-6 text-slate-700">{memo.recommendation.rationale}</p>
        <ul className="mt-2 space-y-1 text-sm text-slate-700">
          {memo.recommendation.nextDiligenceSteps.map((step) => (
            <li key={step}>- {step}</li>
          ))}
        </ul>
      </section>
      <p className="text-xs text-slate-500">{memo.sourceUsageNote}</p>
    </div>
  );
}
