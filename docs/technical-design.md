# Deep Technical Design: Site Screening Copilot

## 1. Executive Summary

Site Screening Copilot is a full-stack, AI-assisted workflow for early-stage screening of Singapore residential development sites. The system helps a development analyst move from fragmented site data to a structured, evidence-backed investment memo.

The central technical decision is to treat AI as a memo-writing and reasoning layer over controlled backend facts, not as the source of market truth. The backend owns data ingestion, validation, analytics, scoring, risk derivation, source provenance, and confidence calculation. The AI layer receives a bounded assessment payload and must generate a memo only from that payload.

For the take-home MVP, the recommended implementation is a Dockerized two-app architecture: a Python FastAPI backend for data ingestion, SQLite access, analytics, and memo generation, plus a Next.js TypeScript frontend for the analyst workflow. Docker Compose is the default reviewer run path. The backend owns the local SQLite database initialized from checked-in official Singapore extracts, deterministic analytics, optional AI memo generation, fallback template memo generation, and SQLite-backed cache/audit records. The frontend remains focused on site selection, evidence review, and memo presentation.

## 2. Product Interpretation

### 2.1 Problem Being Solved

Development analysts currently spend too much time collecting and normalizing information before they can exercise investment judgment. The work is manual, repetitive, inconsistent across analysts, and difficult to audit.

The product should make the first-pass site-screening workflow faster and more consistent by:

* Gathering site context into one workflow.
* Computing comparable transaction and location signals.
* Surfacing assumptions, risks, and missing data.
* Producing a structured investment memo grounded in visible evidence.

### 2.2 What The Product Is Not

This is not:

* A generic real estate chatbot.
* A replacement for investment committee judgment.
* A valuation engine.
* A full financial model.
* A live market-data platform.
* A legal planning or zoning opinion.

The system is a decision-support tool. Its output should help an analyst decide whether a site is worth further diligence, not whether ABC Development Group should definitively acquire it.

### 2.3 Target MVP User

The primary user is a development analyst or investment manager doing early-stage screening for a Singapore residential development site.

The user needs fast answers to:

* Are there relevant comparable transactions nearby?
* What pricing signal do those comparables imply?
* Is the location accessible by MRT and supported by amenities?
* What demographic or planning context should be considered?
* What risks, limitations, and missing information need further diligence?
* Can I turn the above into a coherent first-pass memo?

## 3. Design Goals

### 3.1 Product Goals

* Deliver a working local product reviewers can run.
* Show a clear analyst workflow from site selection to memo generation.
* Make the data behind each insight visible.
* Keep AI output constrained, auditable, and easy to challenge.
* Demonstrate enough data and analytics thinking to be credible for a real estate team.

### 3.2 Engineering Goals

* Keep the MVP small enough for a 6-8 hour take-home implementation.
* Use strong typing and explicit schemas to protect AI and analytics boundaries.
* Keep business logic out of UI components.
* Make scoring and memo generation deterministic where possible.
* Allow the SQLite-backed local data layer to be replaced later with production adapters.
* Allow future interfaces such as chatbot, MCP, or newsletter to reuse the same intelligence layer.

### 3.3 Trust Goals

* The system should never present AI-generated market facts as source data.
* The memo should clearly state limitations and confidence.
* Each displayed insight should be traceable to source records or rules.
* Synthetic or manually curated data should be labelled as such and should not be used when an official extract is available.
* Missing data should reduce confidence instead of being hidden.

## 4. Non-Goals

For the MVP:

* No paid data integrations.
* No live geocoding dependency required to run locally.
* No user authentication.
* No multi-user collaboration.
* No user-facing saved memo history. `memo_runs` may still persist generated memo payloads for local cache and audit behavior.
* No full pro forma, IRR, residual land value, or sensitivity model.
* No production-grade map engine requirement.
* No support for non-residential asset classes.
* No regional expansion outside Singapore.

For the technical design, these are acknowledged as future extension points rather than first-build requirements.

## 5. Key Assumptions

* The app will be reviewed locally from a Git repository.
* Docker Compose is available for the default reviewer run path.
* Reviewers may not have AI API keys, so the app must run without one.
* Checked-in official extracts are preferred for the default reviewer path and must be loaded into the local database with provenance.
* The MVP focuses on predefined official-data-backed reference locations first; manual location input is a future extension.
* The MVP should demonstrate architecture and judgment more than exhaustive data coverage.
* Singapore residential screening is narrow enough to show credible domain logic.
* The first implementation should prefer deterministic analytics over complex ML.
* The system should be designed so data freshness and source reliability can be improved later.

## 6. Recommended Stack

### 6.1 MVP Stack

Use a Python FastAPI backend with a Next.js TypeScript frontend.

```text
Backend:       Python, FastAPI, Pydantic
Frontend:      Next.js App Router, React, TypeScript
Styling:       Tailwind CSS recommended
Data:          SQLite local database initialized from checked-in official extracts
DB Access:     SQLAlchemy Core repositories
Validation:    Pydantic on backend; TypeScript interfaces on frontend
Testing:       pytest for backend; Playwright optional for frontend smoke test
AI Provider:   OpenAI-compatible chat completion interface behind backend provider
Deployment:    Docker Compose by default; native Python/Node commands optional
```

### 6.2 Why FastAPI + Next.js

FastAPI + Next.js is the right take-home choice because it:

* Keeps the frontend focused on analyst UX.
* Puts ingestion, SQLite access, analytics, and AI orchestration in a Python backend.
* Makes data-processing code easier to test with `pytest`.
* Gives clean API boundaries without requiring production infrastructure.
* Keeps reviewer setup repeatable through Docker Compose while preserving a clean service boundary.

The cost is slightly more setup than a single-app JavaScript design, but the separation better matches this product's data and AI workload. Docker Compose absorbs most runtime setup friction for reviewers.

### 6.3 Alternatives Considered

| Option | Benefit | Cost | Decision |
| --- | --- | --- | --- |
| Next.js only | Fastest local setup, one app | Less natural for data ingestion and Python analytics | Do not use |
| FastAPI + Next.js | Clean backend separation, Python data tooling | Requires service orchestration | Use for MVP |
| Docker Compose runtime | Repeatable setup across reviewer machines | Adds container files and lifecycle commands | Use for MVP |
| Streamlit | Very fast prototype | Weaker product/UI and production architecture signal | Avoid |
| Chatbot-only app | Fast AI demo | Weak trust, poor auditability | Avoid |
| SQLite-first app | Better production shape with low setup overhead | Requires schema and initialization scripts | Use for MVP |
| Postgres-first app | Closest production analogue | Requires a separate database service and more configuration | Defer to production path |

## 7. Architecture Overview

### 7.1 System Context

```text
Development Analyst
  |
  | selects an official-data-backed reference location
  v
Site Screening Web App
  |
  | calls FastAPI over HTTP
  v
FastAPI Assessment Service
  |
  | reads site, transaction, amenity, demographic, planning, and source records
  | computes comparable metrics, location score, risks, limitations, confidence
  v
Structured Site Assessment
  |
  | sent to memo generation service
  v
Grounded Memo Generator
  |
  | optional AI call or deterministic fallback
  v
Screening Memo + Evidence Links
```

### 7.2 Container View

```text
Browser
  React UI
  Site selector
  Assessment dashboard
  Memo panel

Docker Compose Runtime
  web service on port 3000
  api service on port 8000
  SQLite named volume

FastAPI Backend
  HTTP API endpoints
  Assessment orchestration service
  Data repositories
  Analytics services
  AI memo service

Local Data Store
  SQLite local database
  Sites
  Transactions
  Amenities
  Demographics
  Planning records
  Sources

Raw Sample Data
  Downloaded or checked-in source extracts
  Used only during initialization and audit

External AI Provider
  Optional
  Only receives structured assessment context
```

### 7.3 Component View

```text
apps/web
  app/
    page.tsx
  components/
    SiteSelector
    SiteSummary
    ComparablePanel
    LocationScorePanel
    AmenityPanel
    PlanningPanel
    RiskPanel
    MemoPanel
    SourceDrawer
  lib/
    apiClient.ts
    types.ts

apps/api
  app/
    main.py
    api/
      routes.py
    domain/
      schemas.py
      units.py
    data/
      repositories.py
      sqlite_repository.py
      migrations.py
      ingestion.py
      validation.py
    analytics/
      assessment_service.py
      geo.py
      comparable_selection.py
      transaction_metrics.py
      location_scoring.py
      risk_engine.py
      confidence.py
    ai/
      memo_generator.py
      prompt_builder.py
      fallback_memo_generator.py
      output_schema.py
    scripts/
      db_init.py
      db_reset.py
      download_sample_data.py

data/
  raw/
    source extracts and small committed samples
  processed/
    optional normalized intermediate files
  local.db
    generated SQLite database, not committed

```

