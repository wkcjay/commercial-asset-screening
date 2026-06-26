from datetime import date, datetime, timedelta, timezone
from statistics import median

from app.models.domain import (
    AmenitySummary,
    Assumption,
    ComparableSummary,
    ComparableTransaction,
    ComparableWithDistance,
    ConfidenceAssessment,
    DemographicContext,
    Limitation,
    LocationScore,
    LocationScoreComponent,
    NearbyAmenity,
    OutlierPolicy,
    PlanningContext,
    RiskAssessment,
    RiskItem,
    Site,
    Source,
    Trend,
)
from app.services.geo import distance_km


SINGAPORE_TIMEZONE = timezone(timedelta(hours=8), name="Asia/Singapore")


def current_scoring_date() -> date:
    return datetime.now(SINGAPORE_TIMEZONE).date()


def _months_since(value: str, as_of_date: date) -> int:
    parsed = date.fromisoformat(value)
    return max(0, (as_of_date.year - parsed.year) * 12 + as_of_date.month - parsed.month)


def _component_score(value: float, thresholds: list[tuple[float, float]], fallback: float) -> float:
    for limit, score in thresholds:
        if value <= limit:
            return score
    return fallback


def _iqr(values: list[float]) -> tuple[float, float, float]:
    sorted_values = sorted(values)
    midpoint = len(sorted_values) // 2
    lower_half = sorted_values[:midpoint]
    upper_half = sorted_values[midpoint:] if len(sorted_values) % 2 == 0 else sorted_values[midpoint + 1 :]
    q1 = median(lower_half) if lower_half else sorted_values[0]
    q3 = median(upper_half) if upper_half else sorted_values[-1]
    return q1, q3, q3 - q1


def score_comparable(site: Site, comparable: ComparableTransaction, distance: float, recency_months: int) -> tuple[float, list[str]]:
    distance_score = _component_score(distance, [(0.5, 1.0), (1.0, 0.85), (2.0, 0.65), (3.0, 0.40)], 0.20)
    recency_score = _component_score(recency_months, [(6, 1.0), (12, 0.85), (24, 0.60), (36, 0.35)], 0.10)
    planning_score = 1.0 if comparable.planningArea == site.planningArea else 0.20
    district_score = 1.0 if comparable.district == site.district else 0.30
    tenure_score = 1.0 if comparable.tenure and comparable.tenure == site.tenure else 0.50
    property_score = 1.0 if comparable.propertyType in {"condo", "apartment"} else 0.60
    score = (
        35 * distance_score
        + 25 * recency_score
        + 15 * planning_score
        + 10 * district_score
        + 10 * tenure_score
        + 5 * property_score
    )

    reasons = [f"{distance:.2f} km from site", f"{recency_months} months old"]
    if comparable.planningArea == site.planningArea:
        reasons.append("same planning area")
    if comparable.district == site.district:
        reasons.append("same district")
    if comparable.tenure == site.tenure:
        reasons.append("same tenure")
    return round(score, 2), reasons


