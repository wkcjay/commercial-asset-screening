"use client";

import { useEffect, useMemo, useState } from "react";
import { Building2, ExternalLink, FileSearch, Percent, RefreshCw, Server, ShieldCheck, TrendingUp } from "lucide-react";
import { generateCommercialMemo, getCommercialAssessment, listCommercialAssets } from "@/lib/api-client";
import type { ApiEnvelopeMeta, CommercialAssetAssessment, CommercialAssetSummary, MarketEvent } from "@/lib/types";
import { formatMoney, formatPercent, formatPsf, formatSqft, titleCase } from "@/lib/format";
import { MemoPanel, type MemoState } from "@/components/memo-panel";
import { SourceChips } from "@/components/source-chips";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Panel } from "@/components/ui/panel";

type ScreenState =
  | { state: "loading-assets" }
  | { state: "no-asset-selected"; assets: CommercialAssetSummary[] }
  | { state: "loading-assessment"; assets: CommercialAssetSummary[]; assetId: string }
  | { state: "assessment-ready"; assets: CommercialAssetSummary[]; assessment: CommercialAssetAssessment; meta: ApiEnvelopeMeta }
  | { state: "assessment-error"; assets: CommercialAssetSummary[]; message: string };

export default function Home() {
  const [screen, setScreen] = useState<ScreenState>({ state: "loading-assets" });
  const [selectedAssetId, setSelectedAssetId] = useState<string>("");
  const [memoState, setMemoState] = useState<MemoState>({ state: "idle" });

  useEffect(() => {
    void loadAssets();
  }, []);

  const assets = "assets" in screen ? screen.assets : [];
  const assessment = screen.state === "assessment-ready" ? screen.assessment : undefined;
  const assessmentMeta = screen.state === "assessment-ready" ? screen.meta : undefined;

  const topStatus = useMemo(() => {
    if (screen.state === "assessment-ready") return screen.meta.dataVersion || "public-source snapshot";
    if (screen.state === "loading-assets") return "loading backend";
    return "public-source snapshot";
  }, [screen]);

  async function loadAssets() {
    setScreen({ state: "loading-assets" });
    setMemoState({ state: "idle" });
    try {
      const response = await listCommercialAssets();
      const loadedAssets = response.data.assets;
      setScreen({ state: "no-asset-selected", assets: loadedAssets });
      if (loadedAssets[0]) {
        setSelectedAssetId(loadedAssets[0].id);
        await loadAssessment(loadedAssets[0].id, loadedAssets);
      }
    } catch (error) {
      setScreen({
        state: "assessment-error",
        assets: [],
        message: error instanceof Error ? error.message : "Unable to load commercial assets.",
      });
    }
  }

  async function loadAssessment(assetId: string, currentAssets = assets) {
    if (!assetId) return;
    setSelectedAssetId(assetId);
    setMemoState({ state: "idle" });
    setScreen({ state: "loading-assessment", assets: currentAssets, assetId });
    try {
      const response = await getCommercialAssessment(assetId);
      setScreen({ state: "assessment-ready", assets: currentAssets, assessment: response.data.assessment, meta: response.meta });
    } catch (error) {
      setScreen({
        state: "assessment-error",
        assets: currentAssets,
        message: error instanceof Error ? error.message : "Unable to load assessment.",
      });
    }
  }

  async function handleGenerateMemo() {
    if (!selectedAssetId) return;
    setMemoState({ state: "generating" });
    try {
      const response = await generateCommercialMemo(selectedAssetId);
      setMemoState({ state: "ready", data: response.data, meta: response.meta });
    } catch (error) {
      setMemoState({ state: "error", message: error instanceof Error ? error.message : "Unable to generate memo." });
    }
  }

  return (
    <main className="min-h-screen bg-field">
      <header className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-[1500px] flex-col gap-3 px-4 py-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase text-accent">Commercial Asset Screening</p>
            <h1 className="text-xl font-semibold">Singapore REIT Portfolio Valuation Screen</h1>
          </div>
          <div className="flex flex-wrap gap-2">
            <Badge>
              <Server className="mr-1 h-3.5 w-3.5" aria-hidden="true" />
              {topStatus}
            </Badge>
            <Badge tone="warn">fallback memo ready</Badge>
            <Badge tone="good">
              <ShieldCheck className="mr-1 h-3.5 w-3.5" aria-hidden="true" />
              backend rules canonical
            </Badge>
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-[1500px] gap-4 px-4 py-4 lg:grid-cols-[300px_minmax(0,1fr)_420px]">
        <aside className="space-y-4">
          <AssetSelector assets={assets} selectedAssetId={selectedAssetId} onSelect={(assetId) => void loadAssessment(assetId)} />
          <Button className="w-full border-line bg-white text-ink hover:bg-field" onClick={() => void loadAssets()}>
            <RefreshCw className="h-4 w-4" aria-hidden="true" />
            Refresh
          </Button>
        </aside>

        <section className="min-w-0 space-y-4">
          {screen.state === "loading-assets" || screen.state === "loading-assessment" ? <LoadingBlock /> : null}
          {screen.state === "assessment-error" ? <ErrorBlock message={screen.message} /> : null}
          {assessment && assessmentMeta ? (
            <>
              <CommercialAssessmentHeader assessment={assessment} meta={assessmentMeta} />
              <ValuationMetrics assessment={assessment} />
              <MarketEventsPanel events={assessment.marketEvents} />
              <CommercialRiskPanel assessment={assessment} />
              <SourceChips sources={assessment.sources} />
            </>
          ) : null}
        </section>

        <aside>
          <MemoPanel memoState={memoState} disabled={!assessment || screen.state === "loading-assessment"} onGenerate={handleGenerateMemo} />
        </aside>
      </div>
    </main>
  );
}

