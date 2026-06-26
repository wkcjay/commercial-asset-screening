# Design Review: Site Screening Copilot

## 1. What This System Does

Site Screening Copilot is a focused full-stack MVP for early-stage Singapore residential site screening. A development analyst selects an official-data-backed HDB reference location, reviews structured evidence, and generates a first-pass memo grounded in backend-computed facts.

The important design principle is that AI is not the source of truth. The backend owns ingestion, validation, analytics, risk rules, confidence, provenance, and cache/audit records. AI only turns the bounded evidence packet into a memo when configured; otherwise the app returns a deterministic fallback memo.

## 2. Architecture At A Glance

```mermaid
flowchart TD
  analyst[Development Analyst] --> web[Next.js Frontend]

  web -->|HTTP via NEXT_PUBLIC_API_BASE_URL| api[FastAPI Backend]

  api --> services[Assessment + Memo Services]
  services --> repos[SQLAlchemy Core Repositories]
  repos --> sqlite[(SQLite local.db)]

  raw[data/raw official extracts] --> init[db_init / db_reset]
  init --> sqlite

  services --> cache[(assessment_runs + memo_runs)]
  cache --> sqlite

  services --> evidence[EvidencePacket]
  evidence --> memo[Constrained Memo Generator]
  memo --> ai[Optional OpenAI-Compatible Provider]
  memo --> fallback[Deterministic Fallback Memo]

  sqlite --> sources[Source Provenance]
  sources --> web
```

## 3. Dockerized Local Runtime

```mermaid
flowchart TD
  reviewer[Reviewer / Developer] --> compose[docker compose up --build]

  compose --> api[api service: FastAPI on 8000]
  compose --> web[web service: Next.js on 3000]

  api --> db[(SQLite local.db)]
  api --> raw[data/raw official extracts]
  api --> volume[Docker named volume]
  db --> volume

  web -->|HTTP| api
  api --> optional_ai[Optional AI provider]
```

Default reviewer path:

```bash
docker compose up --build
```

SQLite remains the MVP database so reviewers do not need to run a separate database service. Docker Compose provides repeatable Python/Node/runtime setup.

## 4. Data, Cache, And Provenance

```mermaid
flowchart TD
  raw[data/raw committed official extracts] --> init[python -m app.scripts.db_init]
  refresh[python -m app.scripts.refresh_official_data] --> raw

  init --> validate[Validate records and source links]
  validate --> normalize[Normalize categories and mark review flags]
  normalize --> version[Create data_versions entry]
  version --> db[(SQLite data/local.db)]

  db --> repo[SQLAlchemy Core repositories]
  repo --> api[FastAPI endpoints]

  api --> assess[Assessment service]
  assess --> acache{assessment_runs cache hit?}
  acache -->|yes| assessment[Return cached assessment]
  acache -->|no| compute[Compute assessment + evidence]
  compute --> astore[Store assessment_runs]
  astore --> assessment

  api --> memo[Memo service]
  memo --> mcache{memo_runs cache hit?}
  mcache -->|yes| generated[Return cached memo]
  mcache -->|no| fallback_or_ai[Generate AI or fallback memo]
  fallback_or_ai --> mstore[Store memo_runs]
  mstore --> generated
```

The data path is hybrid: committed official extracts make the reviewer run deterministic, while `refresh_official_data` can regenerate them from HDB data.gov.sg and OneMap.

## 5. API Flow

