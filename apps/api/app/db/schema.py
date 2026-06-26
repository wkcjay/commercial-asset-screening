from sqlalchemy import Column, Float, Integer, MetaData, Table, Text


metadata = MetaData()

data_versions = Table(
    "data_versions",
    metadata,
    Column("id", Text, primary_key=True),
    Column("label", Text, nullable=False),
    Column("created_at", Text, nullable=False),
    Column("source_hash", Text, nullable=False),
    Column("notes", Text),
)

sources = Table(
    "sources",
    metadata,
    Column("id", Text, primary_key=True),
    Column("label", Text, nullable=False),
    Column("publisher", Text),
    Column("url", Text),
    Column("retrieved_at", Text),
    Column("data_vintage", Text),
    Column("reliability", Text, nullable=False),
    Column("notes", Text),
)

commercial_assets = Table(
    "commercial_assets",
    metadata,
    Column("id", Text, primary_key=True),
    Column("issuer", Text, nullable=False),
    Column("name", Text, nullable=False),
    Column("address", Text),
    Column("country", Text, nullable=False),
    Column("asset_type", Text, nullable=False),
    Column("submarket", Text, nullable=False),
    Column("tenure", Text),
    Column("ownership_interest_percent", Float),
    Column("gross_floor_area_sqm", Float),
    Column("net_lettable_area_sqm", Float),
    Column("net_lettable_area_sqft", Float),
    Column("occupancy_percent", Float),
    Column("number_of_tenants", Integer),
    Column("carpark_lots", Integer),
    Column("source_note", Text),
)

asset_valuations = Table(
    "asset_valuations",
    metadata,
    Column("id", Text, primary_key=True),
    Column("asset_id", Text, nullable=False),
    Column("valuation_amount", Float, nullable=False),
    Column("currency", Text, nullable=False),
    Column("valuation_date", Text, nullable=False),
    Column("valuation_scope", Text, nullable=False),
    Column("valuation_basis", Text),
    Column("source_id", Text),
)

market_events = Table(
    "market_events",
    metadata,
    Column("id", Text, primary_key=True),
    Column("event_date", Text, nullable=False),
    Column("event_type", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("asset_name", Text, nullable=False),
    Column("asset_type", Text, nullable=False),
    Column("submarket", Text, nullable=False),
    Column("buyer", Text),
    Column("seller", Text),
    Column("amount", Float),
    Column("currency", Text),
    Column("stake_percent", Float),
    Column("stake_description", Text),
    Column("area_sqft", Float),
    Column("source_url", Text),
    Column("source_id", Text),
    Column("extraction_confidence", Float, nullable=False),
    Column("needs_review", Integer, nullable=False),
    Column("summary", Text, nullable=False),
    Column("counterparties_json", Text, nullable=False),
)

sites = Table(
    "sites",
    metadata,
    Column("id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("address", Text, nullable=False),
    Column("country", Text, nullable=False),
    Column("district", Text, nullable=False),
    Column("planning_area", Text, nullable=False),
    Column("latitude", Float, nullable=False),
    Column("longitude", Float, nullable=False),
    Column("asset_class", Text, nullable=False),
    Column("tenure", Text),
    Column("land_area_sqm", Float),
    Column("gross_plot_ratio_hint", Float),
)

transactions = Table(
    "transactions",
    metadata,
    Column("id", Text, primary_key=True),
    Column("project_name", Text, nullable=False),
    Column("address", Text, nullable=False),
    Column("country", Text, nullable=False),
    Column("district", Text, nullable=False),
    Column("planning_area", Text, nullable=False),
    Column("latitude", Float, nullable=False),
    Column("longitude", Float, nullable=False),
    Column("transaction_date", Text, nullable=False),
    Column("property_type", Text, nullable=False),
    Column("tenure", Text),
    Column("floor_area_sqm", Float),
    Column("price_sgd", Integer, nullable=False),
    Column("price_psf", Float, nullable=False),
)

amenities = Table(
    "amenities",
    metadata,
    Column("id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("raw_category", Text),
    Column("normalized_category", Text, nullable=False),
    Column("category_confidence", Float),
    Column("category_label_source", Text, nullable=False),
    Column("category_rationale", Text),
    Column("needs_review", Integer, nullable=False),
    Column("latitude", Float, nullable=False),
    Column("longitude", Float, nullable=False),
)

demographics = Table(
    "demographics",
    metadata,
    Column("planning_area", Text, primary_key=True),
    Column("population", Integer),
    Column("resident_households", Integer),
    Column("median_age", Float),
    Column("household_income_band", Text),
    Column("notes_json", Text, nullable=False),
)

planning_contexts = Table(
    "planning_contexts",
    metadata,
    Column("planning_area", Text, primary_key=True),
    Column("zoning", Text),
    Column("gross_plot_ratio", Float),
    Column("height_control", Text),
    Column("master_plan_notes_json", Text, nullable=False),
    Column("professional_verification_required", Integer, nullable=False),
)

record_sources = Table(
    "record_sources",
    metadata,
    Column("record_type", Text, primary_key=True),
    Column("record_id", Text, primary_key=True),
    Column("source_id", Text, primary_key=True),
)

assessment_runs = Table(
    "assessment_runs",
    metadata,
    Column("id", Text, primary_key=True),
    Column("site_id", Text, nullable=False),
    Column("data_version", Text, nullable=False),
    Column("algorithm_version", Text, nullable=False),
    Column("cache_key", Text, nullable=False, unique=True),
    Column("generated_at", Text, nullable=False),
    Column("assessment_json", Text, nullable=False),
)

memo_runs = Table(
    "memo_runs",
    metadata,
    Column("id", Text, primary_key=True),
    Column("assessment_id", Text, nullable=False),
    Column("prompt_version", Text, nullable=False),
    Column("provider", Text, nullable=False),
    Column("model", Text),
    Column("tone", Text, nullable=False),
    Column("cache_key", Text, nullable=False, unique=True),
    Column("generated_at", Text, nullable=False),
    Column("memo_json", Text, nullable=False),
)

ALL_BASE_TABLES = [
    data_versions,
    record_sources,
    market_events,
    asset_valuations,
    commercial_assets,
    planning_contexts,
    demographics,
    amenities,
    transactions,
    sites,
    sources,
]
