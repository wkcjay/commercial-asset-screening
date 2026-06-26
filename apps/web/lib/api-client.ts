import type {
  ApiEnvelope,
  ApiError,
  CommercialAssetAssessment,
  CommercialAssetSummary,
  MemoData,
  SiteAssessment,
  SiteSummary,
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<ApiEnvelope<T>> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    cache: "no-store",
  });

  const body = (await response.json()) as ApiEnvelope<T> | ApiError;
  if (!response.ok) {
    const error = body as ApiError;
    throw new Error(error.error?.message || `Request failed with ${response.status}`);
  }
  return body as ApiEnvelope<T>;
}

export async function listSites() {
  return request<{ sites: SiteSummary[] }>("/sites");
}

export async function listCommercialAssets() {
  return request<{ assets: CommercialAssetSummary[] }>("/commercial-assets");
}

export async function getAssessment(siteId: string) {
  return request<{ assessment: SiteAssessment }>(`/sites/${siteId}/assessment`);
}

export async function getCommercialAssessment(assetId: string) {
  return request<{ assessment: CommercialAssetAssessment }>(`/commercial-assets/${assetId}/assessment`);
}

export async function generateMemo(siteId: string, tone: "investment-committee" | "plain-language" = "investment-committee") {
  return request<MemoData>(`/sites/${siteId}/memo`, {
    method: "POST",
    body: JSON.stringify({ tone }),
  });
}

export async function generateCommercialMemo(
  assetId: string,
  tone: "investment-committee" | "plain-language" = "investment-committee",
) {
  return request<MemoData>(`/commercial-assets/${assetId}/memo`, {
    method: "POST",
    body: JSON.stringify({ tone }),
  });
}
