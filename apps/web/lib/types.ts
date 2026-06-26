export type CacheMeta = {
  hit: boolean;
  key?: string;
  source: "cache" | "computed";
};

export type ApiEnvelopeMeta = {
  requestId: string;
  generatedAt: string;
  dataVersion?: string;
  cache?: CacheMeta;
  warnings: string[];
};

export type ApiEnvelope<T> = {
  data: T;
  meta: ApiEnvelopeMeta;
};

export type ApiError = {
  error: {
    code:
      | "not_found"
      | "validation_error"
      | "out_of_scope"
      | "data_error"
      | "ai_generation_error"
      | "internal_error";
    message: string;
    details?: unknown;
    requestId: string;
  };
};

export type SiteSummary = {
  id: string;
  name: string;
  address: string;
  district: string;
  planningArea: string;
  assetClass: "residential";
  dataReliability: "official" | "manual" | "synthetic" | "seeded" | "sample" | "proxy";
};

export type Source = {
  id: string;
  label: string;
  publisher?: string;
  url?: string;
  retrievedAt?: string;
  dataVintage?: string;
  reliability: "official" | "paid" | "manual" | "synthetic" | "seeded" | "sample" | "proxy";
  notes?: string;
};

export type Site = {
  id: string;
  name: string;
  address: string;
  country: "SG";
  region: "Singapore";
  district: string;
  planningArea: string;
  latitude: number;
  longitude: number;
  assetClass: "residential";
  tenure?: "freehold" | "leasehold" | "unknown";
  landAreaSqm?: number;
  grossPlotRatioHint?: number;
  sourceIds: string[];
};

export type CommercialAssetSummary = {
  id: string;
  issuer: string;
  name: string;
  address?: string;
  country: "SG";
  assetType: "office" | "retail" | "mixed-use" | "hospitality" | "industrial";
  submarket: string;
  valuationAmount?: number | null;
  valuationCurrency?: string | null;
  valuationDate?: string | null;
  valuationPsf?: number | null;
  occupancyPercent?: number | null;
  dataReliability: "official" | "paid" | "manual" | "synthetic" | "seeded" | "sample" | "proxy";
};

export type CommercialAsset = {
  id: string;
  issuer: string;
  name: string;
  address?: string | null;
  country: "SG";
  assetType: "office" | "retail" | "mixed-use" | "hospitality" | "industrial";
  submarket: string;
  tenure?: string | null;
  ownershipInterestPercent?: number | null;
  grossFloorAreaSqm?: number | null;
  netLettableAreaSqm?: number | null;
  netLettableAreaSqft?: number | null;
  occupancyPercent?: number | null;
  numberOfTenants?: number | null;
  carparkLots?: number | null;
  sourceNote?: string | null;
  sourceIds: string[];
};

export type AssetValuation = {
  id: string;
  assetId: string;
  valuationAmount: number;
  currency: string;
  valuationDate: string;
  valuationScope: "asset_100_percent" | "owned_interest" | "unknown";
  valuationBasis?: string | null;
  sourceId?: string | null;
};

export type MarketEvent = {
  id: string;
  eventDate: string;
  eventType: "development" | "stake-acquisition" | "acquisition" | "divestment" | "leasing" | "other";
  title: string;
  assetName: string;
  assetType: "office" | "retail" | "mixed-use" | "hospitality" | "industrial";
  submarket: string;
  buyer?: string | null;
  seller?: string | null;
  amount?: number | null;
  currency?: string | null;
  stakePercent?: number | null;
  stakeDescription?: string | null;
  areaSqft?: number | null;
  sourceUrl?: string | null;
  sourceId?: string | null;
  counterparties: string[];
  extractionConfidence: number;
  needsReview: boolean;
  summary: string;
};

export type CommercialAssetAssessment = {
  assessmentId: string;
  generatedAt: string;
  asset: CommercialAsset;
  scope: Record<string, string>;
  metrics: {
    latestValuation?: AssetValuation | null;
    valuationPsf?: number | null;
    attributableValuation?: number | null;
    attributableValuationCurrency?: string | null;
    nlaSqft?: number | null;
    occupancyPercent?: number | null;
    latestSameSubmarketEvent?: MarketEvent | null;
    latestSameAssetTypeEvent?: MarketEvent | null;
    sameSubmarketEventCount: number;
    sameAssetTypeEventCount: number;
    missingData: string[];
  };
  marketEvents: MarketEvent[];
  riskAssessment: {
    items: RiskItem[];
    overallRiskLevel: "low" | "medium" | "high";
  };
  confidence: {
    level: "high" | "medium" | "low";
    score: number;
    drivers: string[];
    deductions: string[];
  };
  assumptions: Array<{ id: string; statement: string }>;
  limitations: Array<{ id: string; statement: string }>;
  sources: Source[];
};

