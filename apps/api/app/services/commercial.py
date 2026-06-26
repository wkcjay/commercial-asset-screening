from dataclasses import dataclass

from sqlalchemy.engine import Engine

from app.db import repositories
from app.models.api import CacheMeta
from app.models.domain import (
    AssetValuation,
    Assumption,
    CommercialAsset,
    CommercialAssetAssessment,
    CommercialAssetMetrics,
    CommercialAssetSummary,
    ConfidenceAssessment,
    Limitation,
    MarketEvent,
    RiskAssessment,
    RiskItem,
    Source,
)
from app.services import cache


SQM_TO_SQFT = 10.7639


class CommercialAssetNotFoundError(Exception):
    pass


@dataclass(frozen=True)
class CommercialAssessmentResult:
    assessment: CommercialAssetAssessment
    data_version: str
    cache_meta: CacheMeta
    warnings: list[str]


def list_commercial_asset_summaries(engine: Engine) -> list[CommercialAssetSummary]:
    summaries: list[CommercialAssetSummary] = []
    for row in repositories.list_commercial_assets(engine):
        valuation_rows = repositories.list_asset_valuations(engine, row["id"])
        latest_valuation = _latest_valuation(valuation_rows)
        source_ids = set(repositories.get_source_ids(engine, "commercial_asset", row["id"]))
        if latest_valuation and latest_valuation.sourceId:
            source_ids.add(latest_valuation.sourceId)
        source_rows = repositories.list_sources(engine, source_ids)
        reliability = _dominant_reliability(source_rows)
        summaries.append(
            CommercialAssetSummary(
                id=row["id"],
                issuer=row["issuer"],
                name=row["name"],
                address=row.get("address"),
                country=row["country"],
                assetType=row["asset_type"],
                submarket=row["submarket"],
                valuationAmount=latest_valuation.valuationAmount if latest_valuation else None,
                valuationCurrency=latest_valuation.currency if latest_valuation else None,
                valuationDate=latest_valuation.valuationDate if latest_valuation else None,
                valuationPsf=_valuation_psf(latest_valuation, _nla_sqft(row)),
                occupancyPercent=row.get("occupancy_percent"),
                dataReliability=reliability,
            )
        )
    return summaries


def assess_commercial_asset(engine: Engine, asset_id: str) -> CommercialAssessmentResult:
    data_version = repositories.get_current_data_version(engine)
    key = cache.commercial_assessment_cache_key(asset_id, data_version)
    cached = cache.load_assessment(engine, key)
    if cached is not None:
        return CommercialAssessmentResult(
            assessment=CommercialAssetAssessment.model_validate(cached),
            data_version=data_version,
            cache_meta=cache.cache_meta(True, key),
            warnings=[],
        )

    asset_row = repositories.get_commercial_asset(engine, asset_id)
    if asset_row is None:
        raise CommercialAssetNotFoundError(f"Unknown commercial asset: {asset_id}")

    asset = _asset_from_row(engine, asset_row)
    valuation_rows = repositories.list_asset_valuations(engine, asset_id)
    valuations = [_valuation_from_row(row) for row in valuation_rows]
    latest_valuation = valuations[0] if valuations else None
    all_events = [_market_event_from_row(row) for row in repositories.list_market_events(engine)]
    relevant_events = _relevant_events(asset, all_events)
    metrics = _metrics(asset, latest_valuation, relevant_events)
    sources = _sources_for_assessment(engine, asset, valuations, relevant_events)
    risk_assessment = _risk_assessment(asset, metrics, relevant_events)
    confidence = _confidence(asset, metrics, relevant_events, sources)
    assumptions = _assumptions()
    limitations = _limitations(asset, metrics)
    warnings = [item.statement for item in limitations if "missing" in item.statement.lower()]

    assessment = CommercialAssetAssessment(
        assessmentId=f"casmt-{key[:16]}",
        generatedAt=cache.utc_now(),
        asset=asset,
        scope={
            "market": "Singapore",
            "assetClass": "commercial",
            "mode": "issuer-portfolio-and-market-events",
        },
        metrics=metrics,
        marketEvents=relevant_events[:8],
        riskAssessment=risk_assessment,
        confidence=confidence,
        assumptions=assumptions,
        limitations=limitations,
        sources=sources,
    )
    cache.store_assessment(engine, asset_id, data_version, key, assessment.model_dump(mode="json"))
    return CommercialAssessmentResult(
        assessment=assessment,
        data_version=data_version,
        cache_meta=cache.cache_meta(False, key),
        warnings=warnings,
    )


