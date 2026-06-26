import json
from dataclasses import dataclass

import httpx
from sqlalchemy.engine import Engine

from app.constants import FALLBACK_MODEL, FALLBACK_PROVIDER, PROMPT_VERSION
from app.config import Settings, get_settings
from app.models.api import CacheMeta, GeneratedMemo, MemoData, MemoGeneration, MemoRecommendation
from app.models.domain import CommercialAssetAssessment, SiteAssessment
from app.services import cache


@dataclass(frozen=True)
class MemoResult:
    data: MemoData
    cache_meta: CacheMeta
    warnings: list[str]


def generate_memo(engine: Engine, assessment: SiteAssessment, tone: str, settings: Settings | None = None) -> MemoResult:
    resolved_settings = settings or get_settings()
    if _ai_enabled(resolved_settings):
        return _generate_ai_memo(engine, assessment, tone, resolved_settings)

    key = cache.memo_cache_key(assessment.assessmentId, FALLBACK_PROVIDER, FALLBACK_MODEL, tone)
    cached = cache.load_memo(engine, key)
    if cached is not None:
        return MemoResult(data=MemoData.model_validate(cached), cache_meta=cache.cache_meta(True, key), warnings=[])

    generated_at = cache.utc_now()
    memo = _fallback_memo(assessment)
    generation = MemoGeneration(
        provider="fallback",
        model=FALLBACK_MODEL,
        promptVersion=PROMPT_VERSION,
        generatedAt=generated_at,
        groundingSourceIds=sorted({source.id for source in assessment.sources}),
        usedFallback=True,
    )
    data = MemoData(memo=memo, assessmentId=assessment.assessmentId, generation=generation)
    cache.store_memo(engine, assessment.assessmentId, FALLBACK_PROVIDER, FALLBACK_MODEL, tone, key, data.model_dump(mode="json"))
    return MemoResult(
        data=data,
        cache_meta=cache.cache_meta(False, key),
        warnings=["AI provider not configured; deterministic fallback memo returned."],
    )


def generate_commercial_memo(
    engine: Engine,
    assessment: CommercialAssetAssessment,
    tone: str,
    settings: Settings | None = None,
) -> MemoResult:
    resolved_settings = settings or get_settings()
    if _ai_enabled(resolved_settings):
        return _generate_ai_memo(engine, assessment, tone, resolved_settings)

    key = cache.memo_cache_key(assessment.assessmentId, FALLBACK_PROVIDER, FALLBACK_MODEL, tone)
    cached = cache.load_memo(engine, key)
    if cached is not None:
        return MemoResult(data=MemoData.model_validate(cached), cache_meta=cache.cache_meta(True, key), warnings=[])

    generated_at = cache.utc_now()
    memo = _commercial_fallback_memo(assessment)
    generation = MemoGeneration(
        provider="fallback",
        model=FALLBACK_MODEL,
        promptVersion=PROMPT_VERSION,
        generatedAt=generated_at,
        groundingSourceIds=sorted({source.id for source in assessment.sources}),
        usedFallback=True,
    )
    data = MemoData(memo=memo, assessmentId=assessment.assessmentId, generation=generation)
    cache.store_memo(engine, assessment.assessmentId, FALLBACK_PROVIDER, FALLBACK_MODEL, tone, key, data.model_dump(mode="json"))
    return MemoResult(
        data=data,
        cache_meta=cache.cache_meta(False, key),
        warnings=["AI provider not configured; deterministic fallback memo returned."],
    )


def _ai_enabled(settings: Settings) -> bool:
    return bool(settings.enable_ai_memo and settings.ai_api_key and settings.ai_model)


def _generate_ai_memo(
    engine: Engine,
    assessment: SiteAssessment | CommercialAssetAssessment,
    tone: str,
    settings: Settings,
) -> MemoResult:
    provider = settings.ai_provider or "openai-compatible"
    model = settings.ai_model or "unknown"
    key = cache.memo_cache_key(assessment.assessmentId, provider, model, tone)
    cached = cache.load_memo(engine, key)
    if cached is not None:
        return MemoResult(data=MemoData.model_validate(cached), cache_meta=cache.cache_meta(True, key), warnings=[])

    try:
        memo = _call_openai_compatible_memo(assessment, tone, settings)
    except Exception as exc:
        fallback = _commercial_fallback_memo(assessment) if isinstance(assessment, CommercialAssetAssessment) else _fallback_memo(assessment)
        generation = MemoGeneration(
            provider="fallback",
            model=FALLBACK_MODEL,
            promptVersion=PROMPT_VERSION,
            generatedAt=cache.utc_now(),
            groundingSourceIds=sorted({source.id for source in assessment.sources}),
            usedFallback=True,
        )
        data = MemoData(memo=fallback, assessmentId=assessment.assessmentId, generation=generation)
        return MemoResult(
            data=data,
            cache_meta=cache.cache_meta(False, key),
            warnings=[f"AI memo generation failed; deterministic fallback returned. Reason: {exc}"],
        )

    generation = MemoGeneration(
        provider="openai-compatible",
        model=model,
        promptVersion=PROMPT_VERSION,
        generatedAt=cache.utc_now(),
        groundingSourceIds=sorted({source.id for source in assessment.sources}),
        usedFallback=False,
    )
    data = MemoData(memo=memo, assessmentId=assessment.assessmentId, generation=generation)
    cache.store_memo(engine, assessment.assessmentId, provider, model, tone, key, data.model_dump(mode="json"))
    return MemoResult(data=data, cache_meta=cache.cache_meta(False, key), warnings=[])


