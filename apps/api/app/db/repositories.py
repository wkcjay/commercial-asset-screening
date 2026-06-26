import json
from collections.abc import Iterable
from typing import Any

from sqlalchemy import select
from sqlalchemy.engine import Engine

from app.db.schema import (
    amenities,
    asset_valuations,
    commercial_assets,
    data_versions,
    demographics,
    market_events,
    planning_contexts,
    record_sources,
    sites,
    sources,
    transactions,
)


def row_to_dict(row) -> dict[str, Any]:
    return dict(row._mapping)


def get_current_data_version(engine: Engine) -> str:
    with engine.connect() as connection:
        row = connection.execute(
            select(data_versions.c.id).order_by(data_versions.c.created_at.desc()).limit(1)
        ).first()
    if row is None:
        raise RuntimeError("Database has no data version. Run db_init first.")
    return row_to_dict(row)["id"]


def get_source_ids(engine: Engine, record_type: str, record_id: str) -> list[str]:
    with engine.connect() as connection:
        rows = connection.execute(
            select(record_sources.c.source_id).where(
                record_sources.c.record_type == record_type,
                record_sources.c.record_id == record_id,
            )
        ).all()
    return [row_to_dict(row)["source_id"] for row in rows]


def list_sources(engine: Engine, source_ids: Iterable[str]) -> list[dict[str, Any]]:
    ids = sorted(set(source_ids))
    if not ids:
        return []
    with engine.connect() as connection:
        rows = connection.execute(select(sources).where(sources.c.id.in_(ids))).all()
    return [row_to_dict(row) for row in rows]


def list_site_summaries(engine: Engine) -> list[dict[str, Any]]:
    with engine.connect() as connection:
        rows = connection.execute(select(sites).order_by(sites.c.name)).all()
    return [row_to_dict(row) for row in rows]


def get_site(engine: Engine, site_id: str) -> dict[str, Any] | None:
    with engine.connect() as connection:
        row = connection.execute(select(sites).where(sites.c.id == site_id)).first()
    return row_to_dict(row) if row else None


def list_commercial_assets(engine: Engine) -> list[dict[str, Any]]:
    with engine.connect() as connection:
        rows = connection.execute(select(commercial_assets).order_by(commercial_assets.c.issuer, commercial_assets.c.name)).all()
    return [row_to_dict(row) for row in rows]


def get_commercial_asset(engine: Engine, asset_id: str) -> dict[str, Any] | None:
    with engine.connect() as connection:
        row = connection.execute(select(commercial_assets).where(commercial_assets.c.id == asset_id)).first()
    return row_to_dict(row) if row else None


def list_asset_valuations(engine: Engine, asset_id: str | None = None) -> list[dict[str, Any]]:
    statement = select(asset_valuations)
    if asset_id is not None:
        statement = statement.where(asset_valuations.c.asset_id == asset_id)
    statement = statement.order_by(asset_valuations.c.asset_id, asset_valuations.c.valuation_date.desc())
    with engine.connect() as connection:
        rows = connection.execute(statement).all()
    return [row_to_dict(row) for row in rows]


def list_market_events(engine: Engine) -> list[dict[str, Any]]:
    with engine.connect() as connection:
        rows = connection.execute(select(market_events).order_by(market_events.c.event_date.desc())).all()
    events = []
    for row in rows:
        data = row_to_dict(row)
        data["counterparties"] = json.loads(data.pop("counterparties_json"))
        data["needs_review"] = bool(data["needs_review"])
        events.append(data)
    return events


def list_transactions(engine: Engine) -> list[dict[str, Any]]:
    with engine.connect() as connection:
        rows = connection.execute(select(transactions)).all()
    return [row_to_dict(row) for row in rows]


def list_amenities(engine: Engine) -> list[dict[str, Any]]:
    with engine.connect() as connection:
        rows = connection.execute(select(amenities)).all()
    return [row_to_dict(row) for row in rows]


def get_demographics(engine: Engine, planning_area: str) -> dict[str, Any] | None:
    with engine.connect() as connection:
        row = connection.execute(
            select(demographics).where(demographics.c.planning_area == planning_area)
        ).first()
    if row is None:
        return None
    data = row_to_dict(row)
    data["notes"] = json.loads(data.pop("notes_json"))
    return data


def get_planning_context(engine: Engine, planning_area: str) -> dict[str, Any] | None:
    with engine.connect() as connection:
        row = connection.execute(
            select(planning_contexts).where(planning_contexts.c.planning_area == planning_area)
        ).first()
    if row is None:
        return None
    data = row_to_dict(row)
    data["master_plan_notes"] = json.loads(data.pop("master_plan_notes_json"))
    data["professional_verification_required"] = bool(data["professional_verification_required"])
    return data


def validate_source_links(engine: Engine) -> list[str]:
    errors: list[str] = []
    table_ids = {
        "site": (sites, sites.c.id),
        "commercial_asset": (commercial_assets, commercial_assets.c.id),
        "asset_valuation": (asset_valuations, asset_valuations.c.id),
        "market_event": (market_events, market_events.c.id),
        "transaction": (transactions, transactions.c.id),
        "amenity": (amenities, amenities.c.id),
        "demographic": (demographics, demographics.c.planning_area),
        "planning": (planning_contexts, planning_contexts.c.planning_area),
    }
    with engine.connect() as connection:
        source_ids = {
            row_to_dict(row)["id"]
            for row in connection.execute(select(sources.c.id)).all()
        }
        links = [row_to_dict(row) for row in connection.execute(select(record_sources)).all()]
        for link in links:
            if link["source_id"] not in source_ids:
                errors.append(f"Missing source {link['source_id']} for {link['record_type']}:{link['record_id']}")
                continue
            mapping = table_ids.get(link["record_type"])
            if mapping is None:
                errors.append(f"Unsupported record type {link['record_type']}")
                continue
            table, id_column = mapping
            exists = connection.execute(
                select(id_column).select_from(table).where(id_column == link["record_id"]).limit(1)
            ).first()
            if exists is None:
                errors.append(f"Missing record {link['record_type']}:{link['record_id']}")
    return errors