def _asset_from_row(engine: Engine, row: dict) -> CommercialAsset:
    return CommercialAsset(
        id=row["id"],
        issuer=row["issuer"],
        name=row["name"],
        address=row.get("address"),
        country=row["country"],
        assetType=row["asset_type"],
        submarket=row["submarket"],
        tenure=row.get("tenure"),
        ownershipInterestPercent=row.get("ownership_interest_percent"),
        grossFloorAreaSqm=row.get("gross_floor_area_sqm"),
        netLettableAreaSqm=row.get("net_lettable_area_sqm"),
        netLettableAreaSqft=_nla_sqft(row),
        occupancyPercent=row.get("occupancy_percent"),
        numberOfTenants=row.get("number_of_tenants"),
        carparkLots=row.get("carpark_lots"),
        sourceNote=row.get("source_note"),
        sourceIds=repositories.get_source_ids(engine, "commercial_asset", row["id"]),
    )


def _valuation_from_row(row: dict) -> AssetValuation:
    return AssetValuation(
        id=row["id"],
        assetId=row["asset_id"],
        valuationAmount=row["valuation_amount"],
        currency=row["currency"],
        valuationDate=row["valuation_date"],
        valuationScope=row["valuation_scope"],
        valuationBasis=row.get("valuation_basis"),
        sourceId=row.get("source_id"),
    )


def _market_event_from_row(row: dict) -> MarketEvent:
    return MarketEvent(
        id=row["id"],
        eventDate=row["event_date"],
        eventType=row["event_type"],
        title=row["title"],
        assetName=row["asset_name"],
        assetType=row["asset_type"],
        submarket=row["submarket"],
        buyer=row.get("buyer"),
        seller=row.get("seller"),
        amount=row.get("amount"),
        currency=row.get("currency"),
        stakePercent=row.get("stake_percent"),
        stakeDescription=row.get("stake_description"),
        areaSqft=row.get("area_sqft"),
        sourceUrl=row.get("source_url"),
        sourceId=row.get("source_id"),
        counterparties=row.get("counterparties", []),
        extractionConfidence=row["extraction_confidence"],
        needsReview=row["needs_review"],
        summary=row["summary"],
    )


def _source_from_row(row: dict) -> Source:
    return Source(
        id=row["id"],
        label=row["label"],
        publisher=row.get("publisher"),
        url=row.get("url"),
        retrievedAt=row.get("retrieved_at"),
        dataVintage=row.get("data_vintage"),
        reliability=row["reliability"],
        notes=row.get("notes"),
    )


def _latest_valuation(rows: list[dict]) -> AssetValuation | None:
    if not rows:
        return None
    return _valuation_from_row(rows[0])


def _nla_sqft(row: dict) -> float | None:
    if row.get("net_lettable_area_sqft") is not None:
        return row["net_lettable_area_sqft"]
    if row.get("net_lettable_area_sqm") is not None:
        return round(row["net_lettable_area_sqm"] * SQM_TO_SQFT, 1)
    return None


def _valuation_psf(valuation: AssetValuation | None, nla_sqft: float | None) -> float | None:
    if valuation is None or nla_sqft is None or nla_sqft <= 0:
        return None
    return round(valuation.valuationAmount / nla_sqft, 2)


def _attributable_valuation(asset: CommercialAsset, valuation: AssetValuation | None) -> float | None:
    if valuation is None:
        return None
    if valuation.valuationScope == "owned_interest":
        return valuation.valuationAmount
    if valuation.valuationScope == "asset_100_percent" and asset.ownershipInterestPercent is not None:
        return round(valuation.valuationAmount * asset.ownershipInterestPercent / 100, 2)
    return None