def _call_openai_compatible_memo(
    assessment: SiteAssessment | CommercialAssetAssessment,
    tone: str,
    settings: Settings,
) -> GeneratedMemo:
    content = _request_chat_completion(settings, _memo_messages(assessment, tone))
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError("AI response was not valid JSON") from exc
    return GeneratedMemo.model_validate(payload)


def _request_chat_completion(settings: Settings, messages: list[dict[str, str]]) -> str:
    base_url = (settings.ai_base_url or "https://api.openai.com/v1").rstrip("/")
    url = f"{base_url}/chat/completions"
    response = httpx.post(
        url,
        headers={
            "Authorization": f"Bearer {settings.ai_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": settings.ai_model,
            "messages": messages,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        },
        timeout=45,
    )
    response.raise_for_status()
    body = response.json()
    try:
        return body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError("AI response did not include choices[0].message.content") from exc


def _memo_messages(assessment: SiteAssessment | CommercialAssetAssessment, tone: str) -> list[dict[str, str]]:
    schema = {
        "executiveSummary": "string",
        "siteContext": "string",
        "comparableTransactionView": "string",
        "accessibilityAndAmenities": "string",
        "demographicContext": "string",
        "planningContext": "string",
        "risksAndAssumptions": "string",
        "recommendation": {
            "stance": "proceed-to-further-diligence | hold | do-not-prioritize",
            "rationale": "string",
            "nextDiligenceSteps": ["string"],
        },
        "confidenceLevel": "high | medium | low",
        "confidenceRationale": "string",
        "sourceUsageNote": "string",
    }
    return [
        {
            "role": "system",
            "content": (
                "You generate grounded real-estate screening memos. Use only the supplied JSON context. "
                "Do not invent facts, transaction amounts, dates, buyers, sellers, planning details, or source names. "
                "If evidence is missing, say it is missing and make it a diligence item. "
                "Return only valid JSON matching the requested schema."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "tone": tone,
                    "required_schema": schema,
                    "assessment": assessment.model_dump(mode="json"),
                },
                sort_keys=True,
            ),
        },
    ]


def _fallback_memo(assessment: SiteAssessment) -> GeneratedMemo:
    comp = assessment.comparableSummary
    location = assessment.locationScore
    confidence = assessment.confidence
    risk_count = len(assessment.riskAssessment.items)
    planning = assessment.planningContext
    demographic = assessment.demographicContext
    official_sources = all(source.reliability == "official" for source in assessment.sources)
    comparable_basis = "official HDB resale transactions" if official_sources else "resolved comparable transactions"
    stance = "proceed-to-further-diligence" if confidence.level != "low" else "hold"
    if assessment.riskAssessment.overallRiskLevel == "high":
        stance = "hold" if confidence.level == "low" else "proceed-to-further-diligence"

    return GeneratedMemo(
        executiveSummary=(
            f"{assessment.site.name} screens as a {location.rating} location with "
            f"{confidence.level} confidence. The assessment is based on {comp.selectedCount} selected "
            f"{comparable_basis} and visible source limitations."
        ),
        siteContext=(
            f"The site is a residential reference location in {assessment.site.planningArea}, District "
            f"{assessment.site.district}. Tenure is recorded as {assessment.site.tenure or 'unknown'}."
        ),
        comparableTransactionView=(
            f"Selected comparables show median price psf of {comp.medianPricePsf}, with a range from "
            f"{comp.minPricePsf} to {comp.maxPricePsf}. Trend is {comp.trend.label}: {comp.trend.basis}"
        ),
        accessibilityAndAmenities=(
            f"Overall location score is {location.overall}/100. Transport score is {location.transport}; "
            f"amenity score is {location.amenities}. "
            + (" ".join(assessment.amenitySummary.highlights) if assessment.amenitySummary.highlights else "Amenity evidence is limited.")
        ),
        demographicContext=(
            f"Planning-area demographic context is available for {demographic.planningArea}."
            if demographic
            else "No demographic context is available for this planning area."
        ),
        planningContext=(
            f"Indicative planning context records zoning as {planning.zoning} with gross plot ratio {planning.grossPlotRatio}. Professional verification is required."
            if planning
            else "Planning context is missing and should be verified before further investment work."
        ),
        risksAndAssumptions=(
            f"The assessment includes {risk_count} risk item(s). Key limitations include no live paid private-market transaction feed and no supply pipeline."
        ),
        recommendation=MemoRecommendation(
            stance=stance,
            rationale="Proceed only as a first-pass screening view; validate planning assumptions before investment decisions.",
            nextDiligenceSteps=[
                "Add private residential transaction evidence if the target investment is not HDB-related.",
                "Verify zoning, plot ratio, and site constraints with professional planning sources.",
                "Add supply pipeline and sales velocity evidence before committee use.",
            ],
        ),
        confidenceLevel=confidence.level,
        confidenceRationale="; ".join(confidence.deductions or confidence.drivers),
        sourceUsageNote="This fallback memo uses only the backend-computed assessment and its resolved source labels.",
    )


