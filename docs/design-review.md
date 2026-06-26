# Design Review: Commercial Asset Screening Copilot

## 1. What This System Does

Commercial Asset Screening Copilot is a focused full-stack MVP for first-pass Singapore commercial asset screening. An analyst selects a REIT or trust portfolio asset, reviews issuer-reported valuation metrics and structured market events, then generates a memo grounded in backend-computed facts.

The important design principle is that AI is not the source of truth. The backend owns ingestion, validation, analytics, risk rules, confidence, provenance, and cache/audit records. AI only turns the bounded assessment payload into a memo when configured; otherwise the app returns a deterministic fallback memo.

The backend still retains legacy residential `/sites` endpoints from the earlier vertical slice, but the active product workflow is `/commercial-assets`.

## 2. Architecture At A Glance

```mermaid
flowchart TD
  analyst["Investment Analyst"] --> web["Next.js Frontend"]

  web -->|HTTP via NEXT_PUBLIC_API_BASE_URL| api[FastAPI Backend]

  api --> services["Commercial Assessment + Memo Services"]
  services --> repos["SQLAlchemy Core Repositories"]
  repos --> sqlite[(SQLite local.db)]

  raw["data/raw public-source snapshots"] --> init["db_init / db_reset"]
  init --> sqlite

  services --> cache[("assessment_runs + memo_runs")]
  cache --> sqlite

  services --> assessment["CommercialAssetAssessment"]
  assessment --> memo["Constrained Memo Generator"]
  memo --> ai["Optional OpenAI-Compatible Provider"]
  memo --> fallback["Deterministic Fallback Memo"]

  sqlite --> sources["Source Provenance"]
  sources --> web
```

## 3. Dockerized Local Runtime

```mermaid
flowchart TD
  reviewer["Reviewer / Developer"] --> compose["docker compose up --build"]

  compose --> api["api service: FastAPI on 8000"]
  compose --> web["web service: Next.js on 3000"]

  api --> db[(SQLite local.db)]
  api --> raw["data/raw checked-in snapshots"]
  api --> volume["Docker named volume"]
  db --> volume

  web -->|HTTP| api
  api --> optional_ai["Optional AI provider"]
```

Default reviewer path:

```bash
docker compose up --build
```

SQLite remains the MVP database so reviewers do not need to run a separate database service. Docker Compose provides repeatable Python, Node, and runtime setup.

## 4. Data, Cache, And Provenance

```mermaid
flowchart TD
  raw["data/raw committed snapshots"] --> init["python -m app.scripts.db_init"]

  init --> validate["Validate records and source links"]
  validate --> version["Create data_versions entry"]
  version --> db[(SQLite data/local.db)]

  db --> repo["SQLAlchemy Core repositories"]
  repo --> api["FastAPI endpoints"]

  api --> assess["Commercial assessment service"]
  assess --> acache{"assessment_runs cache hit?"}
  acache -->|yes| cached_assessment["Return cached assessment"]
  acache -->|no| compute["Compute valuation metrics + events + risks"]
  compute --> astore["Store assessment_runs"]
  astore --> cached_assessment

  api --> memo["Memo service"]
  memo --> mcache{"memo_runs cache hit?"}
  mcache -->|yes| generated["Return cached memo"]
  mcache -->|no| fallback_or_ai["Generate AI or fallback memo"]
  fallback_or_ai --> mstore["Store memo_runs"]
  mstore --> generated
```

The data path uses checked-in public-source snapshots so the reviewer run is deterministic. Commercial records include issuer portfolio pages, valuation records, and structured market events with source URLs. HDB and OneMap extracts remain in the repo only to support legacy residential endpoints.

## 5. API Flow

```mermaid
sequenceDiagram
  participant UI as Next.js Frontend
  participant API as FastAPI Backend
  participant DB as SQLite
  participant AI as Optional AI Provider

  UI->>API: GET /commercial-assets
  API->>DB: Load commercial asset summaries
  API-->>UI: ApiEnvelope<{ assets }>

  UI->>API: GET /commercial-assets/{asset_id}/assessment
  API->>DB: Check assessment_runs cache
  alt cache hit
    API-->>UI: ApiEnvelope<{ assessment }> with cache.hit=true
  else cache miss
    API->>DB: Load asset, valuation, market events, sources
    API->>API: Compute metrics, risks, confidence, limitations
    API->>DB: Store assessment_runs
    API-->>UI: ApiEnvelope<{ assessment }> with cache.hit=false
  end

  UI->>API: POST /commercial-assets/{asset_id}/memo
  API->>DB: Load or compute assessment
  API->>DB: Check memo_runs cache
  alt cache hit
    API-->>UI: ApiEnvelope<{ memo, assessmentId }> with cache.hit=true
  else cache miss
    API->>AI: Generate memo if configured
    API->>DB: Store memo_runs
    API-->>UI: ApiEnvelope<{ memo, assessmentId }> with cache.hit=false
  end
```

