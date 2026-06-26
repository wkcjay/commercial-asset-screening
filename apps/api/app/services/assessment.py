from dataclasses import dataclass

from sqlalchemy.engine import Engine

from app.db import repositories
from app.models.api import CacheMeta
from app.models.domain import (
    Amenity,
    ComparableTransaction,
    DemographicContext,
    NearbyAmenity,
    PlanningContext,
    Site,
    SiteAssessment,
    SiteSummary,
    Source,
)
from app.services import cache
from app.services.geo import distance_km
from app.services.scoring import (
    build_amenity_summary,
    build_assumptions,
    build_comparable_summary,
    build_limitations,
    compute_confidence,
    compute_location_score,
    current_scoring_date,
    derive_risks,
)


class NotFoundError(Exception):
    pass


@dataclass(frozen=True)
class AssessmentResult:
    assessment: SiteAssessment
    data_version: str
    cache_meta: CacheMeta
    warnings: list[str]


def list_site_summaries(engine: Engine) -> list[SiteSummary]:
    summaries: list[SiteSummary] = []
    for row in repositories.list_site_summaries(engine):
        source_ids = repositories.get_source_ids(engine, "site", row["id"])
        reliability = "seeded"
        if source_ids:
            sources = repositories.list_sources(engine, source_ids)
            reliability = sources[0].get("reliability", "seeded")
        summaries.append(
            SiteSummary(
                id=row["id"],
                name=row["name"],
                address=row["address"],
                district=row["district"],
                planningArea=row["planning_area"],
                assetClass="residential",
                dataReliability=reliability,
            )
        )
    return summaries


