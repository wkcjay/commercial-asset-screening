import type { ReactNode } from "react";

type BadgeTone = "neutral" | "good" | "warn" | "danger";

const toneClass: Record<BadgeTone, string> = {
  neutral: "border-line bg-white text-ink",
  good: "border-emerald-200 bg-emerald-50 text-emerald-800",
  warn: "border-amber-200 bg-amber-50 text-amber-800",
  danger: "border-red-200 bg-red-50 text-red-800",
};

export function Badge({ children, tone = "neutral" }: { children: ReactNode; tone?: BadgeTone }) {
  return (
    <span className={`inline-flex min-h-6 items-center rounded border px-2 py-0.5 text-xs font-medium ${toneClass[tone]}`}>
      {children}
    </span>
  );
}