def build_comparable_summary(
    site: Site,
    candidates: list[ComparableTransaction],
    as_of_date: date | None = None,
) -> ComparableSummary:
    resolved_as_of_date = as_of_date or current_scoring_date()
    scored: list[ComparableWithDistance] = []
    for candidate in candidates:
        if candidate.country != "SG":
            continue
        distance = distance_km(site.latitude, site.longitude, candidate.latitude, candidate.longitude)
        recency_months = _months_since(candidate.transactionDate, resolved_as_of_date)
        if distance > 3.0 or recency_months > 36:
            continue
        relevance, reasons = score_comparable(site, candidate, distance, recency_months)
        scored.append(
            ComparableWithDistance(
                **candidate.model_dump(),
                distanceKm=round(distance, 3),
                recencyMonths=recency_months,
                relevanceScore=relevance,
                relevanceReasons=reasons,
            )
        )

    scored.sort(key=lambda item: item.relevanceScore, reverse=True)
    selected = scored[:8]
    selected_for_metrics = selected
    outlier_ids: list[str] = []
    outlier_policy = OutlierPolicy(
        method="none",
        excludedTransactionIds=[],
        explanation="IQR outlier filtering not applied because fewer than 6 selected comparables were available.",
    )

    if len(selected) >= 6:
        q1, q3, spread = _iqr([item.pricePsf for item in selected])
        lower = q1 - 1.5 * spread
        upper = q3 + 1.5 * spread
        selected_for_metrics = [item for item in selected if lower <= item.pricePsf <= upper]
        outlier_ids = [item.id for item in selected if item.id not in {kept.id for kept in selected_for_metrics}]
        outlier_policy = OutlierPolicy(
            method="iqr",
            excludedTransactionIds=outlier_ids,
            explanation="IQR outlier filtering applied to selected comparable price psf values.",
        )

    prices = [item.pricePsf for item in selected_for_metrics]
    latest_date = max((item.transactionDate for item in selected), default=None)
    return ComparableSummary(
        searchRadiusKm=3.0,
        candidateCount=len(scored),
        selectedCount=len(selected),
        selectedComparables=selected,
        excludedCandidateCount=max(0, len(scored) - len(selected)),
        medianPricePsf=round(float(median(prices)), 2) if prices else None,
        minPricePsf=min(prices) if prices else None,
        maxPricePsf=max(prices) if prices else None,
        latestTransactionDate=latest_date,
        trend=_build_trend(selected_for_metrics),
        outlierPolicy=outlier_policy,
    )


def _build_trend(selected: list[ComparableWithDistance]) -> Trend:
    if len(selected) < 4:
        return Trend(label="insufficient-data", basis="Fewer than 4 selected comparables are available.")
    sorted_items = sorted(selected, key=lambda item: item.transactionDate)
    midpoint = len(sorted_items) // 2
    earlier = sorted_items[:midpoint]
    recent = sorted_items[midpoint:]
    earlier_median = float(median([item.pricePsf for item in earlier]))
    recent_median = float(median([item.pricePsf for item in recent]))
    percent_change = (recent_median - earlier_median) / earlier_median if earlier_median else 0
    if percent_change > 0.05:
        label = "rising"
    elif percent_change < -0.05:
        label = "softening"
    else:
        label = "stable"
    return Trend(
        label=label,
        basis="Median price psf among selected comparables split by HDB registration month.",
        earlierMedianPricePsf=round(earlier_median, 2),
        recentMedianPricePsf=round(recent_median, 2),
        percentChange=round(percent_change, 4),
    )


def build_amenity_summary(site: Site, amenities: list[NearbyAmenity]) -> AmenitySummary:
    nearby = [item for item in amenities if item.distanceKm <= 1.5 and not item.needsReview]
    nearby.sort(key=lambda item: item.distanceKm)
    category_counts: dict[str, int] = {}
    for item in nearby:
        category_counts[item.category] = category_counts.get(item.category, 0) + 1
    mrt_items = [item for item in nearby if item.category == "mrt"]
    nearest_mrt = min(mrt_items, key=lambda item: item.distanceKm) if mrt_items else None
    highlights = []
    if nearest_mrt:
        highlights.append(f"Nearest MRT: {nearest_mrt.name} at {nearest_mrt.distanceKm:.2f} km.")
    if category_counts:
        highlights.append(f"{len(category_counts)} amenity categories represented within 1.5 km.")
    return AmenitySummary(
        searchRadiusKm=1.5,
        nearestMrt=nearest_mrt,
        categoryCounts=category_counts,
        nearbyAmenities=nearby[:12],
        highlights=highlights,
    )


