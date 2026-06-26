import argparse
import json
import time
import urllib.parse
import urllib.request
from urllib.error import HTTPError
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.config import PROJECT_ROOT


HDB_RESOURCE_ID = "d_8b84c4ee58e3cfc0ece0d773c8ca6abc"
HDB_DATASET_URL = f"https://data.gov.sg/datasets/{HDB_RESOURCE_ID}/view"
HDB_API_URL = "https://data.gov.sg/api/action/datastore_search"
ONEMAP_SEARCH_URL = "https://www.onemap.gov.sg/api/common/elastic/search"
SQM_TO_SQFT = 10.7639

TOWN_CONFIG = {
    "QUEENSTOWN": {"site_id": "site-queenstown-001", "district": "3", "planning_area": "Queenstown"},
    "TAMPINES": {"site_id": "site-tampines-001", "district": "18", "planning_area": "Tampines"},
    "BISHAN": {"site_id": "site-bishan-001", "district": "20", "planning_area": "Bishan"},
}

AMENITY_QUERIES = {
    "QUEENSTOWN": [
        ("QUEENSTOWN MRT STATION", "MRT Station"),
        ("COMMONWEALTH MRT STATION", "MRT Station"),
        ("QUEENSTOWN PRIMARY SCHOOL", "School"),
        ("ALEXANDRA HOSPITAL", "Healthcare"),
        ("QUEENSWAY SHOPPING CENTRE", "Shopping Centre"),
        ("DAWSON PLACE", "Shopping Centre"),
        ("ALEXANDRA CANAL LINEAR PARK", "Park"),
        ("NTUC FAIRPRICE DAWSON", "Supermarket"),
    ],
    "TAMPINES": [
        ("TAMPINES MRT STATION", "MRT Station"),
        ("TAMPINES BUS INTERCHANGE", "Bus Interchange"),
        ("TAMPINES MALL", "Shopping Centre"),
        ("OUR TAMPINES HUB", "Shopping Centre"),
        ("TAMPINES PRIMARY SCHOOL", "School"),
        ("TAMPINES POLYCLINIC", "Healthcare"),
        ("TAMPINES ECO GREEN", "Park"),
        ("NTUC FAIRPRICE TAMPINES MALL", "Supermarket"),
    ],
    "BISHAN": [
        ("BISHAN MRT STATION", "MRT Station"),
        ("BISHAN BUS INTERCHANGE", "Bus Interchange"),
        ("JUNCTION 8", "Shopping Centre"),
        ("BISHAN ACTIVE PARK", "Park"),
        ("KUO CHUAN PRESBYTERIAN PRIMARY SCHOOL", "School"),
        ("BISHAN POLYCLINIC", "Healthcare"),
        ("NTUC FAIRPRICE JUNCTION 8", "Supermarket"),
        ("BISHAN PUBLIC LIBRARY", "Public Library"),
    ],
}

ABBREVIATIONS = {
    "C'WEALTH": "COMMONWEALTH",
}


def fetch_json(url: str, params: dict[str, str]) -> dict[str, Any]:
    request_url = f"{url}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(request_url, headers={"User-Agent": "site-screening-copilot/1.0"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            if error.code != 429 or attempt == 4:
                raise
            retry_after = error.headers.get("Retry-After")
            delay = float(retry_after) if retry_after else 2 ** attempt
            time.sleep(delay)
    raise RuntimeError(f"Unable to fetch {request_url}")


def fetch_hdb_town_records(town: str, limit: int) -> list[dict[str, Any]]:
    payload = fetch_json(
        HDB_API_URL,
        {
            "resource_id": HDB_RESOURCE_ID,
            "limit": str(limit),
            "sort": "month desc",
            "filters": json.dumps({"town": town}),
        },
    )
    if not payload.get("success"):
        raise RuntimeError(f"HDB query failed for {town}: {payload}")
    return payload["result"]["records"]


def expand_address(value: str) -> str:
    result = value
    for short, full in ABBREVIATIONS.items():
        result = result.replace(short, full)
    return result


def geocode(search_value: str) -> dict[str, Any] | None:
    payload = fetch_json(
        ONEMAP_SEARCH_URL,
        {
            "searchVal": search_value,
            "returnGeom": "Y",
            "getAddrDetails": "Y",
            "pageNum": "1",
        },
    )
    results = payload.get("results") or []
    if not results:
        return None
    return results[0]


def hdb_address(row: dict[str, Any]) -> str:
    return f"{row['block']} {row['street_name']}"


def official_address(result: dict[str, Any], fallback: str) -> str:
    return result.get("ADDRESS") or fallback


def title_case(value: str) -> str:
    return value.replace("_", " ").title()


def build_sources(retrieved_at: str, latest_month: str) -> list[dict[str, Any]]:
    return [
        {
            "id": "src-hdb-resale-official",
            "label": "HDB resale flat prices based on registration date from Jan 2017 onwards",
            "publisher": "Housing & Development Board via data.gov.sg",
            "url": HDB_DATASET_URL,
            "retrieved_at": retrieved_at,
            "data_vintage": f"Jan 2017 to {latest_month}",
            "reliability": "official",
            "notes": "Official public resale transaction dataset. HDB publishes registration month, not exact transaction day; local extracts store the month as YYYY-MM-01 only for ISO sorting.",
        },
        {
            "id": "src-onemap-search-official",
            "label": "OneMap Search API geocoding and amenity address results",
            "publisher": "OneMap Singapore",
            "url": "https://www.onemap.gov.sg/apidocs/search",
            "retrieved_at": retrieved_at,
            "data_vintage": retrieved_at,
            "reliability": "official",
            "notes": "Used to resolve HDB block/street records and named amenities to official coordinates and addresses.",
        },
    ]