### 7.4 Runtime Request Flow

```text
GET /sites
  -> SQLite connection
  -> SiteRepository.listSites()
  -> return lightweight site summaries

GET /sites/{site_id}/assessment
  -> validate siteId
  -> SQLite connection
  -> SiteRepository.getSite(siteId)
  -> TransactionRepository.findCandidates(site)
  -> AmenityRepository.findNearby(site)
  -> DemographicRepository.getByPlanningArea(site.planningArea)
  -> PlanningRepository.getByPlanningArea(site.planningArea)
  -> ComparableSelection.rankAndFilter()
  -> TransactionMetrics.compute()
  -> LocationScoring.compute()
  -> RiskEngine.derive()
  -> ConfidenceEngine.compute()
  -> SourceRepository.resolveSourceIds()
  -> return SiteAssessment

POST /sites/{site_id}/memo
  -> rebuild assessment server-side
  -> build EvidencePacket from assessment
  -> if AI configured: call AI provider with schema-constrained prompt
  -> validate generated memo
  -> if invalid or unavailable: use fallback generator
  -> return GeneratedMemoResponse
```

### 7.5 Trust Boundary

The trust boundary is between the analytics layer and the AI provider.

Before the boundary:

* Data is validated.
* Metrics are calculated deterministically.
* Risks and limitations are derived by explicit rules.
* Confidence is calculated by the backend.
* Sources are resolved.

After the boundary:

* The AI may summarize, explain, and structure the memo.
* The AI may not invent facts.
* The AI may not add market data outside the provided payload.
* The AI may not increase the backend-provided confidence level.

## 8. Requirement Traceability

| PRD Requirement | Technical Component | Notes |
| --- | --- | --- |
| Select predefined official reference location | `GET /sites`, `SiteSelector` | Required for MVP |
| Input a site location | `ManualSiteInput` future model | Deferred until sample-site flow is complete |
| Comparable transaction analysis | `ComparableSelection`, `TransactionMetrics`, `ComparablePanel` | Core analytics |
| Accessibility and amenities | `AmenityRepository`, `LocationScoring`, `AmenityPanel` | Rule-based scoring |
| Demographics | `DemographicRepository`, `PlanningContextPanel` | Sample planning-area context |
| Zoning/planning | `PlanningRepository`, `PlanningPanel` | Label as indicative |
| AI memo | `MemoGenerator`, `PromptBuilder`, `MemoPanel` | Must use assessment only |
| Source visibility | `SourceRepository`, `SourceDrawer`, source chips | Critical trust feature |
| Limitations | `RiskEngine`, assessment DTO | Must be visible before memo |
| Local runnable app | Docker Compose, FastAPI backend, Next.js frontend, SQLite initialization, README scripts | Required for take-home |

## 9. Domain Model

### 9.1 Modeling Principles

The shapes below describe API and domain contracts. The backend should implement them as Pydantic models; the frontend should mirror response shapes as TypeScript interfaces.

* Use stable string IDs, not display names, for joins.
* Store distances in kilometers.
* Store land and floor areas in square meters and derive square feet where needed.
* Store prices as integer SGD amounts where possible.
* Store price-per-square-foot as a number because it is already a derived market metric.
* Store dates in ISO `YYYY-MM-DD`.
* Keep source IDs on every data record that contributes to an assessment.
* Distinguish observed data from computed insights.
* Distinguish missing data from zero values.

### 9.2 Site

```ts
type Site = {
  id: string;
  name: string;
  address: string;
  country: "SG";
  region: "Singapore";
  district: string;
  planningArea: string;
  latitude: number;
  longitude: number;
  assetClass: "residential";
  tenure?: "freehold" | "leasehold" | "unknown";
  landAreaSqm?: number;
  grossPlotRatioHint?: number;
  sourceIds: string[];
};
```

### 9.3 Future Manual Site Input

Manual location input is not part of the MVP implementation. The first vertical slice should use predefined Singapore reference locations derived from official HDB and OneMap extracts. This future model is kept to show the intended extension path and should avoid relying on live geocoding during reviewer startup.

```ts
type ManualSiteInput = {
  addressLabel: string;
  planningArea?: string;
  latitude: number;
  longitude: number;
  assetClass: "residential";
  tenure?: "freehold" | "leasehold" | "unknown";
  landAreaSqm?: number;
};
```

Validation rules:

* Latitude and longitude must fall within a Singapore bounding box.
* Asset class must be residential.
* Address label is user-provided and should be displayed as unverified unless matched to an official reference location.
* Missing planning area should add a limitation and lower confidence.

### 9.4 Comparable Transaction

```ts
type ComparableTransaction = {
  id: string;
  projectName: string;
  address: string;
  country: "SG";
  district: string;
  planningArea: string;
  latitude: number;
  longitude: number;
  transactionDate: string;
  propertyType: "condo" | "apartment" | "landed" | "executive-condo";
  tenure?: "freehold" | "leasehold" | "unknown";
  floorAreaSqm?: number;
  priceSgd: number;
  pricePsf: number;
  sourceIds: string[];
};
```

Computed fields should not be stored in the source record:

```ts
type ComparableWithDistance = ComparableTransaction & {
  distanceKm: number;
  recencyMonths: number;
  relevanceScore: number;
  relevanceReasons: string[];
};
```

### 9.5 Amenity

```ts
type Amenity = {
  id: string;
  name: string;
  rawCategory?: string;
  category:
    | "mrt"
    | "bus_interchange"
    | "school"
    | "mall"
    | "park"
    | "healthcare"
    | "supermarket"
    | "employment_node"
    | "other";
  categoryConfidence?: number;
  categoryLabelSource: "rule" | "ai" | "manual";
  needsReview: boolean;
  latitude: number;
  longitude: number;
  sourceIds: string[];
};
```

`rawCategory` preserves the original source value. `category` is the normalized taxonomy used by scoring, filters, and dashboard grouping.

Category normalization happens during ingestion, not during request-time assessment. Obvious labels should be mapped by deterministic rules. AI can assist ambiguous free-text labels, but only if the output includes a normalized category, confidence score, rationale, and review flag.

Computed nearby amenity:

```ts
type NearbyAmenity = Amenity & {
  distanceKm: number;
};
```

### 9.6 Demographic Context

```ts
type DemographicContext = {
  planningArea: string;
  population?: number;
  residentHouseholds?: number;
  medianAge?: number;
  householdIncomeBand?: string;
  notes: string[];
  sourceIds: string[];
};
```

Demographics should be treated as context, not as a precise demand forecast. If synthetic, that must be explicit.

### 9.7 Planning Context

```ts
type PlanningContext = {
  planningArea: string;
  zoning?: "residential" | "commercial" | "mixed-use" | "white" | "unknown";
  grossPlotRatio?: number;
  heightControl?: string;
  masterPlanNotes: string[];
  professionalVerificationRequired: boolean;
  sourceIds: string[];
};
```

Planning context should be framed as indicative. The product should never imply legal certainty.

### 9.8 Source

```ts
type Source = {
  id: string;
  label: string;
  publisher?: string;
  url?: string;
  retrievedAt?: string;
  dataVintage?: string;
  reliability: "official" | "paid" | "manual" | "synthetic" | "seeded" | "sample" | "proxy";
  notes?: string;
};
```

### 9.9 Assessment

The assessment is the canonical product object. The UI and AI should both consume this object.

```ts
type SiteAssessment = {
  assessmentId: string;
  generatedAt: string;
  site: Site;
  scope: {
    market: "Singapore";
    assetClass: "residential";
    mode: "sample-site";
  };
  comparableSummary: ComparableSummary;
  locationScore: LocationScore;
  amenitySummary: AmenitySummary;
  demographicContext?: DemographicContext;
  planningContext?: PlanningContext;
  riskAssessment: RiskAssessment;
  confidence: ConfidenceAssessment;
  assumptions: Assumption[];
  limitations: Limitation[];
  sources: Source[];
};
```

### 9.10 Comparable Summary