function AssetSelector({
  assets,
  selectedAssetId,
  onSelect,
}: {
  assets: CommercialAssetSummary[];
  selectedAssetId: string;
  onSelect: (assetId: string) => void;
}) {
  return (
    <Panel title="Assets">
      <div className="space-y-2">
        {assets.map((asset) => {
          const selected = asset.id === selectedAssetId;
          return (
            <button
              key={asset.id}
              className={`w-full rounded-md border p-3 text-left transition ${
                selected ? "border-accent bg-accent/10" : "border-line bg-white hover:border-accent/50"
              }`}
              onClick={() => onSelect(asset.id)}
              type="button"
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="text-sm font-semibold text-ink">{asset.name}</p>
                  <p className="mt-1 text-xs text-slate-500">{asset.issuer}</p>
                </div>
                <Badge tone={asset.dataReliability === "official" ? "good" : "warn"}>{asset.dataReliability}</Badge>
              </div>
              <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-600">
                <span>{titleCase(asset.assetType)}</span>
                <span>{asset.submarket}</span>
              </div>
              <p className="mt-2 text-xs text-slate-500">{formatMoney(asset.valuationAmount, asset.valuationCurrency || "SGD")}</p>
            </button>
          );
        })}
      </div>
    </Panel>
  );
}

function CommercialAssessmentHeader({
  assessment,
  meta,
}: {
  assessment: CommercialAssetAssessment;
  meta: ApiEnvelopeMeta;
}) {
  const asset = assessment.asset;
  return (
    <Panel
      title="Asset Snapshot"
      action={
        <div className="flex gap-2">
          <Badge tone={assessment.confidence.level === "high" ? "good" : "warn"}>{assessment.confidence.level} confidence</Badge>
          <Badge>{meta.cache?.hit ? "cache hit" : "computed"}</Badge>
        </div>
      }
    >
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_260px]">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <Building2 className="h-5 w-5 text-accent" aria-hidden="true" />
            <h2 className="text-lg font-semibold">{asset.name}</h2>
            <Badge>{asset.issuer}</Badge>
          </div>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            {asset.address || "Address not loaded"} · {asset.submarket} · {titleCase(asset.assetType)}
          </p>
          <div className="mt-4 grid gap-3 text-sm sm:grid-cols-3">
            <Fact label="Ownership" value={formatPercent(asset.ownershipInterestPercent)} />
            <Fact label="NLA" value={formatSqft(assessment.metrics.nlaSqft)} />
            <Fact label="Occupancy" value={formatPercent(asset.occupancyPercent)} />
          </div>
        </div>
        <div className="rounded-md border border-line bg-field p-3">
          <p className="text-xs font-semibold uppercase text-slate-500">Confidence Score</p>
          <p className="mt-2 text-3xl font-semibold">{assessment.confidence.score}</p>
          <div className="mt-3 space-y-1 text-xs text-slate-600">
            {(assessment.confidence.deductions.length ? assessment.confidence.deductions : assessment.confidence.drivers).slice(0, 3).map((item) => (
              <p key={item}>{item}</p>
            ))}
          </div>
        </div>
      </div>
    </Panel>
  );
}

