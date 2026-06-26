# PRD: Site Screening Copilot

## 1. Context

ABC Development Group is a regional real estate developer and asset owner across residential, retail, and commercial assets in Southeast Asia.

Today, development teams manually collect fragmented information such as comparable transactions, supply pipeline, demographics, accessibility, zoning, and asset performance before forming an investment view. This process is slow, inconsistent across analysts, and difficult to audit.

The opportunity is to use AI to reduce manual research effort and improve consistency, while keeping the final output grounded in trusted data.

## 2. Problem Statement

Development analysts need a faster and more consistent way to screen potential sites and summarize the key investment considerations.

The current workflow requires analysts to manually gather data from different sources, interpret it, and write a memo. This creates three problems:

1. Time is spent on repetitive data gathering instead of judgment.
2. Different analysts may use different assumptions and formats.
3. AI-generated answers may not be trusted if they are not grounded in source data.

## 3. Target User

The primary user for the MVP is a development analyst or investment manager performing early-stage site screening for a potential residential development site.

This user wants to quickly answer:

* Is this site worth further diligence?
* What comparable transactions support the view?
* How strong is the site’s accessibility and amenity profile?
* What demographic or planning context matters?
* What are the key risks, assumptions, and missing data?

## 4. Product Goal

Build a site-screening copilot that helps a development analyst move from fragmented site data to an evidence-backed investment memo faster.

The product should not replace investment judgment. It should support the analyst by collecting relevant signals, structuring the analysis, surfacing risks, and generating a grounded first-draft memo.

## 5. Non-Goals

For the MVP, the product will not attempt to:

* Cover all Southeast Asian markets.
* Support every asset class.
* Build a generic real estate chatbot.
* Produce a full financial model.
* Make final investment decisions.
* Replace human due diligence.
* Integrate live paid property datasets.
* Build MCP, newsletter, or Telegram interfaces.

These are intentionally left out to keep the MVP focused on a reliable site-screening workflow.

## 6. MVP Scope

The MVP focuses on Singapore residential site screening.

A user can select or input a potential site and receive a structured assessment covering:

* Comparable transactions
* Accessibility
* Nearby amenities
* Demographic catchment
* Zoning or planning context
* Key risks and assumptions
* AI-generated site screening memo

## 7. User Journey

1. User opens the Site Screening Copilot.
2. User selects an official-data-backed reference location or inputs a location.
3. System retrieves relevant site context.
4. System computes structured insights, such as comparable transaction summary and accessibility score.
5. User reviews the dashboard.
6. User clicks “Generate Memo.”
7. AI generates a site-screening memo using only the structured data provided.
8. User reviews the memo, assumptions, limitations, and source references.

## 8. Functional Requirements

### Site Selection

The user should be able to select a predefined official-data-backed reference location or input a site location.

### Comparable Transaction Analysis

The system should show relevant comparable transactions near the selected site, including basic metrics such as transaction count, price range, median price, and recent trend.

### Accessibility and Amenities

The system should provide a simple location score based on nearby transport access, amenities, and distance-based catchment.

### Demographic and Planning Context

The system should display basic demographic and zoning/planning information where available.

### AI Memo Generation

The system should generate a structured memo containing:

* Executive summary
* Comparable transaction view
* Accessibility and amenities
* Demographic context
* Planning/zoning context
* Risks and assumptions
* Recommendation
* Confidence level

## 9. AI and Data Trust Requirements

The AI should not be treated as the source of truth.

The system should first compute structured facts from known data sources. The AI should only summarize and explain the structured data returned by the backend.

The AI should follow these rules:

* Use only the provided structured data.
* Do not invent missing information.
* Clearly state limitations when data is unavailable.
* Separate facts from interpretation.
* Include confidence level and assumptions.
* Make source usage visible to the user.

This design reduces hallucination risk by ensuring the model explains controlled data instead of freely generating market facts.

## 10. Success Metrics

For a real product, success could be measured by:

* Reduction in time needed to produce a first-pass site memo.
* Consistency of memo structure across analysts.
* Analyst trust in generated insights.
* Number of screenings completed per week.
* Percentage of AI-generated memos accepted with minimal edits.
* Frequency of missing or incorrect data flags.

For the take-home MVP, success means:

* The app runs locally.
* The user can select a site and view structured insights.
* The AI memo is grounded in visible data.
* Assumptions and limitations are clearly shown.
* The technical design is extensible.

## 11. Key Product Decision

I considered building a chatbot-style interface, such as a Telegram-like assistant for manual search, questions, and newsletter updates.

However, I would not start with a chatbot-first experience. In real estate investment workflows, trust and auditability matter more than conversational flexibility. A chatbot-first approach risks making the product feel like an LLM wrapper.

The better starting point is a structured site-screening workflow backed by a reliable real estate intelligence layer. Once that foundation exists, chatbot, newsletter, Telegram, API, or MCP interfaces can be added later.

## 12. Future Roadmap

Future extensions could include:

### MCP-Based Tooling

Expose the real estate intelligence layer as an MCP server, allowing analysts to use their own LLM clients while still calling governed tools such as:

* Comparable transaction search
* Zoning lookup
* Accessibility scoring
* Demographic catchment analysis
* Asset performance monitoring
* Weekly market digest generation

This should not be framed as fully removing hallucination. Even with user-owned LLMs, hallucination can still occur at the interpretation layer. The platform’s responsibility is to provide trusted tools, structured responses, source traceability, permissions, and audit logs.

### Newsletter / Asset Monitoring

Add a scheduled digest that summarizes changes in market conditions, asset performance, supply pipeline, or planning updates.

### Chatbot Interface

Add a conversational interface on top of the same backend services, allowing analysts to ask guided questions without bypassing the structured data layer.

### Regional Expansion

Extend the data model to support additional Southeast Asian markets and asset classes.

## 13. Tradeoffs

For the take-home, I would prioritize:

* Trust over conversational flexibility.
* Structured data over broad coverage.
* Clear workflow over feature quantity.
* Explainable scoring over complex black-box AI.
* A narrow but working MVP over an ambitious unfinished platform.

The main tradeoff is that the MVP may feel narrower than a full AI assistant. However, this is intentional. A focused, auditable workflow is more valuable for real estate decision-making than a broad chatbot that users may not trust.
