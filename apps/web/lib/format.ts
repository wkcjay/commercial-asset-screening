export function formatNumber(value: number | null | undefined, options?: Intl.NumberFormatOptions) {
  if (value === undefined || value === null || Number.isNaN(value)) return "n/a";
  return new Intl.NumberFormat("en-SG", options).format(value);
}

export function formatMoney(value: number | null | undefined, currency = "SGD") {
  if (value === undefined || value === null) return "n/a";
  return new Intl.NumberFormat("en-SG", {
    currency,
    maximumFractionDigits: 0,
    style: "currency",
  }).format(value);
}

export function formatPsf(value: number | null | undefined, currency = "S$") {
  if (value === undefined || value === null) return "n/a";
  const prefix = currency === "SGD" ? "S$" : currency;
  return `${prefix}${formatNumber(value, { maximumFractionDigits: 0 })} psf`;
}

export function formatPercent(value: number | null | undefined) {
  if (value === undefined || value === null) return "n/a";
  return `${formatNumber(value, { maximumFractionDigits: 1 })}%`;
}

export function formatSqft(value: number | null | undefined) {
  if (value === undefined || value === null) return "n/a";
  return `${formatNumber(value, { maximumFractionDigits: 0 })} sq ft`;
}

export function formatSqm(value: number | null | undefined) {
  if (value === undefined || value === null) return "n/a";
  return `${formatNumber(value, { maximumFractionDigits: 0 })} sqm`;
}

export function formatResidentialPsf(value: number | undefined) {
  if (value === undefined) return "n/a";
  return `S$${formatNumber(value, { maximumFractionDigits: 0 })} psf`;
}

export function formatKm(value: number | undefined) {
  if (value === undefined) return "n/a";
  return `${formatNumber(value, { maximumFractionDigits: 2 })} km`;
}

export function formatRegistrationMonth(value: string | undefined) {
  if (!value) return "n/a";
  const match = value.match(/^(\d{4})-(\d{2})-\d{2}$/);
  if (!match) return value;
  const [, year, month] = match;
  const date = new Date(Number(year), Number(month) - 1, 1);
  return new Intl.DateTimeFormat("en-SG", { month: "short", year: "numeric" }).format(date);
}

export function titleCase(value: string) {
  return value
    .replaceAll("_", " ")
    .replaceAll("-", " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}