def _relevant_events(asset: CommercialAsset, events: list[MarketEvent]) -> list[MarketEvent]:
    asset_name = asset.name.lower()
    relevant = [
        event
        for event in events
        if event.submarket == asset.submarket
        or event.assetType == asset.assetType
        or asset_name in event.assetName.lower()
        or event.assetName.lower() in asset_name
    ]
    return sorted(relevant, key=lambda event: event.eventDate, reverse=True)


def _metrics(
    asset: CommercialAsset,
    latest_valuation: AssetValuation | None,
    events: list[MarketEvent],
) -> CommercialAssetMetrics:
    same_submarket_events = [event for event in events if event.submarket == asset.submarket]
    same_asset_type_events = [event for event in events if event.assetType == asset.assetType]
    missing_data = []
    if latest_valuation is None:
        missing_data.append("reported valuation")
    if asset.netLettableAreaSqft is None:
        missing_data.append("net lettable area")
    if asset.occupancyPercent is None:
        missing_data.append("occupancy")
    if not same_submarket_events:
        missing_data.append("same-submarket market events")

    return CommercialAssetMetrics(
        latestValuation=latest_valuation,
        valuationPsf=_valuation_psf(latest_valuation, asset.netLettableAreaSqft),
        attributableValuation=_attributable_valuation(asset, latest_valuation),
        attributableValuationCurrency=latest_valuation.currency if latest_valuation else None,
        nlaSqft=asset.netLettableAreaSqft,
        occupancyPercent=asset.occupancyPercent,
        latestSameSubmarketEvent=same_submarket_events[0] if same_submarket_events else None,
        latestSameAssetTypeEvent=same_asset_type_events[0] if same_asset_type_events else None,
        sameSubmarketEventCount=len(same_submarket_events),
        sameAssetTypeEventCount=len(same_asset_type_events),
        missingData=missing_data,
    )


def _sources_for_assessment(
    engine: Engine,
    asset: CommercialAsset,
    valuations: list[AssetValuation],
    events: list[MarketEvent],
) -> list[Source]:
    source_ids = set(asset.sourceIds)
    for valuation in valuations:
        if valuation.sourceId:
            source_ids.add(valuation.sourceId)
        source_ids.update(repositories.get_source_ids(engine, "asset_valuation", valuation.id))
    for event in events:
        if event.sourceId:
            source_ids.add(event.sourceId)
        source_ids.update(repositories.get_source_ids(engine, "market_event", event.id))
    return [_source_from_row(row) for row in repositories.list_sources(engine, source_ids)]


def _risk_assessment(
    asset: CommercialAsset,
    metrics: CommercialAssetMetrics,
    events: list[MarketEvent],
) -> RiskAssessment:
    items: list[RiskItem] = []
    if metrics.latestValuation is None:
        items.append(
            RiskItem(
                id="commercial-risk-missing-valuation",
                severity="high",
                category="data",
                statement="No reported asset valuation is loaded for this asset.",
                evidence=["Latest valuation field is empty."],
                mitigation="Extract the latest issuer portfolio valuation or appraisal table before relying on the screen.",
            )
        )
    if asset.occupancyPercent is None:
        items.append(
            RiskItem(
                id="commercial-risk-missing-occupancy",
                severity="medium",
                category="data",
                statement="Occupancy is missing, so income resilience cannot be screened.",
                evidence=["Occupancy percent is not available in the loaded snapshot."],
                mitigation="Add issuer occupancy, WALE, and tenant concentration fields.",
            )
        )
    if metrics.sameSubmarketEventCount == 0:
        items.append(
            RiskItem(
                id="commercial-risk-no-submarket-event",
                severity="medium",
                category="market",
                statement=f"No recent market event is loaded for {asset.submarket}.",
                evidence=["No matching submarket event in the local event table."],
                mitigation="Add SGX announcements and recent press-reported commercial transactions for this submarket.",
            )
        )
    if any(event.needsReview for event in events):
        items.append(
            RiskItem(
                id="commercial-risk-event-review",
                severity="medium",
                category="data",
                statement="One or more market events are structured from narrative sources and need analyst review.",
                evidence=[event.title for event in events if event.needsReview][:3],
                mitigation="Keep source links attached and verify buyer, seller, consideration, and stake before committee use.",
            )
        )
    if asset.ownershipInterestPercent is not None and asset.ownershipInterestPercent < 100:
        items.append(
            RiskItem(
                id="commercial-risk-partial-interest",
                severity="low",
                category="data",
                statement="The asset is held through a partial interest, so gross and attributable values differ.",
                evidence=[f"Ownership interest loaded as {asset.ownershipInterestPercent}%."],
                mitigation="Confirm whether valuation is 100% asset value or interest-level value before NAV bridge work.",
            )
        )
    if not items:
        items.append(
            RiskItem(
                id="commercial-risk-source-depth",
                severity="low",
                category="market",
                statement="This is a first-pass screening view and excludes full lease, debt, and cap-rate underwriting.",
                evidence=["Loaded evidence covers issuer portfolio facts and selected market events only."],
                mitigation="Add lease expiry, NPI, debt, and appraiser assumptions for investment committee use.",
            )
        )
    severities = {item.severity for item in items}
    overall = "high" if "high" in severities else "medium" if "medium" in severities else "low"
    return RiskAssessment(items=items, overallRiskLevel=overall)