def compute_location_score(
    amenity_summary: AmenitySummary,
    demographic_context: DemographicContext | None,
    planning_context: PlanningContext | None,
) -> LocationScore:
    transport = _transport_score(amenity_summary.nearestMrt)
    amenity_score = _amenity_score(amenity_summary)
    catchment = _catchment_score(demographic_context)
    planning = _planning_fit_score(planning_context)
    overall = round(0.40 * transport + 0.30 * amenity_score + 0.15 * catchment + 0.15 * planning, 2)
    rating = "strong" if overall >= 80 else "moderate" if overall >= 60 else "weak" if overall > 0 else "incomplete"
    return LocationScore(
        overall=overall,
        transport=transport,
        amenities=amenity_score,
        catchment=catchment,
        planningFit=planning,
        rating=rating,
        explanations=[
            "Overall location score combines transport, amenities, catchment context, and planning fit.",
            "Scores use straight-line distance and available planning-area context.",
        ],
        components=[
            LocationScoreComponent(name="Transport", score=transport, weight=0.40, explanation="Based on nearest MRT distance."),
            LocationScoreComponent(name="Amenities", score=amenity_score, weight=0.30, explanation="Based on category diversity and daily-needs amenities."),
            LocationScoreComponent(
                name="Catchment",
                score=catchment,
                weight=0.15,
                explanation="No official demographic context is loaded for this reference location." if demographic_context is None else "Based on planning-area demographic context completeness.",
            ),
            LocationScoreComponent(
                name="Planning fit",
                score=planning,
                weight=0.15,
                explanation="No official planning context is loaded for this reference location." if planning_context is None else "Based on indicative zoning and plot ratio availability.",
            ),
        ],
    )


def _transport_score(nearest_mrt: NearbyAmenity | None) -> float:
    if nearest_mrt is None:
        return 0
    return _component_score(nearest_mrt.distanceKm, [(0.4, 100), (0.8, 85), (1.2, 65), (1.8, 40)], 20)


def _amenity_score(summary: AmenitySummary) -> float:
    expected = {"mrt", "school", "mall", "park", "healthcare", "supermarket"}
    represented = expected.intersection(summary.categoryCounts.keys())
    diversity = len(represented) / len(expected)
    daily = len({"school", "healthcare", "supermarket", "park"}.intersection(summary.categoryCounts.keys())) / 4
    destination = 1.0 if {"mall", "employment_node", "park"}.intersection(summary.categoryCounts.keys()) else 0.0
    return round(100 * (0.40 * diversity + 0.35 * daily + 0.25 * destination), 2)


def _catchment_score(context: DemographicContext | None) -> float:
    if context is None:
        return 0
    present = sum(
        value is not None
        for value in [context.population, context.residentHouseholds, context.medianAge, context.householdIncomeBand]
    )
    if present == 4:
        return 100
    if present == 3:
        return 75
    if present >= 1:
        return 50
    return 25 if context.notes else 0


def _planning_fit_score(context: PlanningContext | None) -> float:
    if context is None:
        return 0
    if context.zoning == "residential" and context.grossPlotRatio is not None:
        return 100
    if context.zoning == "residential":
        return 75
    if context.zoning in {"mixed-use", "white"}:
        return 50
    if context.zoning == "unknown":
        return 25
    return 0


def derive_risks(
    comparable_summary: ComparableSummary,
    amenity_summary: AmenitySummary,
    planning_context: PlanningContext | None,
    sources: list[Source],
    as_of_date: date | None = None,
) -> RiskAssessment:
    resolved_as_of_date = as_of_date or current_scoring_date()
    items: list[RiskItem] = []
    if comparable_summary.selectedCount < 3:
        items.append(RiskItem(id="risk-insufficient-comps", severity="high", category="data", statement="Insufficient nearby comparable evidence.", evidence=["selected comparable count < 3"], mitigation="Validate against paid transaction data."))
    if comparable_summary.latestTransactionDate and _months_since(comparable_summary.latestTransactionDate, resolved_as_of_date) > 12:
        items.append(RiskItem(id="risk-stale-comps", severity="medium", category="market", statement="Transaction evidence may be stale.", evidence=[comparable_summary.latestTransactionDate], mitigation="Refresh with current transactions."))
    if amenity_summary.nearestMrt is None or amenity_summary.nearestMrt.distanceKm > 1.2:
        items.append(RiskItem(id="risk-transport", severity="medium", category="location", statement="Rapid transit accessibility may be weaker.", evidence=["nearest MRT distance"], mitigation="Check walking routes and bus connectivity."))
    if planning_context is None:
        items.append(RiskItem(id="risk-planning-missing", severity="high", category="planning", statement="Planning context is missing.", evidence=["no planning row"], mitigation="Verify zoning and plot ratio with planning sources."))
    if any(source.reliability in {"synthetic", "sample", "proxy", "seeded"} for source in sources):
        items.append(RiskItem(id="risk-sample-data", severity="medium", category="data", statement="Sample/proxy data limits investment reliability.", evidence=["source reliability includes sample or seeded data"], mitigation="Replace sample data with verified market data."))
    if comparable_summary.trend.label == "softening":
        items.append(RiskItem(id="risk-softening-trend", severity="medium", category="market", statement="Selected comparables indicate softer recent pricing.", evidence=[comparable_summary.trend.basis], mitigation="Review more recent transactions and supply conditions."))
    high = any(item.severity == "high" for item in items)
    medium = any(item.severity == "medium" for item in items)
    return RiskAssessment(items=items, overallRiskLevel="high" if high else "medium" if medium else "low")