def assess_site(engine: Engine, site_id: str) -> AssessmentResult:
    data_version = repositories.get_current_data_version(engine)
    as_of_date = current_scoring_date()
    key = cache.assessment_cache_key(site_id, data_version, as_of_date.isoformat())
    cached = cache.load_assessment(engine, key)
    if cached is not None:
        return AssessmentResult(
            assessment=SiteAssessment.model_validate(cached),
            data_version=data_version,
            cache_meta=cache.cache_meta(True, key),
            warnings=[],
        )

    site_row = repositories.get_site(engine, site_id)
    if site_row is None:
        raise NotFoundError(f"Unknown site: {site_id}")

    site = _site_from_row(engine, site_row)
    transaction_models = [_transaction_from_row(engine, row) for row in repositories.list_transactions(engine)]
    comparable_summary = build_comparable_summary(site, transaction_models, as_of_date)

    nearby_amenities = [
        _nearby_amenity_from_row(engine, site, row)
        for row in repositories.list_amenities(engine)
    ]
    amenity_summary = build_amenity_summary(site, nearby_amenities)

    demographic_context = _demographic_context_from_row(engine, repositories.get_demographics(engine, site.planningArea))
    planning_context = _planning_context_from_row(engine, repositories.get_planning_context(engine, site.planningArea))

    source_ids = set(site.sourceIds)
    for comp in comparable_summary.selectedComparables:
        source_ids.update(comp.sourceIds)
    for amenity in amenity_summary.nearbyAmenities:
        source_ids.update(amenity.sourceIds)
    if demographic_context:
        source_ids.update(demographic_context.sourceIds)
    if planning_context:
        source_ids.update(planning_context.sourceIds)
    sources = [_source_from_row(row) for row in repositories.list_sources(engine, source_ids)]

    location_score = compute_location_score(amenity_summary, demographic_context, planning_context)
    risk_assessment = derive_risks(comparable_summary, amenity_summary, planning_context, sources, as_of_date)
    confidence = compute_confidence(comparable_summary, amenity_summary, demographic_context, planning_context, sources, as_of_date)
    has_non_official_data = any(source.reliability in {"synthetic", "sample", "proxy", "seeded"} for source in sources)
    limitations = build_limitations(demographic_context is not None, planning_context is not None, has_non_official_data)
    warnings = [limitation.statement for limitation in limitations if "Sample/proxy" in limitation.statement]

    assessment = SiteAssessment(
        assessmentId=f"asmt-{key[:16]}",
        generatedAt=cache.utc_now(),
        site=site,
        scope={"market": "Singapore", "assetClass": "residential", "mode": "sample-site", "asOfDate": as_of_date.isoformat()},
        comparableSummary=comparable_summary,
        locationScore=location_score,
        amenitySummary=amenity_summary,
        demographicContext=demographic_context,
        planningContext=planning_context,
        riskAssessment=risk_assessment,
        confidence=confidence,
        assumptions=build_assumptions(),
        limitations=limitations,
        sources=sources,
    )
    cache.store_assessment(engine, site_id, data_version, key, assessment.model_dump(mode="json"))
    return AssessmentResult(
        assessment=assessment,
        data_version=data_version,
        cache_meta=cache.cache_meta(False, key),
        warnings=warnings,
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


def _site_from_row(engine: Engine, row: dict) -> Site:
    return Site(
        id=row["id"],
        name=row["name"],
        address=row["address"],
        country=row["country"],
        district=row["district"],
        planningArea=row["planning_area"],
        latitude=row["latitude"],
        longitude=row["longitude"],
        assetClass=row["asset_class"],
        tenure=row.get("tenure") or "unknown",
        landAreaSqm=row.get("land_area_sqm"),
        grossPlotRatioHint=row.get("gross_plot_ratio_hint"),
        sourceIds=repositories.get_source_ids(engine, "site", row["id"]),
    )


def _transaction_from_row(engine: Engine, row: dict) -> ComparableTransaction:
    return ComparableTransaction(
        id=row["id"],
        projectName=row["project_name"],
        address=row["address"],
        country=row["country"],
        district=row["district"],
        planningArea=row["planning_area"],
        latitude=row["latitude"],
        longitude=row["longitude"],
        transactionDate=row["transaction_date"],
        propertyType=row["property_type"],
        tenure=row.get("tenure") or "unknown",
        floorAreaSqm=row.get("floor_area_sqm"),
        priceSgd=row["price_sgd"],
        pricePsf=row["price_psf"],
        sourceIds=repositories.get_source_ids(engine, "transaction", row["id"]),
    )


def _nearby_amenity_from_row(engine: Engine, site: Site, row: dict) -> NearbyAmenity:
    amenity = Amenity(
        id=row["id"],
        name=row["name"],
        rawCategory=row.get("raw_category"),
        category=row["normalized_category"],
        categoryConfidence=row.get("category_confidence"),
        categoryLabelSource=row["category_label_source"],
        needsReview=bool(row["needs_review"]),
        latitude=row["latitude"],
        longitude=row["longitude"],
        sourceIds=repositories.get_source_ids(engine, "amenity", row["id"]),
    )
    return NearbyAmenity(
        **amenity.model_dump(),
        distanceKm=round(distance_km(site.latitude, site.longitude, amenity.latitude, amenity.longitude), 3),
    )


def _demographic_context_from_row(engine: Engine, row: dict | None) -> DemographicContext | None:
    if row is None:
        return None
    return DemographicContext(
        planningArea=row["planning_area"],
        population=row.get("population"),
        residentHouseholds=row.get("resident_households"),
        medianAge=row.get("median_age"),
        householdIncomeBand=row.get("household_income_band"),
        notes=row.get("notes", []),
        sourceIds=repositories.get_source_ids(engine, "demographic", row["planning_area"]),
    )


def _planning_context_from_row(engine: Engine, row: dict | None) -> PlanningContext | None:
    if row is None:
        return None
    return PlanningContext(
        planningArea=row["planning_area"],
        zoning=row.get("zoning") or "unknown",
        grossPlotRatio=row.get("gross_plot_ratio"),
        heightControl=row.get("height_control"),
        masterPlanNotes=row.get("master_plan_notes", []),
        professionalVerificationRequired=bool(row["professional_verification_required"]),
        sourceIds=repositories.get_source_ids(engine, "planning", row["planning_area"]),
    )
