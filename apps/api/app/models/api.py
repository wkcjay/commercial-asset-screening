from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, Field

from app.models.domain import CommercialAssetAssessment, CommercialAssetSummary, SiteAssessment, SiteSummary


T = TypeVar("T")


class CacheMeta(BaseModel):
    hit: bool
    key: str | None = None
    source: Literal["cache", "computed"]


class ApiEnvelopeMeta(BaseModel):
    requestId: str
    generatedAt: str
    dataVersion: str | None = None
    cache: CacheMeta | None = None
    warnings: list[str] = Field(default_factory=list)


class ApiEnvelope(BaseModel, Generic[T]):
    data: T
    meta: ApiEnvelopeMeta


class ErrorBody(BaseModel):
    code: Literal["not_found", "validation_error", "out_of_scope", "data_error", "ai_generation_error", "internal_error"]
    message: str
    details: object | None = None
    requestId: str


class ApiError(BaseModel):
    error: ErrorBody


class HealthResponse(BaseModel):
    ok: bool
    version: str
    dataMode: str
    aiConfigured: bool


class ListSitesData(BaseModel):
    sites: list[SiteSummary]


class ListCommercialAssetsData(BaseModel):
    assets: list[CommercialAssetSummary]


class AssessmentData(BaseModel):
    assessment: SiteAssessment


class CommercialAssetAssessmentData(BaseModel):
    assessment: CommercialAssetAssessment


class GenerateMemoRequest(BaseModel):
    tone: Literal["investment-committee", "plain-language"] = "investment-committee"


class MemoRecommendation(BaseModel):
    stance: Literal["proceed-to-further-diligence", "hold", "do-not-prioritize"]
    rationale: str
    nextDiligenceSteps: list[str]


class GeneratedMemo(BaseModel):
    executiveSummary: str
    siteContext: str
    comparableTransactionView: str
    accessibilityAndAmenities: str
    demographicContext: str
    planningContext: str
    risksAndAssumptions: str
    recommendation: MemoRecommendation
    confidenceLevel: Literal["high", "medium", "low"]
    confidenceRationale: str
    sourceUsageNote: str


class MemoGeneration(BaseModel):
    provider: Literal["openai-compatible", "fallback"]
    model: str | None = None
    promptVersion: str
    generatedAt: str
    groundingSourceIds: list[str]
    usedFallback: bool


class MemoData(BaseModel):
    memo: GeneratedMemo
    assessmentId: str
    generation: MemoGeneration