def _confidence(
    asset: CommercialAsset,
    metrics: CommercialAssetMetrics,
    events: list[MarketEvent],
    sources: list[Source],
) -> ConfidenceAssessment:
    score = 100
    drivers = []
    deductions = []
    if metrics.latestValuation is None:
        score -= 25
        deductions.append("No reported valuation is loaded.")
    else:
        drivers.append("Reported issuer valuation is available.")
    if asset.netLettableAreaSqft is None:
        score -= 15
        deductions.append("Net lettable area is missing.")
    else:
        drivers.append("Net lettable area is available for valuation psf.")
    if asset.occupancyPercent is None:
        score -= 10
        deductions.append("Occupancy is missing.")
    if metrics.sameSubmarketEventCount == 0:
        score -= 10
        deductions.append("No same-submarket market event is loaded.")
    else:
        drivers.append("At least one same-submarket market event is available.")
    if any(source.reliability == "paid" for source in sources):
        score -= 5
        deductions.append("Some market events come from press sources and require verification.")
    if any(event.needsReview for event in events):
        score -= 5
        deductions.append("One or more structured event fields need analyst review.")
    score = max(0, min(100, score))
    level = "high" if score >= 80 else "medium" if score >= 60 else "low"
    return ConfidenceAssessment(level=level, score=score, drivers=drivers, deductions=deductions)


def _assumptions() -> list[Assumption]:
    return [
        Assumption(id="commercial-assumption-reported-values", statement="Issuer-reported valuations are used as stated and are not independently appraised by the application."),
        Assumption(id="commercial-assumption-source-snapshot", statement="The local dataset is a curated public-source snapshot loaded at database initialization time."),
        Assumption(id="commercial-assumption-event-facts", statement="Market-event extraction stores structured facts and source links, not full copyrighted article text."),
    ]


def _limitations(asset: CommercialAsset, metrics: CommercialAssetMetrics) -> list[Limitation]:
    limitations = [
        Limitation(id="commercial-limitation-no-cap-rate", statement="Cap rate and NAV discount analysis are not calculated until NPI, debt, and issuer unit-level data are loaded."),
        Limitation(id="commercial-limitation-private-market", statement="Private broker comps and paid transaction databases are outside the current local dataset."),
    ]
    if metrics.missingData:
        limitations.append(
            Limitation(
                id="commercial-limitation-missing-fields",
                statement=f"The current asset snapshot is missing: {', '.join(metrics.missingData)}.",
            )
        )
    if asset.sourceNote:
        limitations.append(Limitation(id="commercial-limitation-source-note", statement=asset.sourceNote))
    return limitations


def _dominant_reliability(rows: list[dict]) -> str:
    if not rows:
        return "manual"
    reliabilities = [row["reliability"] for row in rows]
    if "official" in reliabilities:
        return "official"
    return reliabilities[0]