```ts
type ComparableSummary = {
  searchRadiusKm: number;
  candidateCount: number;
  selectedCount: number;
  selectedComparables: ComparableWithDistance[];
  excludedCandidateCount: number;
  medianPricePsf?: number;
  minPricePsf?: number;
  maxPricePsf?: number;
  latestTransactionDate?: string;
  trend: {
    label: "rising" | "stable" | "softening" | "insufficient-data";
    basis: string;
    earlierMedianPricePsf?: number;
    recentMedianPricePsf?: number;
    percentChange?: number;
  };
  outlierPolicy: {
    method: "none" | "iqr";
    excludedTransactionIds: string[];
    explanation: string;
  };
};
```

### 9.11 Location Score

```ts
type LocationScore = {
  overall: number;
  transport: number;
  amenities: number;
  catchment: number;
  planningFit: number;
  rating: "strong" | "moderate" | "weak" | "incomplete";
  explanations: string[];
  components: Array<{
    name: string;
    score: number;
    weight: number;
    explanation: string;
  }>;
};
```

### 9.12 Risk, Assumption, and Limitation

```ts
type RiskAssessment = {
  items: RiskItem[];
  overallRiskLevel: "low" | "medium" | "high";
};

type RiskItem = {
  id: string;
  severity: "low" | "medium" | "high";
  category: "data" | "market" | "location" | "planning" | "execution";
  statement: string;
  evidence: string[];
  mitigation?: string;
};

type Assumption = {
  id: string;
  statement: string;
  reason: string;
};

type Limitation = {
  id: string;
  severity: "info" | "warning" | "blocking";
  statement: string;
};
```

### 9.13 Confidence

```ts
type ConfidenceAssessment = {
  level: "high" | "medium" | "low";
  score: number;
  drivers: string[];
  deductions: string[];
};
```

The confidence assessment is computed before AI generation. The AI may explain it but may not override it.

## 10. Data Design

### 10.1 MVP Data Sources

The MVP should use local SQLite as the runtime data store. Raw official extract files are initialization inputs, not the source of truth at request time.

| Dataset | MVP Input | Runtime Table | Required Fields | Production Source Direction |
| --- | --- | --- | --- | --- |
| Sites | Official HDB transaction address + OneMap geocode extract | `sites` | location, planning area, asset class | Internal site pipeline, GIS, CRM |
| Transactions | HDB resale flat prices via data.gov.sg + OneMap geocodes | `transactions` | project, date, price, psf, location | Paid private datasets, government records |
| Amenities | OneMap Search API result extract | `amenities` | raw category, normalized category, name, coordinates | Open data, mapping provider, internal GIS |
| Demographics | Not included until an official source is wired | `demographics` | planning area summary | Government statistical tables |
| Planning | Not included until an official source is wired | `planning_contexts` | zoning, plot ratio, notes | Planning authority data, GIS layers |
| Sources | Official source registry records | `sources`, `record_sources` | label, reliability, vintage | Source registry and data catalog |

The app should still run if live download is unavailable. The default path is checked-in, license-compatible official extracts under `data/raw/`, loaded into SQLite during `python -m app.scripts.db_init`. `python -m app.scripts.refresh_official_data` can regenerate the extract from HDB data.gov.sg and OneMap, but reviewer execution must not depend on network access.

### 10.2 Local Data Initialization Shape

A credible local demo can initialize SQLite with:

* 3 official HDB reference locations in different Singapore residential contexts.
* 20-40 official HDB resale transactions across the relevant planning areas.
* 15-30 OneMap-sourced amenities across MRT, schools, malls, parks, healthcare, and supermarkets.
* Demographic records only when an official source is wired.
* Planning records only when an official source is wired.
* Source records for every imported dataset.

Recommended directory and command layout:

```text
data/
  raw/
    committed small official extracts or downloaded files
  processed/
    optional normalized intermediate files
  local.db
    generated by initialization and ignored by git

python -m app.scripts.db_init
  create SQLite schema
  import raw official records
  normalize records
  validate required joins and source links
  create a data_versions row from source file hashes

python -m app.scripts.db_reset
  remove generated SQLite database
  rerun db_init
```

`db_init` should be idempotent and non-destructive by default. It should create missing schema and upsert deterministic official extract rows. `db_reset` is the explicit destructive local rebuild command.

The goal is not to mimic complete market coverage. The goal is to show a realistic ingestion-to-assessment path and how the system behaves when data is sufficient, partial, or weak.

### 10.3 Data Quality Rules

Run validation at app startup or test time:

* Every record has a stable ID.
* Every source ID resolves to an existing source.
* Coordinates are within Singapore bounds.
* Transaction dates are valid ISO dates.
* Price and price-per-square-foot are positive.
* Amenities preserve raw categories and have supported normalized categories.
* Category confidence is between 0 and 1 when present.
* Low-confidence AI-normalized categories are marked `needs_review`.
* Planning records map to known planning areas.
* Synthetic, sample, or proxy records are labelled clearly if ever introduced.

Validation failures should fail tests and fail local startup in development.

### 10.4 Source Provenance

Every assessment should include:

* Sources used directly by selected comparables.
* Sources used by site metadata.
* Sources used by amenities.
* Sources used by demographic context.
* Sources used by planning context.
* A visible data reliability note.

The UI should show source labels near the relevant section, not only at the bottom of the page.

### 10.5 Data Freshness

For MVP, freshness is mostly descriptive:

```ts
type DataFreshness = {
  newestTransactionDate?: string;
  oldestTransactionDate?: string;
  sourceVintageLabels: string[];
  staleDataWarnings: string[];
};
```

Production should turn this into dataset-level monitoring and warnings.

### 10.6 SQLite-First Local Data Strategy

SQLite is the default MVP data store because it is free, local, and does not require reviewers to configure a separate database service. Docker Compose is still the default runtime wrapper for consistent Python and Node setup. SQLite demonstrates relational modeling, SQL-backed repositories, provenance joins, cache/audit records, and realistic initialization without adding a Postgres container.

Runtime behavior:

* FastAPI endpoints query SQLite-backed repositories.
* Repositories use SQLAlchemy Core, not ad hoc SQL scattered through route handlers.
* Raw files are never read directly by assessment endpoints.
* `local.db` is generated and excluded from git.
* `python -m app.scripts.db_init` creates schema and loads official extract data.
* `python -m app.scripts.db_reset` rebuilds a clean database.
* In Docker, `local.db` is stored in a named volume such as `/data/local.db`.
* Postgres remains the production direction, not the local default.

Why not Postgres by default:

* It adds a separate database service, credentials, and migrations earlier than needed.
* It introduces port, credential, and lifecycle failure modes.
* It is unnecessary for the take-home data volume.

Keep SQL and repository design Postgres-friendly where practical:

* Use clear primary keys.
* Avoid SQLite-only business logic.
* Keep migrations explicit.
* Keep repository interfaces independent from the database driver.

### 10.7 SQLite Schema

