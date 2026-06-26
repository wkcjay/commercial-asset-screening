import hashlib
import json
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.engine import Engine

from app.constants import ALGORITHM_VERSION, PROMPT_VERSION
from app.db.schema import assessment_runs, memo_runs
from app.models.api import CacheMeta


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def stable_key(*parts: str | None) -> str:
    joined = "|".join(part or "" for part in parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def assessment_cache_key(site_id: str, data_version: str, as_of_date: str | None = None) -> str:
    return stable_key(site_id, data_version, ALGORITHM_VERSION, as_of_date)


def commercial_assessment_cache_key(asset_id: str, data_version: str) -> str:
    return stable_key("commercial", asset_id, data_version, ALGORITHM_VERSION)


def memo_cache_key(assessment_id: str, provider: str, model: str | None, tone: str) -> str:
    return stable_key(assessment_id, PROMPT_VERSION, provider, model, tone)


def load_assessment(engine: Engine, cache_key: str) -> dict | None:
    with engine.connect() as connection:
        row = connection.execute(
            select(assessment_runs.c.assessment_json).where(assessment_runs.c.cache_key == cache_key)
        ).first()
    if row is None:
        return None
    return json.loads(row._mapping["assessment_json"])


def store_assessment(engine: Engine, site_id: str, data_version: str, cache_key: str, assessment: dict) -> None:
    row = {
        "id": f"asmt-run-{cache_key[:16]}",
        "site_id": site_id,
        "data_version": data_version,
        "algorithm_version": ALGORITHM_VERSION,
        "cache_key": cache_key,
        "generated_at": utc_now(),
        "assessment_json": json.dumps(assessment, sort_keys=True),
    }
    statement = sqlite_insert(assessment_runs).values(row)
    update_columns = {
        "generated_at": statement.excluded.generated_at,
        "assessment_json": statement.excluded.assessment_json,
    }
    with engine.begin() as connection:
        connection.execute(statement.on_conflict_do_update(index_elements=[assessment_runs.c.cache_key], set_=update_columns))


def load_memo(engine: Engine, cache_key: str) -> dict | None:
    with engine.connect() as connection:
        row = connection.execute(select(memo_runs.c.memo_json).where(memo_runs.c.cache_key == cache_key)).first()
    if row is None:
        return None
    return json.loads(row._mapping["memo_json"])


def store_memo(
    engine: Engine,
    assessment_id: str,
    provider: str,
    model: str | None,
    tone: str,
    cache_key: str,
    memo_payload: dict,
) -> None:
    row = {
        "id": f"memo-run-{cache_key[:16]}",
        "assessment_id": assessment_id,
        "prompt_version": PROMPT_VERSION,
        "provider": provider,
        "model": model,
        "tone": tone,
        "cache_key": cache_key,
        "generated_at": utc_now(),
        "memo_json": json.dumps(memo_payload, sort_keys=True),
    }
    statement = sqlite_insert(memo_runs).values(row)
    update_columns = {
        "generated_at": statement.excluded.generated_at,
        "memo_json": statement.excluded.memo_json,
    }
    with engine.begin() as connection:
        connection.execute(statement.on_conflict_do_update(index_elements=[memo_runs.c.cache_key], set_=update_columns))


def cache_meta(hit: bool, key: str) -> CacheMeta:
    return CacheMeta(hit=hit, key=key, source="cache" if hit else "computed")
