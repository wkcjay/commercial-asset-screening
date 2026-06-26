from sqlalchemy import func, select

from app.db import repositories
from app.db.schema import amenities, asset_valuations, commercial_assets, data_versions, market_events, sites, sources, transactions


def test_db_init_loads_official_extract_tables(test_engine):
    with test_engine.connect() as connection:
        site_count = connection.execute(select(func.count()).select_from(sites)).scalar_one()
        transaction_count = connection.execute(select(func.count()).select_from(transactions)).scalar_one()
        amenity_count = connection.execute(select(func.count()).select_from(amenities)).scalar_one()
        commercial_asset_count = connection.execute(select(func.count()).select_from(commercial_assets)).scalar_one()
        asset_valuation_count = connection.execute(select(func.count()).select_from(asset_valuations)).scalar_one()
        market_event_count = connection.execute(select(func.count()).select_from(market_events)).scalar_one()
        version_count = connection.execute(select(func.count()).select_from(data_versions)).scalar_one()
        official_source_count = connection.execute(
            select(func.count()).select_from(sources).where(sources.c.reliability == "official")
        ).scalar_one()

    assert site_count == 3
    assert transaction_count >= 30
    assert amenity_count >= 18
    assert commercial_asset_count >= 10
    assert asset_valuation_count >= 7
    assert market_event_count >= 4
    assert version_count == 1
    assert official_source_count >= 2


def test_record_source_links_resolve(test_engine):
    assert repositories.validate_source_links(test_engine) == []


def test_category_normalization_writes_auditable_fields(test_engine):
    rows = repositories.list_amenities(test_engine)
    mrt = next(row for row in rows if row["id"] == "am-queenstown-001")
    assert mrt["raw_category"] == "MRT Station"
    assert mrt["normalized_category"] == "mrt"
    assert mrt["category_label_source"] == "rule"
    assert mrt["needs_review"] == 0