```sql
CREATE TABLE data_versions (
  id TEXT PRIMARY KEY,
  label TEXT NOT NULL,
  created_at TEXT NOT NULL,
  source_hash TEXT NOT NULL,
  notes TEXT
);

CREATE TABLE sources (
  id TEXT PRIMARY KEY,
  label TEXT NOT NULL,
  publisher TEXT,
  url TEXT,
  retrieved_at TEXT,
  data_vintage TEXT,
  reliability TEXT NOT NULL,
  notes TEXT
);

CREATE TABLE sites (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  address TEXT NOT NULL,
  country TEXT NOT NULL,
  district TEXT NOT NULL,
  planning_area TEXT NOT NULL,
  latitude REAL NOT NULL,
  longitude REAL NOT NULL,
  asset_class TEXT NOT NULL,
  tenure TEXT,
  land_area_sqm REAL,
  gross_plot_ratio_hint REAL
);

CREATE TABLE transactions (
  id TEXT PRIMARY KEY,
  project_name TEXT NOT NULL,
  address TEXT NOT NULL,
  country TEXT NOT NULL,
  district TEXT NOT NULL,
  planning_area TEXT NOT NULL,
  latitude REAL NOT NULL,
  longitude REAL NOT NULL,
  transaction_date TEXT NOT NULL,
  property_type TEXT NOT NULL,
  tenure TEXT,
  floor_area_sqm REAL,
  price_sgd INTEGER NOT NULL,
  price_psf REAL NOT NULL
);

CREATE TABLE amenities (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  raw_category TEXT,
  normalized_category TEXT NOT NULL,
  category_confidence REAL,
  category_label_source TEXT NOT NULL,
  category_rationale TEXT,
  needs_review INTEGER NOT NULL,
  latitude REAL NOT NULL,
  longitude REAL NOT NULL
);

CREATE TABLE demographics (
  planning_area TEXT PRIMARY KEY,
  population INTEGER,
  resident_households INTEGER,
  median_age REAL,
  household_income_band TEXT,
  notes_json TEXT NOT NULL
);

CREATE TABLE planning_contexts (
  planning_area TEXT PRIMARY KEY,
  zoning TEXT,
  gross_plot_ratio REAL,
  height_control TEXT,
  master_plan_notes_json TEXT NOT NULL,
  professional_verification_required INTEGER NOT NULL
);

CREATE TABLE record_sources (
  record_type TEXT NOT NULL,
  record_id TEXT NOT NULL,
  source_id TEXT NOT NULL,
  PRIMARY KEY (record_type, record_id, source_id)
);

CREATE TABLE assessment_runs (
  id TEXT PRIMARY KEY,
  site_id TEXT NOT NULL,
  data_version TEXT NOT NULL,
  algorithm_version TEXT NOT NULL,
  cache_key TEXT NOT NULL UNIQUE,
  generated_at TEXT NOT NULL,
  assessment_json TEXT NOT NULL
);

CREATE TABLE memo_runs (
  id TEXT PRIMARY KEY,
  assessment_id TEXT NOT NULL,
  prompt_version TEXT NOT NULL,
  provider TEXT NOT NULL,
  model TEXT,
  tone TEXT NOT NULL,
  cache_key TEXT NOT NULL UNIQUE,
  generated_at TEXT NOT NULL,
  memo_json TEXT NOT NULL
);

CREATE INDEX idx_sites_planning_area
  ON sites(planning_area);

CREATE INDEX idx_transactions_planning_area_date
  ON transactions(planning_area, transaction_date);

CREATE INDEX idx_transactions_district_date
  ON transactions(district, transaction_date);

CREATE INDEX idx_amenities_category
  ON amenities(normalized_category);

CREATE INDEX idx_assessment_runs_site_version
  ON assessment_runs(site_id, data_version, algorithm_version);

CREATE INDEX idx_memo_runs_assessment_version
  ON memo_runs(assessment_id, prompt_version, provider, model, tone);
```

### 10.8 Category Normalization

Category normalization is an ingestion concern. Assessment logic should consume `normalized_category`, but source/audit views should preserve `raw_category`.

Normalization precedence:

1. Deterministic rule mapping for obvious labels.
2. AI labeling for ambiguous free-text labels.
3. Manual review for low-confidence or unsupported labels.

AI-assisted category labeling must return structured output:

```ts
type CategoryLabel = {
  normalizedCategory:
    | "mrt"
    | "bus_interchange"
    | "school"
    | "mall"
    | "park"
    | "healthcare"
    | "supermarket"
    | "employment_node"
    | "other";
  confidence: number;
  rationale: string;
  needsReview: boolean;
};
```

Rules:

* Preserve the raw free-text category.
* Auto-accept only high-confidence AI labels, default threshold `0.85`.
* Set `needs_review = true` for low-confidence, unsupported, or contradictory labels.
* Runtime scoring should treat `needs_review` amenities conservatively.
* AI category labeling must not create new source facts; it only maps source text into the fixed taxonomy.

## 11. Assessment Pipeline

### 11.1 Pipeline Overview

```text
Input site
  -> Validate scope
  -> Load site context
  -> Load candidate transactions
  -> Calculate distances and recency
  -> Rank and select comparables
  -> Calculate transaction metrics
  -> Load nearby amenities
  -> Calculate accessibility and amenity scores
  -> Load demographic context
  -> Load planning context
  -> Derive risks, assumptions, and limitations
  -> Compute confidence
  -> Resolve sources
  -> Return assessment
```

### 11.2 Assessment Orchestrator Contract

```ts
type AssessmentService = {
  assessSiteById(siteId: string): Promise<SiteAssessment>;
};
```

The orchestrator should not contain scoring logic directly. It coordinates repositories and analytics modules. Manual-location assessment can be added later behind a separate method once geocoding and planning-area validation are in scope.

### 11.3 Error Behavior

The assessment endpoint should degrade gracefully where possible:

* Missing demographics should produce a limitation, not a failed assessment.
* Missing planning context should produce a limitation and lower confidence.
* No comparables should return an assessment with `selectedCount = 0`, not a server error.
* Invalid site ID should return `404`.
* Out-of-scope asset class should return `422`.
* Unexpected data parsing errors should return `500`.

## 12. Analytics Design

### 12.1 Geospatial Calculation

Use Haversine distance for deterministic MVP calculations.

```ts
type Coordinate = {
  latitude: number;
  longitude: number;
};

type DistanceCalculator = {
  distanceKm(a: Coordinate, b: Coordinate): number;
};
```

For the MVP data volume, calculating distances in memory is fine. Production should use spatial indexes or a GIS-capable database.

### 12.2 Comparable Candidate Generation

Candidate filters:

* Same country.
* Residential asset class.
* Supported property types.
* Within maximum search radius, default 3 km.
* Transaction date within a defined lookback window, default 36 months.

Prefer but do not require:

* Same planning area.
* Same district.
* Similar tenure.
* Similar property type.

If too few comparables exist within the default radius, the system can expand the radius to 5 km and add a limitation.

### 12.3 Comparable Relevance Scoring

Score each candidate from 0 to 100.

```text
relevance =
  35 * distanceScore +
  25 * recencyScore +
  15 * planningAreaScore +
  10 * districtScore +
  10 * tenureScore +
   5 * propertyTypeScore
```

Suggested component scoring:

```text
distanceScore:
  <= 0.5 km: 1.00
  <= 1.0 km: 0.85
  <= 2.0 km: 0.65
  <= 3.0 km: 0.40
  >  3.0 km: 0.20

recencyScore:
  <= 6 months: 1.00
  <= 12 months: 0.85
  <= 24 months: 0.60
  <= 36 months: 0.35
  >  36 months: 0.10

planningAreaScore:
  same planning area: 1.00
  adjacent or similar area: 0.60
  otherwise: 0.20

districtScore:
  same district: 1.00
  otherwise: 0.30

tenureScore:
  same known tenure: 1.00
  one or both unknown: 0.50
  mismatch: 0.25

propertyTypeScore:
  same property type: 1.00
  same broad residential category: 0.60
  otherwise: 0.25
```

Select the top comparables after scoring, with a default maximum of 8. Return relevance reasons so the UI can explain why each comparable was selected.

### 12.4 Outlier Handling

For the MVP, use a simple IQR rule if there are at least 6 selected comparables.

```text
IQR = Q3 - Q1
lowerBound = Q1 - 1.5 * IQR
upperBound = Q3 + 1.5 * IQR
```

Transactions outside the range can be excluded from median and trend calculations but should still be shown as excluded outliers. If there are fewer than 6 comparables, do not apply outlier exclusion and explain that the sample is too small.

### 12.5 Price Metrics

Compute:

* Selected comparable count.
* Candidate count.
* Median price per square foot.
* Min and max price per square foot.
* Interquartile range if enough observations exist.
* Latest transaction date.
* Weighted average price per square foot, optional.

Median should be the primary metric because it is less sensitive to outliers than average.

### 12.6 Trend Logic

Trend should be deliberately simple and explainable.

```text
If selected comparable count < 4:
  trend = insufficient-data

Else:
  Split comparables into earlier and recent periods.
  recent = transactions in latest half of selected date range.
  earlier = transactions in earlier half.
  Compute median psf for each period.
  percentChange = (recentMedian - earlierMedian) / earlierMedian

  if percentChange > 0.05:
    rising
  else if percentChange < -0.05:
    softening
  else:
    stable
```

Trend should always include a `basis` sentence. Example: "Trend is based on median price psf among selected comparables split by transaction date; sample size is limited."

### 12.7 Amenity Catchment

Compute nearby amenities within configured radii.

```text
MRT:           nearest and within 0.8 km / 1.2 km
Schools:       count within 1.0 km
Malls:         count within 1.5 km
Parks:         count within 1.0 km
Healthcare:    count within 1.5 km
Supermarkets:  count within 1.0 km
```

Return both nearest amenities and category counts.

### 12.8 Transport Score

