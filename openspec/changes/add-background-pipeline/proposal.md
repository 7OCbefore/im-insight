# Change: Add Background Ingestion, SQLite Storage, and Sorted Excel Reporting

## Why
Current implementation relies on CSV logs and foreground monitoring, which makes incremental capture fragile across restarts and does not provide durable query/reporting workflows. We want a background-friendly pipeline that keeps strong filtering, LLM extraction, and produces structured outputs.

## What Changes
- Add background incremental ingestion that does not require manual watching of the WeChat UI.
- Enforce staged filtering: goods whitelist + intent whitelist before LLM; persistent storage only excludes non-trade messages.
- Persist structured signals and raw messages in SQLite with idempotent inserts.
- Generate Excel-compatible CSV reports sorted by price.
- Strengthen durability: deduplication across runs, error handling, and auditability.

## Impact
- Affected specs: message-ingestion, signal-processing, signal-storage, report-generation
- Affected code: src/core, src/engine, src/action, config, data model definitions