export type ComparableWithDistance = {
  id: string;
  projectName: string;
  address: string;
  country: "SG";
  district: string;
  planningArea: string;
  latitude: number;
  longitude: number;
  transactionDate: string;
  propertyType: "condo" | "apartment" | "landed" | "executive-condo" | "hdb";
  tenure?: "freehold" | "leasehold" | "unknown";
  floorAreaSqm?: number;
  priceSgd: number;
  pricePsf: number;
  sourceIds: string[];
  distanceKm: number;
  recencyMonths: number;
  relevanceScore: number;
  relevanceReasons: string[];
};

export type ComparableSummary = {
  searchRadiusKm: number;
  candidateCount: number;
  selectedCount: number;
  selectedComparables: ComparableWithDistance[];
  excludedCandidateCount: number;
  medianPricePsf?: number;
  minPricePsf?: number;
  maxPricePsf?: number;
  latestTransactionDate?: string;
  trend: {
    label: "rising" | "stable" | "softening" | "insufficient-data";
    basis: string;
    earlierMedianPricePsf?: number;
    recentMedianPricePsf?: number;
    percentChange?: number;
  };
  outlierPolicy: {
    method: "none" | "iqr";
    excludedTransactionIds: string[];
    explanation: string;
  };
};

export type NearbyAmenity = {
  id: string;
  name: string;
  rawCategory?: string;
  category:
    | "mrt"
    | "bus_interchange"
    | "school"
    | "mall"
    | "park"
    | "healthcare"
    | "supermarket"
    | "employment_node"
    | "other";
  categoryConfidence?: number;
  categoryLabelSource: "rule" | "ai" | "manual";
  needsReview: boolean;
  latitude: number;
  longitude: number;
  sourceIds: string[];
  distanceKm: number;
};

export type AmenitySummary = {
  searchRadiusKm: number;
  nearestMrt?: NearbyAmenity | null;
  categoryCounts: Record<string, number>;
  nearbyAmenities: NearbyAmenity[];
  highlights: string[];
};

export type DemographicContext = {
  planningArea: string;
  population?: number;
  residentHouseholds?: number;
  medianAge?: number;
  householdIncomeBand?: string;
  notes: string[];
  sourceIds: string[];
};

export type PlanningContext = {
  planningArea: string;
  zoning?: "residential" | "commercial" | "mixed-use" | "white" | "unknown";
  grossPlotRatio?: number;
  heightControl?: string;
  masterPlanNotes: string[];
  professionalVerificationRequired: boolean;
  sourceIds: string[];
};

export type LocationScore = {
  overall: number;
  transport: number;
  amenities: number;
  catchment: number;
  planningFit: number;
  rating: "strong" | "moderate" | "weak" | "incomplete";
  explanations: string[];
  components: Array<{
    name: string;
    score: number;
    weight: number;
    explanation: string;
  }>;
};

export type RiskItem = {
  id: string;
  severity: "low" | "medium" | "high";
  category: "data" | "market" | "location" | "planning" | "execution";
  statement: string;
  evidence: string[];
  mitigation?: string;
};

export type SiteAssessment = {
  assessmentId: string;
  generatedAt: string;
  site: Site;
  scope: Record<string, string>;
  comparableSummary: ComparableSummary;
  locationScore: LocationScore;
  amenitySummary: AmenitySummary;
  demographicContext?: DemographicContext | null;
  planningContext?: PlanningContext | null;
  riskAssessment: {
    items: RiskItem[];
    overallRiskLevel: "low" | "medium" | "high";
  };
  confidence: {
    level: "high" | "medium" | "low";
    score: number;
    drivers: string[];
    deductions: string[];
  };
  assumptions: Array<{ id: string; statement: string }>;
  limitations: Array<{ id: string; statement: string }>;
  sources: Source[];
};

export type GeneratedMemo = {
  executiveSummary: string;
  siteContext: string;
  comparableTransactionView: string;
  accessibilityAndAmenities: string;
  demographicContext: string;
  planningContext: string;
  risksAndAssumptions: string;
  recommendation: {
    stance: "proceed-to-further-diligence" | "hold" | "do-not-prioritize";
    rationale: string;
    nextDiligenceSteps: string[];
  };
  confidenceLevel: "high" | "medium" | "low";
  confidenceRationale: string;
  sourceUsageNote: string;
};

export type MemoData = {
  memo: GeneratedMemo;
  assessmentId: string;
  generation: {
    provider: "openai-compatible" | "fallback";
    model?: string;
    promptVersion: string;
    generatedAt: string;
    groundingSourceIds: string[];
    usedFallback: boolean;
  };
};