```text
nearest MRT distance:
  <= 0.4 km: 100
  <= 0.8 km: 85
  <= 1.2 km: 65
  <= 1.8 km: 40
  >  1.8 km: 20
  missing: 0
```

Add small bonuses for bus interchange or multiple MRT stations nearby, capped at 100.

### 12.9 Amenity Score

Use diversity and proximity.

```text
amenityScore =
  40 * categoryDiversityScore +
  35 * dailyNeedsScore +
  25 * destinationAmenityScore
```

Definitions:

* `categoryDiversityScore`: share of expected amenity categories represented within catchment.
* `dailyNeedsScore`: presence of supermarket, school, healthcare, and park within relevant radii.
* `destinationAmenityScore`: malls, employment nodes, or major parks within 1.5 km.

### 12.10 Catchment Score

Catchment is not a demand model. It measures whether the system has enough planning-area context to support a narrative.

```text
catchmentScore:
  100 if population, households, median age, and income/context notes present
   75 if three major fields present
   50 if one or two major fields present
   25 if only qualitative notes present
    0 if no demographic context
```

### 12.11 Planning Fit Score

Planning fit should be conservative.

```text
planningFit:
  100 if residential zoning and plot ratio are present
   75 if residential zoning is present but plot ratio missing
   50 if mixed-use/white zoning with residential possibility but unclear specifics
   25 if zoning unknown
    0 if planning context missing or incompatible
```

Planning fit does not mean planning approval is guaranteed.

### 12.12 Overall Location Score

```text
overall =
  0.40 * transport +
  0.30 * amenities +
  0.15 * catchment +
  0.15 * planningFit
```

Rating:

```text
strong:     >= 80
moderate:   60-79
weak:        1-59
incomplete: 0 or critical missing context
```

The UI should display component scores and explanations, not only the overall score.

### 12.13 Risk Engine

Risks should be rule-derived before AI generation.

Example rules:

```text
If selected comparable count < 3:
  High data risk: insufficient nearby comparable evidence.

If latest transaction date older than 12 months:
  Medium market risk: transaction evidence may be stale.

If nearest MRT distance > 1.2 km:
  Medium location risk: weaker rapid transit accessibility.

If planning context missing:
  High planning risk: zoning and plot ratio require verification.

If source reliability includes synthetic, sample, or proxy:
  Medium data risk: sample/proxy data limits investment reliability.

If trend = softening:
  Medium market risk: selected comparables indicate softer recent pricing.
```

Each risk item should include:

* Severity.
* Category.
* Statement.
* Evidence IDs or summary.
* Suggested mitigation.

### 12.14 Assumption Engine

Assumptions should be explicit and stable.

Examples:

* The selected comparables are treated as broadly relevant to the subject site.
* Price-per-square-foot is used as the primary normalized transaction metric.
* Sample planning data is indicative and requires professional verification.
* Accessibility scoring uses straight-line distance, not walking time.
* Demographic context is at planning-area level, not micro-catchment level.

### 12.15 Limitation Engine

Limitations should capture what the system cannot prove.

Examples:

* No live paid transaction feed is connected.
* No current supply pipeline data is included.
* No construction cost, sales velocity, or financial model is included.
* No legal zoning opinion is provided.
* Walking routes and travel times are approximated by distance.
* Sample/proxy data may not represent current market conditions.

### 12.16 Confidence Calculation

Compute confidence as a 0-100 score with deductions.

Start at 100 and subtract:

```text
Comparable count < 3:                 -30
Comparable count 3-4:                 -15
Latest comparable older than 12 mo:    -15
No planning context:                   -25
Planning context missing plot ratio:   -10
No demographic context:                -15
Synthetic data included:               -15
Future manual site input not geocoded: -10
No nearby MRT amenity data:            -10
```

Confidence level:

```text
High:   score >= 80
Medium: score >= 55 and < 80
Low:    score < 55
```

This score is about reliability of the screening output, not attractiveness of the site.

## 13. AI Design

### 13.1 AI Pattern

This product should use structured grounded generation, not open-ended retrieval and not an autonomous agent. The AI component is a constrained memo generator over backend facts.

```text
Structured data and analytics
  -> Evidence packet
  -> Prompt with strict rules
  -> Schema-constrained memo
  -> Validation
  -> UI display with source references
```

The AI is allowed to:

* Summarize facts.
* Explain implications.
* Organize a memo.
* Use cautious investment language.
* Reference risks, assumptions, limitations, and confidence already provided.

The AI is not allowed to:

* Invent transactions.
* Invent zoning or demographic data.
* Use general knowledge as if it were source data.
* Claim certainty over planning approval or valuation.
* Increase backend confidence.
* Change backend scores, risk severity, or source reliability.
* Call tools, retrieve external data, or run multi-step autonomous workflows.
* Hide limitations.

### 13.2 Evidence Packet

Do not send the full UI object blindly. Send a compact evidence packet.

```ts
type EvidencePacket = {
  site: {
    name: string;
    address: string;
    planningArea?: string;
    district?: string;
    assetClass: "residential";
    tenure?: string;
    landAreaSqm?: number;
  };
  comparableEvidence: {
    selectedCount: number;
    medianPricePsf?: number;
    minPricePsf?: number;
    maxPricePsf?: number;
    latestTransactionDate?: string;
    trendLabel: string;
    trendBasis: string;
    comparables: Array<{
      projectName: string;
      transactionDate: string;
      pricePsf: number;
      distanceKm: number;
      relevanceReasons: string[];
    }>;
  };
  locationEvidence: {
    overallScore: number;
    rating: string;
    componentScores: Array<{
      name: string;
      score: number;
      explanation: string;
    }>;
    nearestMrt?: {
      name: string;
      distanceKm: number;
    };
    amenityHighlights: string[];
  };
  demographicEvidence?: {
    planningArea: string;
    summary: string[];
  };
  planningEvidence?: {
    zoning?: string;
    grossPlotRatio?: number;
    notes: string[];
    verificationRequired: boolean;
  };
  risks: RiskItem[];
  assumptions: Assumption[];
  limitations: Limitation[];
  confidence: ConfidenceAssessment;
  sourceLabels: string[];
};
```

The evidence packet strips unnecessary internal fields and reduces the chance that the model focuses on irrelevant implementation details.

### 13.3 Prompt Contract

System prompt responsibilities:

* Define the model role as an analyst drafting a first-pass site-screening memo.
* State that the provided evidence packet is the only allowed factual basis.
* Forbid external facts and unsupported claims.
* Require missing data to be stated as a limitation.
* Require separation of facts, interpretation, risks, assumptions, and recommendation.
* Require valid JSON output.
* Require concise, investment-committee style language.

User prompt responsibilities:

* Provide the evidence packet JSON.
* Provide the output schema.
* Provide confidence instructions.
* Provide recommendation constraints.

### 13.4 Output Schema

```ts
type GeneratedMemo = {
  executiveSummary: string;
  siteContext: string;
  comparableTransactionView: string;
  accessibilityAndAmenities: string;
  demographicContext: string;
  planningContext: string;
  risksAndAssumptions: string;
  recommendation: {
    stance: "proceed-to-further-diligence" | "hold" | "do-not-prioritize";
    rationale: string;
    nextDiligenceSteps: string[];
  };
  confidenceLevel: "high" | "medium" | "low";
  confidenceRationale: string;
  sourceUsageNote: string;
};
```

The schema should be validated with a Pydantic model before returning to the frontend.

### 13.5 Recommendation Rules

The recommendation should be bounded:

* The model may recommend whether to proceed to further diligence.
* The model may not recommend final acquisition.
* Low confidence should prevent a strong positive recommendation.
* Missing planning data should require planning diligence as a next step.
* Synthetic, sample, or proxy data should trigger a source validation step.

Example rule:

```text
If confidence = low:
  stance cannot be proceed-to-further-diligence unless rationale clearly states that this is for data gathering only.
```

### 13.6 Provider Interface

```ts
type MemoGenerator = {
  generateMemo(input: {
    assessment: SiteAssessment;
    tone: "investment-committee" | "plain-language";
  }): Promise<GeneratedMemoResponse>;
};

type GeneratedMemoResponse = {
  memo: GeneratedMemo;
  generation: {
    provider: "openai-compatible" | "fallback";
    model?: string;
    promptVersion: string;
    generatedAt: string;
    groundingSourceIds: string[];
    usedFallback: boolean;
  };
};
```

### 13.7 Fallback Memo Generator

The fallback generator is required for local review.

Behavior:

* Uses deterministic string templates.
* Uses the same `EvidencePacket`.
* Produces the same `GeneratedMemo` schema.
* Marks `provider = "fallback"`.
* Includes a clear note that no AI provider was configured.

This allows the product to remain fully runnable without secrets.

### 13.8 AI Output Validation

Validation steps:

1. Parse model output as JSON.
2. Validate against `GeneratedMemo` schema.
3. Verify confidence level equals backend confidence level.
4. Verify recommendation stance is allowed for the confidence/risk profile.
5. Check for empty required sections.
6. Optionally scan for banned phrases such as "guaranteed", "definitely approved", or "market value is".
7. If validation fails, retry once with a stricter repair prompt.
8. If retry fails, use fallback generator.

### 13.9 Prompt Injection Defense

The main injection risk comes from user-entered address labels or imported text fields. Treat all data fields as untrusted content.

Controls:

* Never place raw user text in the system prompt.
* Serialize evidence as JSON.
* Tell the model that fields may contain untrusted text and must not be treated as instructions.
* Validate output schema.
* Do not allow model output to trigger tools or follow-up data access.
* Do not let the model decide which sources are valid.

### 13.10 AI-Assisted Category Labeling

AI may be used as an ingestion-time normalization assistant for ambiguous amenity categories. It should not be used as runtime evidence for site assessment.

Allowed:

* Map free-text source labels to the fixed amenity taxonomy.
* Return confidence, rationale, and review status.
* Flag ambiguous categories for manual review.

Not allowed:

* Invent amenities.
* Override source coordinates or names.
* Create new category values outside the taxonomy.
* Silently relabel low-confidence records.
* Change runtime assessment conclusions directly.

Implementation should prefer deterministic rules first. AI is only called for records that rules cannot classify confidently. The normalized category, confidence score, label source, rationale, and review flag are persisted in SQLite.

### 13.11 AI Evaluation

Create a small evaluation fixture set:

* Strong site with sufficient data.
* Site with weak transport.
* Site with insufficient comparables.
* Site with missing planning context.
* Site using synthetic-only data.

For each fixture, evaluate:

* Did the memo include all required sections?
* Did it avoid unsupported facts?
* Did it preserve backend confidence?
* Did it mention critical limitations?
* Did the recommendation match guardrails?
* Was source usage visible?

Automated checks can cover structure and guardrails. Human review should cover memo usefulness.

## 14. API Design

### 14.1 API Principles

* FastAPI responses should be typed with Pydantic models and schema-validated.
* Endpoints should return structured errors.
* Memo generation should rebuild the assessment server-side.
* Client-submitted assessment data should never be trusted.
* Endpoints should degrade gracefully for missing optional data.
* The Next.js frontend should call the FastAPI base URL configured by `NEXT_PUBLIC_API_BASE_URL`.
* Business responses should use a typed envelope so the UI can show data version, cache status, request ID, and warnings.

### 14.2 Response Envelope

`GET /health` can return a plain health object for container checks. Business endpoints should return:

```ts
type ApiEnvelopeMeta = {
  requestId: string;
  generatedAt: string;
  dataVersion?: string;
  cache?: {
    hit: boolean;
    key?: string;
    source: "cache" | "computed";
  };
  warnings: string[];
};

type ApiEnvelope<T> = {
  data: T;
  meta: ApiEnvelopeMeta;
};
```

### 14.3 Error Shape

```ts
type ApiError = {
  error: {
    code:
      | "not_found"
      | "validation_error"
      | "out_of_scope"
      | "data_error"
      | "ai_generation_error"
      | "internal_error";
    message: string;
    details?: unknown;
    requestId: string;
  };
};
```

### 14.4 `GET /health`

Returns service status.

```json
{
  "ok": true,
  "version": "local",
  "dataMode": "sqlite",
  "aiConfigured": false
}
```

### 14.5 `GET /sites`

Returns selectable official reference locations.

```ts
type ListSitesResponse = ApiEnvelope<{
  sites: Array<{
    id: string;
    name: string;
    address: string;
    district: string;
    planningArea: string;
    assetClass: "residential";
    dataReliability: "official" | "manual" | "synthetic" | "seeded" | "sample" | "proxy";
  }>;
}>;
```

### 14.6 `GET /sites/{site_id}/assessment`

Returns the canonical site assessment.

```ts
type GetAssessmentResponse = ApiEnvelope<{
  assessment: SiteAssessment;
}>;
```

Status codes:

* `200` success.
* `404` unknown site.
* `422` out of MVP scope.
* `500` unexpected server error.

### 14.7 `POST /sites/{site_id}/memo`

Request:

```ts
type GenerateMemoRequest = {
  tone?: "investment-committee" | "plain-language";
};
```

Response:

```ts
type GenerateMemoResponse = ApiEnvelope<{
  memo: GeneratedMemo;
  assessmentId: string;
  generation: {
    provider: "openai-compatible" | "fallback";
    model?: string;
    promptVersion: string;
    generatedAt: string;
    groundingSourceIds: string[];
    usedFallback: boolean;
  };
}>;
```

Important behavior:

* Rebuild assessment server-side.
* Generate evidence packet server-side.
* Do not accept client-provided memo facts.
* Return fallback memo if AI provider is unavailable.

## 15. Frontend Design

### 15.1 Product Screen

The first screen should be the product itself, not a landing page.

Use Next.js App Router, React, TypeScript, Tailwind CSS, and local components. Recommended layout:

```text
Top bar:
  Product name
  Data mode indicator
  AI/fallback indicator

Left panel:
  Site selector
  Site metadata
  Source reliability note

Main content:
  Score and recommendation readiness
  Comparable transaction summary
  Comparable table
  Accessibility and amenity panel
  Demographic context
  Planning context
  Risks, assumptions, limitations

Right or lower panel:
  Generate Memo button
  Memo sections
  Source usage note
```

### 15.2 UI Components

| Component | Responsibility |
| --- | --- |
| `SiteSelector` | Load sites, select site, show scope |
| `AssessmentHeader` | Site name, planning area, generated time, confidence |
| `ComparableMetrics` | Median psf, range, count, trend |
| `ComparableTable` | Selected comparables and relevance reasons |
| `LocationScorePanel` | Overall and component scores |
| `AmenityList` | Nearest MRT and amenity categories |
| `ContextPanel` | Demographic and planning context |
| `RiskPanel` | Risks, assumptions, limitations |
| `SourceChips` | Section-level source labels |
| `MemoPanel` | Generate, loading, memo display, fallback indicator |

### 15.3 UI State

```ts
type ScreenState =
  | { state: "loading-sites" }
  | { state: "no-site-selected"; sites: SiteSummary[] }
  | { state: "loading-assessment"; siteId: string }
  | { state: "assessment-ready"; assessment: SiteAssessment; meta: ApiEnvelopeMeta }
  | { state: "assessment-error"; error: ApiError };

type MemoState =
  | { state: "idle" }
  | { state: "generating" }
  | { state: "ready"; memo: GeneratedMemo; meta: ApiEnvelopeMeta }
  | { state: "error"; error: ApiError };
```

### 15.4 UX Requirements

* Show loading state for assessment and memo generation.
* Show fallback/AI mode clearly.
* Keep limitations visible before and after memo generation.
* Avoid hiding source labels in a single footer.
* Use clear labels for synthetic, sample, or proxy data.
* Make the memo feel like a draft, not a final decision.
* Do not use a chatbot as the primary interface.

### 15.5 Accessibility

* Use semantic headings.
* Ensure keyboard navigation for site selection and memo generation.
* Use sufficient contrast.
* Do not use color alone to indicate risk.
* Provide text labels for score/risk indicators.

## 16. Security, Privacy, and Safety

### 16.1 MVP Security

* Keep AI API keys server-side only.
* Read secrets from environment variables.
* Do not expose raw prompt text unless explicitly debugging locally.
* Validate all route parameters and request bodies.
* Escape user-entered text in UI rendering.
* Do not expose user-facing saved memo history in the MVP. `memo_runs` may persist generated memo JSON only for local cache and audit behavior.

### 16.2 AI Safety

* Do not allow the AI to call tools.
* Do not let AI retrieve external data.
* Validate schema and guardrail rules.
* Label memo as a first-draft screening memo.
* State that planning and legal details require verification.

### 16.3 Production Additions

* Authentication.
* Role-based access control.
* Audit logging.
* Dataset versioning.
* Prompt versioning.
* Encryption for stored memos.
* User feedback capture.
* Access control for paid data sources.