function ValuationMetrics({ assessment }: { assessment: CommercialAssetAssessment }) {
  const metrics = assessment.metrics;
  const valuation = metrics.latestValuation;
  const currency = valuation?.currency || "SGD";
  const metricItems = [
    {
      icon: <TrendingUp className="h-4 w-4" aria-hidden="true" />,
      label: "Reported valuation",
      value: formatMoney(valuation?.valuationAmount, currency),
      detail: valuation ? formatDate(valuation.valuationDate) : "not loaded",
    },
    {
      icon: <FileSearch className="h-4 w-4" aria-hidden="true" />,
      label: "Attributable value",
      value: formatMoney(metrics.attributableValuation, metrics.attributableValuationCurrency || currency),
      detail: valuation?.valuationScope ? titleCase(valuation.valuationScope) : "not loaded",
    },
    {
      icon: <Percent className="h-4 w-4" aria-hidden="true" />,
      label: "Valuation psf",
      value: formatPsf(metrics.valuationPsf, currency),
      detail: metrics.nlaSqft ? `${formatSqft(metrics.nlaSqft)} basis` : "NLA missing",
    },
    {
      icon: <Building2 className="h-4 w-4" aria-hidden="true" />,
      label: "Same-submarket events",
      value: `${metrics.sameSubmarketEventCount}`,
      detail: metrics.latestSameSubmarketEvent?.title || "not loaded",
    },
  ];

  return (
    <Panel title="Valuation Metrics">
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {metricItems.map((item) => (
          <div key={item.label} className="rounded-md border border-line bg-white p-3">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase text-slate-500">
              {item.icon}
              {item.label}
            </div>
            <p className="mt-2 text-lg font-semibold text-ink">{item.value}</p>
            <p className="mt-1 line-clamp-2 text-xs leading-5 text-slate-500">{item.detail}</p>
          </div>
        ))}
      </div>
      {metrics.missingData.length ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {metrics.missingData.map((item) => (
            <Badge key={item} tone="warn">
              missing {item}
            </Badge>
          ))}
        </div>
      ) : null}
    </Panel>
  );
}

