from app.models.domain import ComparableTransaction, Site
from app.services.geo import distance_km
from app.services.scoring import build_comparable_summary, score_comparable


def test_haversine_distance_is_reasonable():
    distance = distance_km(1.2949, 103.8082, 1.2941, 103.8061)
    assert 0.20 <= distance <= 0.30


def test_comparable_scoring_prefers_near_recent_same_area():
    site = Site(
        id="site-test",
        name="Test",
        address="Test",
        country="SG",
        district="3",
        planningArea="Queenstown",
        latitude=1.2949,
        longitude=103.8082,
        assetClass="residential",
        tenure="leasehold",
    )
    comp = ComparableTransaction(
        id="tx-test",
        projectName="Nearby",
        address="Nearby",
        country="SG",
        district="3",
        planningArea="Queenstown",
        latitude=1.2943,
        longitude=103.8062,
        transactionDate="2026-01-01",
        propertyType="condo",
        tenure="leasehold",
        floorAreaSqm=80,
        priceSgd=2000000,
        pricePsf=2300,
    )
    score, reasons = score_comparable(site, comp, 0.25, 5)
    assert score > 90
    assert "same planning area" in reasons


def test_comparable_summary_computes_metrics(test_engine):
    from app.services.assessment import assess_site

    result = assess_site(test_engine, "site-queenstown-001")
    summary = result.assessment.comparableSummary
    assert summary.selectedCount >= 5
    assert summary.medianPricePsf is not None
    assert summary.trend.label in {"rising", "stable", "softening", "insufficient-data"}
