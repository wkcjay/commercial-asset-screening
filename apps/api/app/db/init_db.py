import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.engine import Engine

from app.constants import DATA_VERSION_LABEL
from app.db.schema import (
    ALL_BASE_TABLES,
    amenities,
    asset_valuations,
    commercial_assets,
    data_versions,
    demographics,
    market_events,
    metadata,
    planning_contexts,
    record_sources,
    sites,
    sources,
    transactions,
)
from app.services.normalization import normalize_amenity_category


def load_json(raw_dir: Path, filename: str) -> list[dict[str, Any]]:
    with (raw_dir / filename).open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, list):
        raise ValueError(f"{filename} must contain a JSON array")
    return data


def load_optional_json(raw_dir: Path, filename: str) -> list[dict[str, Any]]:
    path = raw_dir / filename
    if not path.exists():
        return []
    return load_json(raw_dir, filename)


def compute_source_hash(raw_dir: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(raw_dir.glob("*.json")):
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _upsert_many(connection, table, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    statement = sqlite_insert(table).values(rows)
    update_columns = {
        column.name: getattr(statement.excluded, column.name)
        for column in table.columns
        if not column.primary_key
    }
    if update_columns:
        connection.execute(statement.on_conflict_do_update(index_elements=table.primary_key.columns, set_=update_columns))
    else:
        connection.execute(statement.on_conflict_do_nothing(index_elements=table.primary_key.columns))


def initialize_database(engine: Engine, raw_data_dir: str | Path) -> str:
    raw_dir = Path(raw_data_dir)
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")

    metadata.create_all(engine)
    source_hash = compute_source_hash(raw_dir)
    version_id = f"official-{source_hash[:12]}"
    created_at = datetime.now(UTC).isoformat()

    with engine.begin() as connection:
        for table in ALL_BASE_TABLES:
            connection.execute(delete(table))

        _upsert_many(connection, sources, load_json(raw_dir, "sources.json"))
        _upsert_many(connection, commercial_assets, load_optional_json(raw_dir, "commercial_assets.json"))
        _upsert_many(connection, asset_valuations, load_optional_json(raw_dir, "asset_valuations.json"))

        market_event_rows = []
        for row in load_optional_json(raw_dir, "market_events.json"):
            market_event_rows.append({**row, "counterparties_json": json.dumps(row.get("counterparties", []))})
            market_event_rows[-1].pop("counterparties", None)
            market_event_rows[-1]["needs_review"] = int(row.get("needs_review", False))
        _upsert_many(connection, market_events, market_event_rows)

        _upsert_many(connection, sites, load_json(raw_dir, "sites.json"))
        _upsert_many(connection, transactions, load_json(raw_dir, "transactions.json"))

        amenity_rows = []
        for row in load_json(raw_dir, "amenities.json"):
            label = normalize_amenity_category(row.get("raw_category"))
            amenity_rows.append(
                {
                    **row,
                    "normalized_category": label.normalized_category,
                    "category_confidence": label.confidence,
                    "category_label_source": label.label_source,
                    "category_rationale": label.rationale,
                    "needs_review": int(label.needs_review),
                }
            )
        _upsert_many(connection, amenities, amenity_rows)

        demographic_rows = []
        for row in load_json(raw_dir, "demographics.json"):
            demographic_rows.append({**row, "notes_json": json.dumps(row.get("notes", []))})
            demographic_rows[-1].pop("notes", None)
        _upsert_many(connection, demographics, demographic_rows)

        planning_rows = []
        for row in load_json(raw_dir, "planning_contexts.json"):
            planning_rows.append(
                {
                    **row,
                    "master_plan_notes_json": json.dumps(row.get("master_plan_notes", [])),
                    "professional_verification_required": int(row.get("professional_verification_required", True)),
                }
            )
            planning_rows[-1].pop("master_plan_notes", None)
        _upsert_many(connection, planning_contexts, planning_rows)
        _upsert_many(connection, record_sources, load_json(raw_dir, "record_sources.json"))

        _upsert_many(
            connection,
            data_versions,
            [
                {
                    "id": version_id,
                    "label": DATA_VERSION_LABEL,
                    "created_at": created_at,
                    "source_hash": source_hash,
                    "notes": "Official Singapore open-data extract for local screening.",
                }
            ],
        )

    return version_id


def database_has_current_data(engine: Engine, raw_data_dir: str | Path) -> bool:
    metadata.create_all(engine)
    current_hash = compute_source_hash(Path(raw_data_dir))
    with engine.connect() as connection:
        row = connection.execute(
            select(data_versions.c.source_hash).order_by(data_versions.c.created_at.desc()).limit(1)
        ).first()
    return row is not None and row._mapping["source_hash"] == current_hash
