# Commercial Asset Screening Copilot

A take-home assignment for a Digital & AI Product Builder role.

## Overview

Commercial Asset Screening Copilot is a Dockerized full-stack MVP for screening Singapore commercial real estate assets. The current product focuses on REIT portfolio assets, issuer-reported valuations, selected public market events, source provenance, risk flags, and memo generation.

The app does not try to be a final valuation engine. It is a first-pass screening workflow that helps an investment analyst move from fragmented public data to a structured, auditable memo.

The main product decision is to keep AI behind the backend facts. The backend owns data ingestion, SQLite persistence, metrics, source links, confidence, and risk rules. AI, when configured, only drafts a memo from the structured assessment payload. Without an AI key, the backend returns a deterministic fallback memo.

## Product Thinking

For a quick reviewer-facing walkthrough of the architecture and main tradeoffs, start here:

[Read the Design Review](docs/design-review.md)

The product thinking, scope decisions, tradeoffs, and future roadmap are documented here:

[Read the Product PRD](docs/product.md)

The build-oriented architecture, data model, API design, AI grounding approach, and implementation details are documented here:

[Read the Technical Design](docs/technical-design.md)

The original assignment brief is preserved unchanged here:

[Read the Take-Home Brief](docs/take-home-brief-lean.md)

## Problem

ABC Development Group assesses development opportunities and monitors existing real estate assets across residential, retail, and commercial markets. Analysts manually gather issuer facts, transaction headlines, market evidence, source links, risks, assumptions, and memo text.

This process is:

* Slow
* Inconsistent across analysts
* Difficult to audit
* Vulnerable to unsupported AI-generated facts if not controlled

## Current MVP

The implemented MVP is scoped to Singapore commercial asset screening, with office, retail, and mixed-use assets from listed REIT or trust portfolios.

A user selects a commercial asset and receives a structured assessment covering:

* Issuer, asset type, submarket, address, ownership, tenure, NLA, and occupancy where available
* Latest issuer-reported valuation and valuation psf where available
* Attributable value where ownership and valuation basis allow it
* Recent structured market events with buyer, seller, amount, stake, source URL, and review flags
* Missing-data flags, risks, assumptions, limitations, and confidence
* Source links and source reliability
* AI-assisted or fallback memo generation

The first screen is the working product dashboard, not a landing page or chatbot.

## Data

The app runs offline from checked-in raw data under `apps/api/data/raw`.

Current commercial data includes:

* OUE REIT assets with issuer-reported property facts and valuations
* CICT assets with issuer-reported property facts and valuations
* Keppel REIT, Suntec REIT, and MPACT representative assets where issuer identity is loaded and missing valuation fields are surfaced as limitations
* Selected Business Times market-event facts stored as structured records with source links, not article bodies

The repository also still contains HDB and OneMap extracts because the backend retains legacy residential `/sites` endpoints from the earlier vertical slice. These are not the primary frontend workflow.

## Key Product Decision

I intentionally did not build a chatbot-first experience.

For real estate investment workflows, trust and auditability matter more than conversational flexibility. A chatbot-first product risks becoming a generic LLM wrapper. The MVP instead builds the underlying real estate intelligence layer: data model, source provenance, deterministic analytics, risk logic, confidence scoring, and constrained memo generation.

Other interfaces can be added later:

* Chatbot
* Newsletter digest
* Portfolio monitoring alerts
* MCP server
* API access

All of those should reuse the same backend intelligence layer rather than putting business logic inside the AI prompt.

## AI Trust Approach

The AI layer follows a grounded generation pattern:

1. Backend services load and compute structured asset data.
2. The AI receives only the structured assessment payload.
3. The AI returns a schema-validated memo.
4. Missing information is shown as a limitation or diligence item.
5. The memo separates facts, assumptions, risks, and recommendations.

If no AI provider is configured, memo generation still works through a deterministic fallback template.

## Repository Structure

```text
commercial-asset-screening/
  README.md
  LICENSE
  docker-compose.yml
  docs/
    design-review.md
    product.md
    technical-design.md
    take-home-brief-lean.md
  apps/
    api/
      Dockerfile
      app/
      data/
        raw/
        local.db   # generated and ignored
      tests/
    web/
      Dockerfile
      app/
      components/
      lib/
```

## Setup

Expected reviewer flow:

```bash
docker compose up --build
```

Then open:

```text
Frontend: http://localhost:3000
Backend:  http://localhost:8000/health
```

The intended local runtime is a Docker Compose stack with a FastAPI backend, Next.js frontend, and a generated SQLite database volume. Native Python and Node commands are also available for development, but Compose is the default reviewer-safe path.

## Optional AI Memo Provider

The app works without an AI key. By default, memo generation uses the deterministic fallback template and `/health` returns `"aiConfigured": false`.

To test with an AI provider, use any OpenAI-compatible Chat Completions API. Create a local `.env` file at the repository root:

```bash
cp .env.example .env
```

Then fill in:

```env
ENABLE_AI_MEMO=true
AI_PROVIDER=openai-compatible
AI_API_KEY=your_api_key_here
AI_MODEL=your_model_name_here
AI_BASE_URL=https://api.openai.com/v1
```

For non-OpenAI providers, keep `AI_PROVIDER=openai-compatible` and change `AI_BASE_URL` and `AI_MODEL` to the provider's OpenAI-compatible values. Do not commit `.env`; it is ignored by git.

Restart the stack after changing these values:

```bash
docker compose up -d --build
```

When configured successfully, `/health` returns `"aiConfigured": true`, and memo responses show `"provider": "openai-compatible"` and `"usedFallback": false`. If the provider call fails, the backend returns the deterministic fallback memo with a warning instead of breaking the user flow.

## Useful Commands

Backend tests:

```bash
cd apps/api
python -m pytest
```

Frontend type check:

```bash
cd apps/web
npm run lint
```

Frontend production build:

```bash
cd apps/web
npm run build
```

Reset local API database outside Docker:

```bash
cd apps/api
python -m app.scripts.db_reset
```

Clear Dockerized memo and assessment cache:

```bash
docker compose exec -T api python -c "import sqlite3; c=sqlite3.connect('/data/local.db'); c.execute('delete from memo_runs'); c.execute('delete from assessment_runs'); c.commit()"
```

## Notes

This project prioritizes sharp product and technical decisions over feature breadth. The main tradeoff is choosing a narrow, auditable commercial asset-screening workflow instead of a broad AI assistant.