Primary API surface:

```text
GET  /health
GET  /commercial-assets
GET  /commercial-assets/{asset_id}/assessment
POST /commercial-assets/{asset_id}/memo
```

Legacy API surface still available:

```text
GET  /sites
GET  /sites/{site_id}/assessment
POST /sites/{site_id}/memo
```

## 6. AI Memo Guardrails

```mermaid
flowchart TD
  request["POST /commercial-assets/{asset_id}/memo"] --> assess["Load or compute CommercialAssetAssessment"]
  assess --> payload["Structured assessment payload"]
  payload --> cache{"memo_runs cache hit?"}

  cache -->|yes| cached["Return cached GeneratedMemo"]
  cache -->|no| configured{"AI enabled and configured?"}

  configured -->|no| fallback["Generate deterministic fallback memo"]
  configured -->|yes| prompt["Build guarded JSON prompt"]

  prompt --> ai["Call OpenAI-compatible provider"]
  ai --> parse["Parse JSON"]
  parse --> validate{"Pydantic validation passes?"}

  validate -->|yes| store["Store memo_runs"]
  validate -->|no| fallback

  fallback --> response["Return memo with warning if needed"]
  store --> response
  cached --> response
```

AI is a constrained memo generator, not an autonomous agent. It cannot retrieve data, call tools, change scores, upgrade confidence, invent facts, or hide limitations.

## 7. Frontend Workflow

```mermaid
flowchart LR
  app["Commercial Asset Screening Screen"]

  app --> top["Top Bar"]
  top --> status["Data Version + AI/Fallback + Cache Status"]

  app --> left["Asset Panel"]
  left --> selector["Commercial Asset Selector"]
  left --> issuer["Issuer + Submarket + Reliability"]

  app --> main["Assessment Dashboard"]
  main --> snapshot["Asset Snapshot"]
  main --> valuation["Valuation Metrics"]
  main --> events["Market Events Table"]
  main --> risks["Risks + Assumptions + Limitations"]
  main --> sources["Source Chips"]

  app --> memo["Memo Panel"]
  memo --> generate["Generate Memo Button"]
  memo --> draft["Structured Memo Sections"]
  memo --> usage["Source Usage Note"]
```

The first screen is the product itself: a single dashboard workflow, not a landing page, wizard, or chatbot.

## 8. Key Decisions

| Decision | Why | Tradeoff |
| --- | --- | --- |
| Commercial asset workflow | Better matches the later product pivot and implemented frontend | Residential docs/endpoints become legacy support |
| FastAPI backend + Next.js frontend | Keeps data and AI logic server-side and UI product-focused | Two services instead of one app |
| Docker Compose default runtime | Makes reviewer setup repeatable across machines | Adds Docker files and container lifecycle |
| SQLite local database | Free, local, deterministic, no separate DB service | Not production-scale |
| SQLAlchemy Core | Explicit SQL with a cleaner future Postgres path | Slightly more setup than direct `sqlite3` |
| Public-source asset snapshot | Enables offline reviewer flow with source links | Not exhaustive market coverage |
| Backend rule-based metrics | Explainable, testable, auditable | Simpler than production underwriting |
| SQLite cache/audit tables | Repeatable assessments and memo cache without Redis | Cache invalidation must use versions |
| Optional AI + fallback | Reviewer can run without secrets while still supporting AI | Fallback memo is less expressive |
| Constrained generator, not agent | More consistent for trust-sensitive memo writing | Less autonomous than a full agent |

## 9. Reviewer Context

Approximate time spent was 9-10 hours total. The core working vertical slice was around 6-8 hours; the remaining time went into the commercial-scope pivot, source alignment, Docker and AI-provider setup, tests, GitHub publishing, and reviewer-ready documentation cleanup.

## 10. What To Read Next

* [Product PRD](product.md) for scope, user journey, and product decisions.
* [Deep Technical Design](technical-design.md) for schemas, endpoints, data model, tests, and setup.