def _commercial_fallback_memo(assessment: CommercialAssetAssessment) -> GeneratedMemo:
    asset = assessment.asset
    metrics = assessment.metrics
    confidence = assessment.confidence
    risk_count = len(assessment.riskAssessment.items)
    valuation = metrics.latestValuation
    value_label = (
        f"{valuation.currency} {valuation.valuationAmount:,.0f}"
        if valuation
        else "no loaded reported valuation"
    )
    valuation_psf_label = (
        f"{valuation.currency} {metrics.valuationPsf:,.0f} psf"
        if valuation and metrics.valuationPsf
        else "n/a"
    )
    submarket_event = metrics.latestSameSubmarketEvent
    asset_type_label = asset.assetType.replace("-", " ")
    article = "an" if asset_type_label[0].lower() in {"a", "e", "i", "o", "u"} else "a"
    ownership_label = (
        f"{asset.ownershipInterestPercent}%"
        if asset.ownershipInterestPercent is not None
        else "not loaded"
    )
    stance = "proceed-to-further-diligence" if confidence.level != "low" else "hold"
    if assessment.riskAssessment.overallRiskLevel == "high":
        stance = "hold"

    return GeneratedMemo(
        executiveSummary=(
            f"{asset.name} screens as {article} {asset_type_label} asset in {asset.submarket} with "
            f"{confidence.level} confidence. Reported valuation is {value_label}; valuation psf is {valuation_psf_label}."
        ),
        siteContext=(
            f"{asset.issuer} reports {asset.name} at {asset.address or 'an unspecified Singapore address'}. "
            f"Ownership interest is {ownership_label}."
        ),
        comparableTransactionView=(
            f"The event set includes {metrics.sameSubmarketEventCount} same-submarket event(s) and "
            f"{metrics.sameAssetTypeEventCount} same-asset-type event(s). "
            + (
                f"Latest same-submarket event: {submarket_event.title}."
                if submarket_event
                else "No same-submarket event is loaded."
            )
        ),
        accessibilityAndAmenities=(
            f"Loaded operating context shows NLA of {metrics.nlaSqft:,.0f} sq ft and occupancy of "
            f"{metrics.occupancyPercent}%."
            if metrics.nlaSqft and metrics.occupancyPercent is not None
            else "Operating metrics are incomplete; add NLA, occupancy, WALE, and tenant concentration."
        ),
        demographicContext=(
            "Commercial catchment should be assessed with tenant demand, office or retail supply, and worker or shopper flows; "
            "the current MVP focuses on issuer valuation and transaction/event evidence."
        ),
        planningContext=(
            "Planning and title fields are limited to issuer-reported tenure and submarket tagging in this MVP."
        ),
        risksAndAssumptions=(
            f"The assessment includes {risk_count} risk item(s). Key limitations are missing private-market comps, "
            "no cap-rate bridge, and no live lease-level diligence."
        ),
        recommendation=MemoRecommendation(
            stance=stance,
            rationale="Use this as a first-pass screen; move to diligence only after validating valuation basis and event facts.",
            nextDiligenceSteps=[
                "Verify valuation basis, ownership percentage, and latest appraisal date from issuer reports.",
                "Add lease expiry, top tenant, NPI, debt, and cap-rate bridge data.",
                "Validate recent same-submarket transactions with SGX announcements or primary filings.",
            ],
        ),
        confidenceLevel=confidence.level,
        confidenceRationale="; ".join(confidence.deductions or confidence.drivers),
        sourceUsageNote="This fallback memo uses only backend-computed metrics, structured market events, and linked source labels.",
    )