```mermaid
sequenceDiagram
  participant UI as Next.js Frontend
  participant API as FastAPI Backend
  participant DB as SQLite
  participant AI as Optional AI Provider

  UI->>API: GET /sites
  API->>DB: Load official reference locations
  API-->>UI: ApiEnvelope<{ sites }>

  UI->>API: GET /sites/{site_id}/assessment
  API->>DB: Check assessment_runs cache
  alt cache hit
    API-->>UI: ApiEnvelope<{ assessment }> with cache.hit=true
  else cache miss
    API->>DB: Load site, comps, amenities, context
    API->>DB: Store assessment_runs
    API-->>UI: ApiEnvelope<{ assessment }> with cache.hit=false
  end

  UI->>API: POST /sites/{site_id}/memo
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

MVP API surface:

```text
GET  /health
GET  /sites
GET  /sites/{site_id}/assessment
POST /sites/{site_id}/memo
```

## 6. AI Memo Guardrails

```mermaid
flowchart TD
  request[POST /sites/{site_id}/memo] --> assess[Load or compute SiteAssessment]
  assess --> evidence[Build EvidencePacket]
  evidence --> cache{memo_runs cache hit?}

  cache -->|yes| cached[Return cached GeneratedMemo]
  cache -->|no| configured{AI enabled and configured?}

  configured -->|no| fallback[Generate deterministic fallback memo]
  configured -->|yes| prompt[Build guarded prompt]

  prompt --> ai[Call AI provider]
  ai --> parse[Parse JSON]
  parse --> validate{Pydantic validation passes?}

  validate -->|yes| guardrails{Guardrail checks pass?}
  validate -->|no| repair[Retry once with repair prompt]

  repair --> parse2[Parse repaired JSON]
  parse2 --> validate2{Valid and safe?}

  validate2 -->|yes| store[Store memo_runs]
  validate2 -->|no| fallback

  guardrails -->|yes| store
  guardrails -->|no| repair

  fallback --> store
  store --> response[Return ApiEnvelope memo]
  cached --> response
```

AI is a constrained memo generator, not an autonomous agent. It cannot retrieve data, call tools, change scores, upgrade confidence, invent facts, or hide limitations.

## 7. Frontend Workflow

```mermaid
flowchart LR
  app[Site Screening Copilot Screen]

  app --> top[Top Bar]
  top --> mode[Data Version + AI/Fallback + Cache Status]

  app --> left[Site Panel]
  left --> selector[Reference Location Selector]
  left --> metadata[Site Metadata]
  left --> reliability[Source Reliability Note]

  app --> main[Assessment Dashboard]
  main --> score[Location Score + Confidence]
  main --> comps[Comparable Metrics + Table]
  main --> amenities[Amenities + Accessibility]
  main --> context[Demographic + Planning Context]
  main --> risks[Risks + Assumptions + Limitations]
  main --> sources[Section Source Chips]

  app --> memo[Memo Panel]
  memo --> generate[Generate Memo Button]
  memo --> draft[Structured Memo Sections]
  memo --> usage[Source Usage Note]
```

The first screen is the product itself: a single dashboard workflow, not a landing page, wizard, or chatbot.

## 8. Key Decisions

| Decision | Why | Tradeoff |
| --- | --- | --- |
| FastAPI backend + Next.js frontend | Keeps data/AI logic server-side and UI product-focused | Two services instead of one app |
| Docker Compose default runtime | Makes reviewer setup repeatable across machines | Adds Docker files and container lifecycle |
| SQLite local database | Free, local, deterministic, no separate DB service | Not production-scale |
| SQLAlchemy Core | Explicit SQL with a cleaner future Postgres path | Slightly more setup than direct `sqlite3` |
| Official HDB reference locations for MVP | Keeps vertical slice strong while avoiding synthetic comparables | Manual location input is deferred |
| Backend rule-based scoring | Explainable, testable, auditable | Simpler than production analytics |
| SQLite cache/audit tables | Repeatable assessments and memo cache without Redis | Cache invalidation must use versions |
| Optional AI + fallback | Reviewer can run without secrets while still supporting AI | Fallback memo is less expressive |
| Constrained generator, not agent | More consistent and safer for trust-sensitive memo writing | Less autonomous than a full agent |

## 9. What To Read Next

* [Product PRD](product.md) for scope, user journey, and product decisions.
* [Deep Technical Design](technical-design.md) for schemas, algorithms, API contracts, tests, and implementation sequencing.