function MarketEventsPanel({ events }: { events: MarketEvent[] }) {
  return (
    <Panel title="Market Events">
      <div className="overflow-hidden rounded-md border border-line">
        <table className="w-full text-left text-sm">
          <thead className="bg-field text-xs uppercase text-slate-500">
            <tr>
              <th className="px-3 py-2 font-semibold">Date</th>
              <th className="px-3 py-2 font-semibold">Event</th>
              <th className="px-3 py-2 font-semibold">Parties</th>
              <th className="px-3 py-2 font-semibold">Amount</th>
              <th className="px-3 py-2 font-semibold">Stake</th>
              <th className="px-3 py-2 font-semibold">Source</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line bg-white">
            {events.map((event) => (
              <tr key={event.id}>
                <td className="whitespace-nowrap px-3 py-3 text-slate-600">{formatDate(event.eventDate)}</td>
                <td className="px-3 py-3">
                  <p className="font-medium text-ink">{event.title}</p>
                  <p className="mt-1 text-xs text-slate-500">
                    {event.submarket} · {titleCase(event.assetType)} · {titleCase(event.eventType)}
                  </p>
                </td>
                <td className="px-3 py-3 text-slate-600">
                  <p>{event.buyer || "n/a"}</p>
                  {event.seller ? <p className="mt-1 text-xs text-slate-500">Seller: {event.seller}</p> : null}
                </td>
                <td className="whitespace-nowrap px-3 py-3 text-slate-600">{formatMoney(event.amount, event.currency || "SGD")}</td>
                <td className="px-3 py-3 text-slate-600">
                  <p>{formatPercent(event.stakePercent)}</p>
                  {event.needsReview ? <Badge tone="warn">review</Badge> : null}
                </td>
                <td className="px-3 py-3">
                  {event.sourceUrl ? (
                    <a className="inline-flex items-center gap-1 text-accent" href={event.sourceUrl} target="_blank" rel="noreferrer">
                      Link
                      <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
                    </a>
                  ) : (
                    <span className="text-slate-500">n/a</span>
                  )}
                </td>
              </tr>
            ))}
            {!events.length ? (
              <tr>
                <td className="px-3 py-6 text-sm text-slate-500" colSpan={6}>
                  No market events loaded.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}

function CommercialRiskPanel({ assessment }: { assessment: CommercialAssetAssessment }) {
  return (
    <div className="grid gap-4 xl:grid-cols-2">
      <Panel
        title="Risks"
        action={
          <Badge tone={assessment.riskAssessment.overallRiskLevel === "high" ? "danger" : assessment.riskAssessment.overallRiskLevel === "medium" ? "warn" : "good"}>
            {assessment.riskAssessment.overallRiskLevel}
          </Badge>
        }
      >
        <div className="space-y-3">
          {assessment.riskAssessment.items.map((risk) => (
            <div key={risk.id} className="rounded-md border border-line p-3">
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone={risk.severity === "high" ? "danger" : risk.severity === "medium" ? "warn" : "good"}>{risk.severity}</Badge>
                <Badge>{risk.category}</Badge>
              </div>
              <p className="mt-2 text-sm font-medium">{risk.statement}</p>
              {risk.mitigation ? <p className="mt-1 text-sm leading-6 text-slate-600">{risk.mitigation}</p> : null}
            </div>
          ))}
        </div>
      </Panel>
      <Panel title="Assumptions & Limits">
        <div className="space-y-4">
          <section>
            <h3 className="text-sm font-semibold">Assumptions</h3>
            <ul className="mt-2 space-y-2 text-sm leading-6 text-slate-600">
              {assessment.assumptions.map((item) => (
                <li key={item.id}>- {item.statement}</li>
              ))}
            </ul>
          </section>
          <section>
            <h3 className="text-sm font-semibold">Limitations</h3>
            <ul className="mt-2 space-y-2 text-sm leading-6 text-slate-600">
              {assessment.limitations.map((item) => (
                <li key={item.id}>- {item.statement}</li>
              ))}
            </ul>
          </section>
        </div>
      </Panel>
    </div>
  );
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs font-semibold uppercase text-slate-500">{label}</p>
      <p className="mt-1 font-medium">{value}</p>
    </div>
  );
}

function LoadingBlock() {
  return (
    <div className="rounded-md border border-line bg-white p-6 text-sm text-slate-600 shadow-panel">
      Loading commercial assessment data...
    </div>
  );
}

function ErrorBlock({ message }: { message: string }) {
  return (
    <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-800">
      {message}
    </div>
  );
}

function formatDate(value: string | undefined | null) {
  if (!value) return "n/a";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("en-SG", { day: "2-digit", month: "short", year: "numeric" }).format(date);
}
