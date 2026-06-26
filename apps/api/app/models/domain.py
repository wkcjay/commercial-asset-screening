from typing import Literal

from pydantic import BaseModel, Field


class Source(BaseModel):
    id: str
    label: str
    publisher: str | None = None
    url: str | None = None
    retrievedAt: str | None = None
    dataVintage: str | None = None
    reliability: Literal["official", "paid", "manual", "synthetic", "seeded", "sample", "proxy"]
    notes: str | None = None


class SiteSummary(BaseModel):
    id: str
    name: str
    address: str
    district: str
    planningArea: str
    assetClass: Literal["residential"]
    dataReliability: Literal["official", "manual", "synthetic", "seeded", "sample", "proxy"]


class Site(BaseModel):
    id: str
    name: str
    address: str
    country: Literal["SG"]
    region: Literal["Singapore"] = "Singapore"
    district: str
    planningArea: str
    latitude: float
    longitude: float
    assetClass: Literal["residential"]
    tenure: Literal["freehold", "leasehold", "unknown"] | None = None
    landAreaSqm: float | None = None
    grossPlotRatioHint: float | None = None
    sourceIds: list[str] = Field(default_factory=list)


class CommercialAssetSummary(BaseModel):
    id: str
    issuer: str
    name: str
    address: str | None = None
    country: Literal["SG"]
    assetType: Literal["office", "retail", "mixed-use", "hospitality", "industrial"]
    submarket: str
    valuationAmount: float | None = None
    valuationCurrency: str | None = None
    valuationDate: str | None = None
    valuationPsf: float | None = None
    occupancyPercent: float | None = None
    dataReliability: Literal["official", "paid", "manual", "synthetic", "seeded", "sample", "proxy"]


class CommercialAsset(BaseModel):
    id: str
    issuer: str
    name: str
    address: str | None = None
    country: Literal["SG"]
    assetType: Literal["office", "retail", "mixed-use", "hospitality", "industrial"]
    submarket: str
    tenure: str | None = None
    ownershipInterestPercent: float | None = None
    grossFloorAreaSqm: float | None = None
    netLettableAreaSqm: float | None = None
    netLettableAreaSqft: float | None = None
    occupancyPercent: float | None = None
    numberOfTenants: int | None = None
    carparkLots: int | None = None
    sourceNote: str | None = None
    sourceIds: list[str] = Field(default_factory=list)


class AssetValuation(BaseModel):
    id: str
    assetId: str
    valuationAmount: float
    currency: str
    valuationDate: str
    valuationScope: Literal["asset_100_percent", "owned_interest", "unknown"]
    valuationBasis: str | None = None
    sourceId: str | None = None


class MarketEvent(BaseModel):
    id: str
    eventDate: str
    eventType: Literal["development", "stake-acquisition", "acquisition", "divestment", "leasing", "other"]
    title: str
    assetName: str
    assetType: Literal["office", "retail", "mixed-use", "hospitality", "industrial"]
    submarket: str
    buyer: str | None = None
    seller: str | None = None
    amount: float | None = None
    currency: str | None = None
    stakePercent: float | None = None
    stakeDescription: str | None = None
    areaSqft: float | None = None
    sourceUrl: str | None = None
    sourceId: str | None = None
    counterparties: list[str] = Field(default_factory=list)
    extractionConfidence: float
    needsReview: bool
    summary: str


class CommercialAssetMetrics(BaseModel):
    latestValuation: AssetValuation | None = None
    valuationPsf: float | None = None
    attributableValuation: float | None = None
    attributableValuationCurrency: str | None = None
    nlaSqft: float | None = None
    occupancyPercent: float | None = None
    latestSameSubmarketEvent: MarketEvent | None = None
    latestSameAssetTypeEvent: MarketEvent | None = None
    sameSubmarketEventCount: int
    sameAssetTypeEventCount: int
    missingData: list[str]


class ComparableTransaction(BaseModel):
    id: str
    projectName: str
    address: str
    country: Literal["SG"]
    district: str
    planningArea: str
    latitude: float
    longitude: float
    transactionDate: str
    propertyType: Literal["condo", "apartment", "landed", "executive-condo", "hdb"]
    tenure: Literal["freehold", "leasehold", "unknown"] | None = None
    floorAreaSqm: float | None = None
    priceSgd: int
    pricePsf: float
    sourceIds: list[str] = Field(default_factory=list)


