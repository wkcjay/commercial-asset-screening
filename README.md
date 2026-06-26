# Site Screening Copilot

A take-home assignment for a Digital & AI Product Builder role.

## Overview

Site Screening Copilot is a lightweight AI-powered tool designed to help real estate development teams screen potential development sites faster and more consistently.

The product focuses on early-stage site assessment. It brings together comparable transactions, accessibility, amenities, demographics, zoning or planning context, and uses AI to generate a grounded first-pass investment memo.

The goal is not to replace investment judgment. The goal is to reduce manual research effort, improve consistency across analysts, and make site-screening outputs easier to audit.

## Product Thinking

For a quick reviewer-facing walkthrough of the architecture and main tradeoffs, start here:

[Read the Design Review](docs/design-review.md)

The product thinking, scope decisions, tradeoffs, and future roadmap are documented here:

[Read the Product PRD](docs/product.md)

The build-oriented architecture, data model, API design, AI grounding approach, and implementation plan are documented here:

[Read the Technical Design](docs/technical-design.md)

## Problem

ABC Development Group’s development team currently assesses potential sites by manually gathering fragmented data from different sources. This includes comparable transactions, supply pipeline, demographics, accessibility, zoning, and asset performance.

This process is:

* Slow
* Inconsistent across analysts
* Difficult to audit
* Dependent on individual analyst workflows

AI can improve this workflow, but only if it is grounded in trusted data and used in a controlled way.

## Proposed Solution

The MVP is a structured site-screening copilot.

A user selects an official-data-backed Singapore residential reference location, and the system generates a structured assessment covering:

* Comparable transactions
* Accessibility
* Nearby amenities
* Demographic catchment gaps
* Zoning or planning context gaps
* Key risks and assumptions
* AI-generated site-screening memo

The backend computes structured insights first. The AI layer then summarizes those insights into a memo. The AI is not treated as the source of truth.

## Key Product Decision

I intentionally chose not to build a chatbot-first experience for the MVP.

A chatbot interface can be useful, but in a real estate investment workflow, trust and auditability matter more than conversational flexibility. A chatbot-first product risks becoming a generic LLM wrapper.

Instead, the MVP focuses on the underlying real estate intelligence layer: data ingestion, analytics, scoring, and source-grounded memo generation.

Once that foundation exists, other interfaces can be added later, such as:

* Chatbot
* Telegram-style assistant
* Newsletter digest
* API access
* MCP-based tool server

## MVP Scope

For the take-home, the MVP is scoped to Singapore residential site screening.

This is intentionally narrow so the product can demonstrate:

* Clear user workflow
* Grounded data usage
* Explainable analytics
* AI-assisted memo generation
* Practical engineering tradeoffs

## Out of Scope

The MVP does not attempt to cover:

* All Southeast Asian markets
* All asset classes
* Full financial modelling
* Live paid property datasets
* Final investment decision-making
* Newsletter automation
* MCP integration
* Generic chatbot interaction

These are potential future extensions.

## AI Trust Approach

The AI layer follows a grounded generation pattern:

1. Backend services retrieve and compute structured site data.
2. The AI receives only the structured context.
3. The AI generates a memo using only the provided data.
4. Missing information is shown as a limitation.
5. The memo separates facts, assumptions, risks, and recommendations.

This reduces hallucination risk and makes the output more suitable for decision-support workflows.

## Future Roadmap

Future versions could expose the same real estate intelligence layer through multiple interfaces:

* MCP server for analysts using their own LLM clients
* Weekly market or asset-monitoring newsletter
* Conversational assistant
* Portfolio monitoring alerts
* Regional expansion across Southeast Asia
* More asset classes such as retail and commercial

The key principle is that every interface should reuse the same trusted intelligence layer instead of duplicating business logic inside the AI model.

## Repository Structure

```text
site-screening-copilot/
  README.md
  docker-compose.yml
  docs/
    design-review.md
    product.md
    technical-design.md
  apps/
    web/
      Dockerfile
    api/
      Dockerfile
      data/
        raw/
        local.db   # generated and ignored
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

The intended local runtime is a Docker Compose stack with a FastAPI backend, Next.js frontend, and a generated SQLite database volume. Native Python/Node commands are also available for development, but Compose is the default reviewer-safe path.

### Optional AI memo provider

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

Default data is a checked-in official extract generated from:

* HDB resale flat prices on data.gov.sg
* OneMap Search API geocoding and amenity address results

The app runs offline from `apps/api/data/raw`. To refresh the extract from official APIs:

```bash
cd apps/api
python -m app.scripts.refresh_official_data
python -m app.scripts.db_reset
```

Backend-only development:

```bash
cd apps/api
python -m pip install -r requirements.txt
python -m app.scripts.db_reset
python -m pytest
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend-only development:

```bash
cd apps/web
npm install
npm run dev
```

## Notes

This project prioritizes sharp product and technical decisions over feature completeness.

The main tradeoff is choosing a narrow but trustworthy workflow instead of a broad AI assistant. This is intentional because real estate development decisions require evidence, traceability, and human judgment.
