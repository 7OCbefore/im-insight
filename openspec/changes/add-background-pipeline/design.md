## Context
We want to combine background-friendly ingestion with the existing L1/L2 pipeline and add durable storage plus sorted reporting.

## Goals / Non-Goals
- Goals:
  - Background incremental capture without manual UI watching
  - Staged filtering before LLM
  - SQLite persistence with idempotency
  - Excel report sorted by price
- Non-Goals:
  - Replacing wxauto with a new WeChat integration
  - Building a full UI or dashboard

## Decisions
- Decision: Use SQLite as the primary persistence layer (raw messages + structured signals).
- Decision: Persist an ingestion watermark/dedup key to guarantee idempotent processing across restarts.
- Decision: Enforce intent whitelist + blacklist before LLM; goods whitelist is only used for temporary reports.
- Decision: Report generation reads from SQLite and writes Excel-compatible CSV sorted by price.
- Decision: Report set includes aggregate, per-group, and temporary goods whitelist reports.
- Decision: Retain raw messages for 60 days; keep structured signals long-term.
- Decision: Limit LLM calls to 60 per minute.
- Decision: Temporary goods whitelist lives in config as a list and drives a one-week report validity window with dated filenames.
- Decision: Reports are manually triggered; each run reloads config for hot-updated temporary whitelist.

## Risks / Trade-offs
- wxauto still depends on WeChat PC client behavior; background-friendly means no manual supervision, not true headless capture.
- LLM output variability requires strict validation and fallback rules.

## Migration Plan
1. Introduce SQLite schema and dual-write from existing pipeline if needed.
2. Switch recorder to SQLite as the source of truth.
3. Add Excel report generation from SQLite.

## Open Questions
- None.