def build_assumptions() -> list[Assumption]:
    return [
        Assumption(id="assumption-comps", statement="Selected comparables are treated as broadly relevant to the subject site."),
        Assumption(id="assumption-psf", statement="Price per square foot is used as the primary normalized transaction metric."),
        Assumption(id="assumption-distance", statement="Accessibility scoring uses straight-line distance, not walking time."),
        Assumption(id="assumption-planning", statement="Planning context is indicative and requires professional verification."),
    ]


def build_limitations(has_demographics: bool, has_planning: bool, has_non_official_data: bool = False) -> list[Limitation]:
    limitations = [
        Limitation(id="limitation-live-feed", statement="No live paid private-market transaction feed is connected."),
        Limitation(id="limitation-supply", statement="No current supply pipeline data is included."),
        Limitation(id="limitation-financial-model", statement="No construction cost, sales velocity, or financial model is included."),
        Limitation(id="limitation-distance", statement="Walking routes and travel times are approximated by distance."),
    ]
    if has_non_official_data:
        limitations.append(Limitation(id="limitation-sample-data", statement="Sample/proxy data may not represent current market conditions."))
    if not has_demographics:
        limitations.append(Limitation(id="limitation-demographics", statement="No demographic context is available for the planning area."))
    if not has_planning:
        limitations.append(Limitation(id="limitation-planning", statement="No legal zoning opinion is provided."))
    return limitations


def compute_confidence(
    comparable_summary: ComparableSummary,
    amenity_summary: AmenitySummary,
    demographic_context: DemographicContext | None,
    planning_context: PlanningContext | None,
    sources: list[Source],
    as_of_date: date | None = None,
) -> ConfidenceAssessment:
    resolved_as_of_date = as_of_date or current_scoring_date()
    score = 100
    deductions: list[str] = []
    drivers: list[str] = []
    if comparable_summary.selectedCount < 3:
        score -= 30
        deductions.append("Comparable count below 3 (-30).")
    elif comparable_summary.selectedCount <= 4:
        score -= 15
        deductions.append("Comparable count between 3 and 4 (-15).")
    else:
        drivers.append("Sufficient selected comparable count.")
    if comparable_summary.latestTransactionDate and _months_since(comparable_summary.latestTransactionDate, resolved_as_of_date) > 12:
        score -= 15
        deductions.append("Latest comparable older than 12 months (-15).")
    if planning_context is None:
        score -= 25
        deductions.append("No planning context (-25).")
    elif planning_context.grossPlotRatio is None:
        score -= 10
        deductions.append("Planning context missing plot ratio (-10).")
    else:
        drivers.append("Planning context includes zoning and plot ratio.")
    if demographic_context is None:
        score -= 15
        deductions.append("No demographic context (-15).")
    else:
        drivers.append("Planning-area demographic context is available.")
    if any(source.reliability in {"synthetic", "sample", "proxy", "seeded"} for source in sources):
        score -= 15
        deductions.append("Sample, proxy, or seeded data included (-15).")
    if amenity_summary.nearestMrt is None:
        score -= 10
        deductions.append("No nearby MRT amenity data (-10).")
    score = max(0, min(100, score))
    level = "high" if score >= 80 else "medium" if score >= 55 else "low"
    return ConfidenceAssessment(level=level, score=score, drivers=drivers, deductions=deductions)