class ComparableWithDistance(ComparableTransaction):
    distanceKm: float
    recencyMonths: int
    relevanceScore: float
    relevanceReasons: list[str]


class Trend(BaseModel):
    label: Literal["rising", "stable", "softening", "insufficient-data"]
    basis: str
    earlierMedianPricePsf: float | None = None
    recentMedianPricePsf: float | None = None
    percentChange: float | None = None


class OutlierPolicy(BaseModel):
    method: Literal["none", "iqr"]
    excludedTransactionIds: list[str]
    explanation: str


class ComparableSummary(BaseModel):
    searchRadiusKm: float
    candidateCount: int
    selectedCount: int
    selectedComparables: list[ComparableWithDistance]
    excludedCandidateCount: int
    medianPricePsf: float | None = None
    minPricePsf: float | None = None
    maxPricePsf: float | None = None
    latestTransactionDate: str | None = None
    trend: Trend
    outlierPolicy: OutlierPolicy


class Amenity(BaseModel):
    id: str
    name: str
    rawCategory: str | None = None
    category: Literal[
        "mrt",
        "bus_interchange",
        "school",
        "mall",
        "park",
        "healthcare",
        "supermarket",
        "employment_node",
        "other",
    ]
    categoryConfidence: float | None = None
    categoryLabelSource: Literal["rule", "ai", "manual"]
    needsReview: bool
    latitude: float
    longitude: float
    sourceIds: list[str] = Field(default_factory=list)


class NearbyAmenity(Amenity):
    distanceKm: float


class AmenitySummary(BaseModel):
    searchRadiusKm: float
    nearestMrt: NearbyAmenity | None = None
    categoryCounts: dict[str, int]
    nearbyAmenities: list[NearbyAmenity]
    highlights: list[str]


class DemographicContext(BaseModel):
    planningArea: str
    population: int | None = None
    residentHouseholds: int | None = None
    medianAge: float | None = None
    householdIncomeBand: str | None = None
    notes: list[str]
    sourceIds: list[str] = Field(default_factory=list)


class PlanningContext(BaseModel):
    planningArea: str
    zoning: Literal["residential", "commercial", "mixed-use", "white", "unknown"] | None = None
    grossPlotRatio: float | None = None
    heightControl: str | None = None
    masterPlanNotes: list[str]
    professionalVerificationRequired: bool
    sourceIds: list[str] = Field(default_factory=list)


class LocationScoreComponent(BaseModel):
    name: str
    score: float
    weight: float
    explanation: str


class LocationScore(BaseModel):
    overall: float
    transport: float
    amenities: float
    catchment: float
    planningFit: float
    rating: Literal["strong", "moderate", "weak", "incomplete"]
    explanations: list[str]
    components: list[LocationScoreComponent]


class RiskItem(BaseModel):
    id: str
    severity: Literal["low", "medium", "high"]
    category: Literal["data", "market", "location", "planning", "execution"]
    statement: str
    evidence: list[str]
    mitigation: str | None = None


class RiskAssessment(BaseModel):
    items: list[RiskItem]
    overallRiskLevel: Literal["low", "medium", "high"]


class Assumption(BaseModel):
    id: str
    statement: str


class Limitation(BaseModel):
    id: str
    statement: str


class ConfidenceAssessment(BaseModel):
    level: Literal["high", "medium", "low"]
    score: int
    drivers: list[str]
    deductions: list[str]


class SiteAssessment(BaseModel):
    assessmentId: str
    generatedAt: str
    site: Site
    scope: dict[str, str]
    comparableSummary: ComparableSummary
    locationScore: LocationScore
    amenitySummary: AmenitySummary
    demographicContext: DemographicContext | None = None
    planningContext: PlanningContext | None = None
    riskAssessment: RiskAssessment
    confidence: ConfidenceAssessment
    assumptions: list[Assumption]
    limitations: list[Limitation]
    sources: list[Source]


class CommercialAssetAssessment(BaseModel):
    assessmentId: str
    generatedAt: str
    asset: CommercialAsset
    scope: dict[str, str]
    metrics: CommercialAssetMetrics
    marketEvents: list[MarketEvent]
    riskAssessment: RiskAssessment
    confidence: ConfidenceAssessment
    assumptions: list[Assumption]
    limitations: list[Limitation]
    sources: list[Source]