## 17. Observability and Auditability

### 17.1 MVP Observability

Log:

* Request ID.
* Endpoint.
* Site ID.
* Assessment generation duration.
* Memo generation duration.
* AI provider or fallback.
* AI validation failures.
* Data validation failures.

### 17.2 Assessment Audit Record

Even if not persisted in MVP, design the record shape:

```ts
type AssessmentAuditRecord = {
  assessmentId: string;
  siteId?: string;
  generatedAt: string;
  dataVersion: string;
  algorithmVersion: string;
  sourceIds: string[];
  confidence: ConfidenceAssessment;
};
```

### 17.3 Memo Audit Record

```ts
type MemoAuditRecord = {
  memoId: string;
  assessmentId: string;
  generatedAt: string;
  provider: "openai-compatible" | "fallback";
  model?: string;
  promptVersion: string;
  outputValidationPassed: boolean;
  usedFallback: boolean;
};
```

Production auditability depends on being able to recreate the assessment and memo context later.

## 18. Testing Strategy

### 18.1 Unit Tests

Highest priority:

* Haversine distance calculation.
* Singapore bounding-box validation.
* Comparable candidate filtering.
* Comparable relevance scoring.
* Median price calculation.
* Outlier policy.
* Trend label calculation.
* Transport score.
* Amenity score.
* Planning fit score.
* Confidence deductions.
* Risk rule triggering.
* Evidence packet construction.
* Fallback memo generation.
* Rule-based amenity category normalization.

### 18.2 Contract Tests

* SQLite schema creates successfully from an empty database.
* `python -m app.scripts.db_init` populates required tables.
* `python -m app.scripts.db_reset` rebuilds a clean database.
* Imported records pass Pydantic validation.
* All `record_sources` links resolve.
* `assessment_runs` and `memo_runs` enforce unique cache keys.
* API responses match response schemas.
* AI output schema validation rejects malformed output.
* Memo endpoint returns fallback response when AI is not configured.

### 18.3 Integration Tests

* `GET /sites` returns official reference locations from SQLite.
* `GET /sites/{site_id}/assessment` returns a complete assessment.
* Assessment includes resolved sources.
* Assessment with weak data includes limitations.
* `POST /sites/{site_id}/memo` returns all required memo sections.
* Assessment endpoints do not read raw files directly.
* Assessment and memo requests return cache metadata in the API envelope.

### 18.4 UI Smoke Tests

* App loads.
* User selects a site.
* Assessment dashboard renders.
* Generate memo button works.
* Memo displays confidence and source usage note.

### 18.5 AI Evaluation Tests

For fixture assessments, assert:

* Output is valid JSON.
* Confidence level is unchanged.
* Critical limitations are mentioned.
* No unsupported market facts are introduced.
* Low-confidence cases do not produce overly strong recommendations.

### 18.6 Category Normalization Tests

* Deterministic rules classify common amenity labels.
* AI category output includes normalized category, confidence, rationale, and review flag.
* Low-confidence AI labels are stored as `needs_review`.
* Runtime scoring ignores or downgrades ambiguous categories instead of trusting them silently.

## 19. Performance and Scalability

### 19.1 MVP Performance

The MVP data volume is small. SQLite queries with in-process distance calculation are acceptable.

Expected local performance:

* Site list: under 100 ms.
* Assessment generation: under 500 ms.
* Fallback memo: under 100 ms.
* AI memo: depends on provider, target under 10 seconds.

### 19.2 Scaling Path

As data grows:

* Move from local SQLite to Postgres.
* Add spatial indexing.
* Precompute amenity distances for known sites.
* Cache assessment results by site ID and data version.
* Store transaction aggregates by planning area and period.
* Add background ingestion jobs.
* Add dataset freshness monitoring.

### 19.3 Cache Strategy

For MVP:

* Use SQLite as the persistent local cache and audit store.
* Cache assessments in `assessment_runs`.
* Cache memos in `memo_runs`.
* Do not add Redis for the take-home.
* Do not use TTL-based invalidation for the MVP. Use versioned keys instead.

Cache keys:

```text
assessment cache key =
  siteId + dataVersion + algorithmVersion

memo cache key =
  assessmentId + promptVersion + provider + model + tone
```

`dataVersion` is created during `db_init` from the sample source set. `algorithmVersion` should be a small constant in the assessment service so scoring changes invalidate previous assessment cache rows. `promptVersion` should be a small constant in the memo service so prompt changes invalidate previous memo cache rows.

For production, this can move to Postgres tables, Redis, or a job-backed cache depending on workload. The MVP should keep cache behavior local and visible.

## 20. Deployment and Configuration

### 20.1 Environment Variables

Backend environment:

```text
DATA_MODE=sqlite
SQLITE_DB_PATH=/data/local.db
AI_PROVIDER=openai-compatible
AI_API_KEY=
AI_MODEL=
AI_BASE_URL=
ENABLE_AI_MEMO=false
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://web:3000
API_HOST=0.0.0.0
API_PORT=8000
```

Frontend environment:

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

If `ENABLE_AI_MEMO` is false or `AI_API_KEY` is missing, use fallback generation.

### 20.2 Docker Compose Commands

Docker Compose is the default reviewer run path:

```bash
docker compose up --build
```

Expected services:

```text
web: http://localhost:3000
api: http://localhost:8000
sqlite: generated at /data/local.db inside a named volume
```

The API container should ensure the database exists at startup by running an idempotent initialization path. Reset should be explicit:

```bash
docker compose run --rm api python -m app.scripts.db_reset
```

### 20.3 Optional Native Development Commands

Native commands can remain available for development, but they are not the primary reviewer path.

Backend terminal:

```bash
cd apps/api
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m app.scripts.db_init
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend terminal:

```bash
cd apps/web
npm install
npm run dev
```

Test commands:

```bash
cd apps/api
pytest