def build_extract(raw_data_dir: Path, hdb_limit_per_town: int, max_transactions_per_town: int) -> None:
    retrieved_at = datetime.now(UTC).date().isoformat()
    geocode_cache: dict[str, dict[str, Any] | None] = {}
    sites: list[dict[str, Any]] = []
    transactions: list[dict[str, Any]] = []
    amenities: list[dict[str, Any]] = []
    record_sources: list[dict[str, str]] = []
    latest_month = ""

    for town, config in TOWN_CONFIG.items():
        rows = fetch_hdb_town_records(town, hdb_limit_per_town)
        if rows:
            latest_month = max(latest_month, max(row["month"] for row in rows))

        geocoded_for_town = []
        for row in rows:
            query = expand_address(hdb_address(row))
            if query not in geocode_cache:
                geocode_cache[query] = geocode(query)
                time.sleep(0.35)
            result = geocode_cache[query]
            if result is None:
                continue
            geocoded_for_town.append((row, result))
            if len(geocoded_for_town) >= max_transactions_per_town:
                break

        if not geocoded_for_town:
            raise RuntimeError(f"No geocoded HDB records found for {town}")

        site_row, site_geo = geocoded_for_town[0]
        site_address = official_address(site_geo, hdb_address(site_row))
        sites.append(
            {
                "id": config["site_id"],
                "name": f"{config['planning_area']} Official HDB Reference Site",
                "address": site_address,
                "country": "SG",
                "district": config["district"],
                "planning_area": config["planning_area"],
                "latitude": float(site_geo["LATITUDE"]),
                "longitude": float(site_geo["LONGITUDE"]),
                "asset_class": "residential",
                "tenure": "leasehold",
                "land_area_sqm": None,
                "gross_plot_ratio_hint": None,
            }
        )
        record_sources.append({"record_type": "site", "record_id": config["site_id"], "source_id": "src-hdb-resale-official"})
        record_sources.append({"record_type": "site", "record_id": config["site_id"], "source_id": "src-onemap-search-official"})

        for row, geo in geocoded_for_town:
            area_sqm = float(row["floor_area_sqm"])
            price = int(float(row["resale_price"]))
            transaction_id = f"hdb-{row['_id']}"
            transactions.append(
                {
                    "id": transaction_id,
                    "project_name": f"HDB {title_case(row['flat_type'])} {title_case(expand_address(hdb_address(row)))}",
                    "address": official_address(geo, hdb_address(row)),
                    "country": "SG",
                    "district": config["district"],
                    "planning_area": config["planning_area"],
                    "latitude": float(geo["LATITUDE"]),
                    "longitude": float(geo["LONGITUDE"]),
                    "transaction_date": f"{row['month']}-01",
                    "property_type": "hdb",
                    "tenure": "leasehold",
                    "floor_area_sqm": area_sqm,
                    "price_sgd": price,
                    "price_psf": round(price / (area_sqm * SQM_TO_SQFT), 2),
                }
            )
            record_sources.append({"record_type": "transaction", "record_id": transaction_id, "source_id": "src-hdb-resale-official"})
            record_sources.append({"record_type": "transaction", "record_id": transaction_id, "source_id": "src-onemap-search-official"})

        for index, (query, category) in enumerate(AMENITY_QUERIES[town], start=1):
            result = geocode(query)
            time.sleep(0.35)
            if result is None:
                continue
            amenity_id = f"am-{town.lower()}-{index:03d}"
            amenities.append(
                {
                    "id": amenity_id,
                    "name": result.get("SEARCHVAL") or query,
                    "raw_category": category,
                    "latitude": float(result["LATITUDE"]),
                    "longitude": float(result["LONGITUDE"]),
                }
            )
            record_sources.append({"record_type": "amenity", "record_id": amenity_id, "source_id": "src-onemap-search-official"})

    raw_data_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "sources.json": build_sources(retrieved_at, latest_month),
        "sites.json": sites,
        "transactions.json": transactions,
        "amenities.json": amenities,
        "demographics.json": [],
        "planning_contexts.json": [],
        "record_sources.json": record_sources,
    }
    for filename, data in files.items():
        path = raw_data_dir / filename
        path.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n", encoding="utf-8")

    print(
        f"Wrote official extract to {raw_data_dir}: "
        f"{len(sites)} sites, {len(transactions)} transactions, {len(amenities)} amenities."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh local raw data from official Singapore open-data APIs.")
    parser.add_argument("--raw-data-dir", default=str(PROJECT_ROOT / "data" / "raw"))
    parser.add_argument("--hdb-limit-per-town", type=int, default=40)
    parser.add_argument("--max-transactions-per-town", type=int, default=12)
    args = parser.parse_args()
    build_extract(Path(args.raw_data_dir), args.hdb_limit_per_town, args.max_transactions_per_town)


if __name__ == "__main__":
    main()
