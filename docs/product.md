# PRD: Commercial Asset Screening Copilot

## 1. Context

ABC Development Group is a regional real estate developer and asset owner across residential, retail, and commercial assets in Southeast Asia.

Development and investment teams need to screen both new opportunities and existing commercial assets. The work often involves collecting issuer disclosures, valuation tables, transaction announcements, market headlines, source links, risks, and memo text from fragmented public and internal sources.

The opportunity is to use AI to reduce manual research effort while keeping the final output grounded in trusted backend data.

## 2. Problem Statement

Investment analysts need a faster and more consistent way to screen commercial assets and produce first-pass investment memos.

The current workflow creates three problems:

1. Time is spent on repetitive data gathering instead of judgment.
2. Different analysts may use different source sets and memo structures.
3. AI-generated answers are not trusted if they are not grounded in source data.

## 3. Target User

The primary MVP user is an investment analyst, asset manager, or development manager performing first-pass screening of a Singapore commercial asset.

This user wants to quickly answer:

* What asset is being screened, who owns it, and where is it located?
* What is the latest reported valuation and valuation psf?
* Is the valuation based on 100% asset value or an owned-interest basis?
* What recent market events in the same submarket or asset type are relevant?
* Which buyer, seller, amount, stake, and source link support each event?
* What data is missing before this can become committee-ready?
* Can the evidence be turned into a coherent first-pass memo?

## 4. Product Goal

Build a commercial asset-screening copilot that turns structured public-source data into a consistent, auditable first-pass memo.

The product should not replace investment judgment or formal valuation. It should support analysts by structuring evidence, exposing source links, surfacing missing fields, deriving risks, and producing a grounded draft memo.

## 5. Non-Goals

For the MVP, the product will not attempt to:

* Cover every Southeast Asian market.
* Cover every commercial asset class.
* Replace formal valuation or appraisal.
* Calculate NAV, cap rates, IRR, NPI yield, or financing metrics without the required issuer data.
* Scrape or bypass paywalled article bodies.
* Integrate live paid transaction databases.
* Make final investment decisions.
* Build a generic real estate chatbot.
* Build MCP, newsletter, or Telegram interfaces.

These are future extension points once the evidence layer is stronger.

## 6. MVP Scope

The implemented MVP focuses on Singapore commercial asset screening, using a curated public-source snapshot of office, retail, and mixed-use assets from listed REIT or trust portfolios.

The user selects a commercial asset and receives a structured assessment covering:

* Issuer and asset identity
* Asset type and Singapore submarket
* Address, tenure, ownership, NLA, occupancy, tenants, and carpark lots where available
* Latest reported valuation and valuation psf where available
* Attributable valuation when ownership and valuation basis allow it
* Structured market events with buyer, seller, amount, stake, and source link
* Missing-data flags
* Risks, assumptions, limitations, confidence, and source provenance
* AI-generated or deterministic fallback memo

The backend still exposes legacy residential `/sites` endpoints from the earlier implementation slice, but the current frontend and product scope are commercial assets.

## 7. User Journey

1. User opens the Commercial Asset Screening Copilot.
2. User selects a Singapore commercial asset from the asset list.
3. System retrieves asset details, valuation data, market events, source links, and missing fields.
4. System computes valuation psf, attributable valuation, event relevance, risks, and confidence.
5. User reviews the dashboard and source chips.
6. User clicks "Generate Memo."
7. The backend returns either an OpenAI-compatible AI memo or a deterministic fallback memo.
8. User reviews the memo, assumptions, limitations, confidence, and source references.

## 8. Functional Requirements

### Asset Selection

The user should be able to select a predefined Singapore commercial asset from the local dataset.

### Valuation Metrics

The system should show latest reported valuation, valuation date, valuation scope, valuation psf, attributable value, NLA, occupancy, and ownership where available.

### Market Events

The system should show relevant structured market events, including event date, event type, asset name, submarket, buyer, seller, amount, stake, review flag, and source URL.

### Risk And Confidence

The system should derive risks before memo generation. Missing valuation, NLA, occupancy, same-submarket events, partial ownership, and narrative-source extraction should affect risk and confidence.

### Source Provenance

Every loaded asset, valuation, and market event should be connected to a source record. Source links should be visible in the UI.

### Memo Generation

The system should generate a structured memo containing:

* Executive summary
* Asset context
* Market evidence
* Operating context
* Planning or title context where available
* Risks and assumptions
* Recommendation
* Confidence level
* Source usage note

## 9. AI And Data Trust Requirements

The AI should not be treated as the source of truth.

The backend computes structured facts first. The AI receives only the computed assessment payload and should only summarize, explain, and organize that data.

The AI should follow these rules:

* Use only the provided structured data.
* Do not invent missing facts, source names, buyers, sellers, amounts, or dates.
* Clearly state limitations when data is unavailable.
* Separate facts from interpretation.
* Preserve backend confidence and limitations.
* Return schema-valid JSON.

If the AI provider is not configured or fails, the deterministic fallback memo keeps the workflow usable.

## 10. Success Metrics

For a real product, success could be measured by:

* Reduction in time needed to produce a first-pass commercial asset memo.
* Consistency of memo structure across analysts.
* Analyst trust in source-grounded insights.
* Number of assets screened per week.
* Percentage of AI-generated memos accepted with minimal edits.
* Frequency of missing or incorrect data flags caught before committee use.

For the take-home MVP, success means:

* The app runs locally with Docker Compose.
* The user can select a commercial asset and view structured insights.
* Valuation and market-event evidence is visible and source-linked.
* Missing data is explicit rather than hidden.
* Memo generation works without an AI key.
* The architecture is extensible.

## 11. Key Product Decision

I considered building a chatbot-first interface. I would not start there.

In real estate investment workflows, trust and auditability matter more than conversational flexibility. A chatbot-first approach risks making the product feel like a generic LLM wrapper. The better starting point is a structured screening workflow backed by a reliable intelligence layer.

Once that foundation exists, chatbot, newsletter, API, or MCP interfaces can be added without duplicating business logic inside prompts.

## 12. Future Roadmap

Future extensions could include:

* More issuer coverage and automated portfolio table extraction.
* SGX announcement ingestion.
* NAV, NPI, debt, yield, cap-rate, and unit-level REIT analytics.
* Lease expiry, top tenant, WALE, and tenant concentration fields.
* Live market-event monitoring and weekly digest generation.
* MCP server exposing governed commercial real estate tools.
* Conversational assistant over the same backend evidence layer.
* Regional expansion across Southeast Asia.

## 13. Tradeoffs

For the take-home, I prioritized:

* Trust over broad coverage.
* Structured data over open-ended retrieval.
* Explainable metrics over black-box scoring.
* Source visibility over polished but unsupported answers.
* A narrow working product over an ambitious unfinished platform.

The main tradeoff is that the data snapshot is incomplete for some issuers. The product handles that by showing null fields, limitations, and confidence deductions rather than fabricating values.