cd apps/web
npm run lint
```

### 20.4 Production Direction

If this moved beyond take-home:

* Deploy FastAPI and Next.js as separate services.
* Store operational data in Postgres.
* Store source documents or extracts in object storage.
* Use scheduled ingestion workers.
* Add authentication through an identity provider.
* Add observability through structured logging and tracing.

## 21. Implementation Plan

### 21.1 Build Order

Build a complete vertical slice first.

1. Scaffold repository structure for `apps/api`, `apps/web`, `data/raw`, and Docker Compose.
2. Add Docker Compose with `api`, `web`, and a SQLite named volume.
3. Scaffold FastAPI backend app with config, health endpoint, and SQLAlchemy Core database access.
4. Add SQLite schema, `data_versions`, cache/audit tables, and official raw extracts.
5. Implement Python `db_init` and `db_reset` scripts.
6. Implement ingestion, validation, provenance links, and category normalization.
7. Implement repositories and Pydantic schemas.
8. Implement assessment service for one official reference location.
9. Expose FastAPI endpoints for site list, assessment, and memo generation.
10. Connect Next.js frontend to FastAPI through `NEXT_PUBLIC_API_BASE_URL`.
11. Render the single-dashboard workflow for one site.
12. Add comparable metrics, location score, risks, assumptions, limitations, confidence, and source chips.
13. Add fallback memo generator and memo cache.
14. Add optional OpenAI-compatible memo provider.
15. Add tests, README startup instructions, and design-review link.

### 21.2 Timeboxed Take-Home Plan

For a 6-8 hour implementation:

| Time | Focus | Output |
| --- | --- | --- |
| 0.75 h | Scaffold apps and Docker Compose | `docker compose up --build` starts services |
| 1.0 h | SQLite schema and official extract data | Local database initializes in Docker volume |
| 1.0 h | Ingestion and repositories | Validated SQL-backed data access |
| 1.5 h | Analytics layer | Assessment object |
| 1.0 h | FastAPI endpoints | Site, assessment, memo endpoints |
| 1.25 h | UI dashboard | Analyst workflow connected to API |
| 0.75 h | Memo generation | Fallback plus optional AI |
| 0.75 h | Tests and README | Reviewer-ready repo |

If time runs short, cut manual site input, maps, and live AI first. Do not cut Docker startup, source visibility, limitations, cache correctness, or fallback memo generation.

### 21.3 Minimum Acceptable Demo

The minimum acceptable version:

* Runs through `docker compose up --build`.
* Shows at least two selectable sites.
* Displays comparable metrics and selected transactions.
* Displays location score with component explanations.
* Displays planning/demographic context where available.
* Displays risks, assumptions, and limitations.
* Generates a memo without requiring an API key.
* Shows whether the memo used fallback or AI.

## 22. Risk Register

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Official extract is too narrow | Product credibility suffers | Preserve source provenance, show limitations, and wire additional official sources over time |
| AI invents facts | Trust failure | Evidence packet, prompt rules, schema validation, fallback |
| Scoring feels arbitrary | Analyst distrust | Show component weights and explanations |
| Too much architecture, not enough product | Take-home misses working demo | Build vertical slice first |
| Live AI key unavailable | Demo fails | Fallback memo generator |
| Docker startup fails | Reviewer cannot run demo | Keep Compose simple: web, api, SQLite volume only |
| Local DB initialization fails | Reviewer cannot run demo | Keep `db_init` idempotent and commit small official extracts |
| Planning context overstates certainty | Domain risk | Use indicative language and verification-required flags |
| Manual input creates messy geocoding scope | Time sink | Start with official reference locations |
| UI hides limitations | Trust failure | Display limitations near metrics and memo |

## 23. Architecture Decision Records

### ADR-001: Structured Workflow Over Chatbot

Decision: Use a site-screening dashboard with memo generation rather than a chatbot-first interface.

Reason: Real estate investment workflows require source traceability, comparable review, and visible assumptions. A chatbot hides evidence and makes hallucinations harder to detect.

Consequence: The product is narrower but more trustworthy. Chat can be added later on top of the same assessment service.

### ADR-002: FastAPI Backend With Next.js Frontend

Decision: Build a Python FastAPI backend and a separate Next.js TypeScript frontend.

Reason: The backend is responsible for data ingestion, SQLite access, analytics, scoring, and AI memo generation. Python and FastAPI are a better fit for this data-heavy backend, while Next.js remains a strong fit for the analyst-facing UI.

Consequence: The app has two services and CORS configuration, but Docker Compose keeps reviewer setup simple. The service boundary is clearer and the backend can evolve toward workers, Postgres, and production APIs without moving business logic out of the frontend later.

### ADR-003: SQLite-Backed Official Extracts With Provenance

Decision: Use a generated local SQLite database for MVP runtime data, initialized from downloaded or checked-in official extracts with explicit source reliability labels.

Reason: Live paid data integrations are out of scope and brittle for reviewers. SQLite keeps setup local and free while demonstrating ingestion, schema design, SQL querying, source joins, and reproducible tests.

Consequence: The product must clearly disclose that the default extract covers official HDB resale transactions and OneMap locations, not the full private residential market. `local.db` should be generated locally in the host dev environment or Docker volume rather than committed.

### ADR-004: Rule-Based Analytics Before AI

Decision: Comparable selection, scoring, risk derivation, and confidence are deterministic backend functions.

Reason: These are trust-sensitive calculations. They should be testable and explainable rather than hidden in the model.

Consequence: Scoring is simpler than production analytics, but easier to audit.

### ADR-005: Fallback Memo Generation Required

Decision: Memo generation must work without an AI key.

Reason: Reviewers may not configure secrets. A broken memo button would undermine the demo.

Consequence: The fallback memo is less expressive, but it keeps the product runnable.

### ADR-006: Docker Compose As Default Runtime

Decision: Use Docker Compose as the primary reviewer run path.

Reason: Reviewers should not need to align local Python, Node, and environment setup manually. Compose makes the two-service architecture safer to run across machines.

Consequence: The repo needs container files, but no separate database container is required because SQLite runs in a named volume.

### ADR-007: SQLite Cache And Audit Tables

Decision: Use `assessment_runs` and `memo_runs` as MVP cache/audit tables.

Reason: Cached assessments and memos make repeated reviewer interactions faster and expose useful metadata without adding Redis.

Consequence: Cache invalidation depends on `dataVersion`, `algorithmVersion`, and `promptVersion` being maintained deliberately.

### ADR-008: Official Reference Locations First

Decision: Implement predefined official-data-backed reference location selection first and defer manual location input.

Reason: Manual input quickly creates geocoding, planning-area matching, and validation scope. A strong official-reference-location flow better demonstrates the full site-to-memo workflow without synthetic comparable data.

Consequence: The MVP is narrower, but it is more reliable and easier to finish within the take-home window.

### ADR-009: Constrained Generator Over AI Agent

Decision: Use a constrained memo generator, not a tool-using AI agent.

Reason: Consistency and auditability come from bounded evidence, prompt versioning, JSON schema validation, guardrails, and fallback behavior. Agent autonomy would add unnecessary decision points.

Consequence: The AI layer is less autonomous, but more trustworthy for investment memo drafting.

## 24. Future Architecture

### 24.1 Production Data Platform

Future production version:

```text
Ingestion jobs
  -> raw data lake
  -> validation and normalization
  -> curated real estate warehouse
  -> assessment API
  -> web, MCP, newsletter, chatbot interfaces
```

### 24.2 MCP Server

Expose governed tools:

* `search_comparable_transactions`
* `score_site_accessibility`
* `lookup_planning_context`
* `summarize_demographic_catchment`
* `generate_screening_memo`

The MCP server should return structured data with source IDs. It should not let arbitrary LLM clients bypass the data layer.

### 24.3 Newsletter And Monitoring

A scheduled digest can reuse the same intelligence layer:

* Track new transactions near watched assets.
* Track changes in supply pipeline.
* Track planning updates.
* Summarize weekly market changes.
* Link each item to source records.

### 24.4 Regional Expansion

To expand beyond Singapore:

* Add country-specific planning models.
* Add currency and unit normalization.
* Add source reliability by market.
* Add local amenity category mappings.
* Add market-specific comparable rules.

## 25. Locked MVP Defaults

* Focus on predefined official HDB reference locations first.
* Use Docker Compose as the default reviewer run path.
* Use checked-in official extracts by default, with refresh tooling available.
* Skip map unless the rest of the dashboard is complete.
* Persist memo payloads only in `memo_runs` for cache/audit, not as user-facing memo history.
* Support an OpenAI-compatible provider optionally, with fallback required.
* Use a constrained memo generator, not an autonomous agent.
* Use SQLite cache/audit tables, not Redis.

## 26. Acceptance Criteria

The technical design is successfully implemented when:

* The app runs through `docker compose up --build`.
* The API is healthy at `http://localhost:8000`.
* The frontend is available at `http://localhost:3000`.
* `python -m app.scripts.db_init` creates and populates the SQLite database, either during startup or by documented command.
* The app reads assessment data from SQLAlchemy Core repositories backed by SQLite.
* `assessment_runs` and `memo_runs` provide cache metadata in API envelopes.
* The user can select a Singapore residential official reference location.
* The assessment dashboard loads without an AI key.
* Comparable transactions are selected and explained.
* Median price, price range, and trend are computed.
* Location score is decomposed into understandable components.
* Demographic and planning context appear where available.
* Risks, assumptions, limitations, and confidence are visible.
* Memo generation works with fallback mode.
* Optional AI generation uses only the structured evidence packet.
* The generated memo includes all required sections.
* Source labels are visible in the UI.
* Raw amenity categories are preserved and normalized categories are auditable.
* Unit tests cover the core scoring and assessment logic.
* `README.md` links to `docs/design-review.md`, `docs/product.md`, and this technical design.

## 27. Appendix: Example Prompt Skeleton

```text
System:
You are drafting a first-pass site-screening memo for a real estate development analyst.
Use only the evidence packet supplied by the application.
Do not add external market facts, transactions, planning rules, or demographic facts.
If information is missing, state it as a limitation.
Separate facts from interpretation.
Return valid JSON matching the requested schema.

User:
Evidence packet:
{...}

Return JSON with:
executiveSummary
siteContext
comparableTransactionView
accessibilityAndAmenities
demographicContext
planningContext
risksAndAssumptions
recommendation
confidenceLevel
confidenceRationale
sourceUsageNote
```

## 28. Appendix: Example Assessment Summary

```text
Site: Queenstown Residential Sample
Asset class: Residential
Planning area: Queenstown
Comparable count: 7 selected from 12 candidates within 3 km
Median price: SGD X psf
Trend: stable, based on selected comparable median psf split by transaction date
Location score: 82, strong
Key strengths: MRT proximity, diverse amenities, residential planning context
Key risks: sample/proxy data, no live supply pipeline, planning requires verification
Confidence: medium
```

This summary is the kind of structured evidence the memo generator should explain, not expand with unsupported facts.
