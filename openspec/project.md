# Project Context

## Purpose
IM-Insight is a WeChat PC client monitoring system that passively captures chat
messages, filters for trading intent, extracts structured market signals, and
records results to CSV logs for later analysis.

## Tech Stack
- Python 3
- wxauto (WeChat PC client automation)
- pydantic + pydantic-settings (configuration validation)
- httpx + asyncio (LLM API calls)
- PyYAML (settings file)
- CSV logging to local filesystem

## Project Conventions

### Code Style
- PEP 8-ish formatting, type hints where helpful
- Dataclasses for data models (see `src/types`)
- Logging via `logging` module; no print in runtime paths
- Defensive error handling around external dependencies

### Architecture Patterns
- Ingestion -> Processing -> Recording pipeline
- L1 regex filter (whitelist/blacklist) before L2 LLM extraction
- Clear module boundaries: `core/` (ingestion), `engine/` (processing),
  `action/` (record/export), `types/` (dataclasses), `config/` (settings)

### Testing Strategy
- Pytest-based unit tests in `test_*.py`
- Manual integration testing required due to WeChat UI dependency
- Validate configuration loading and message processing paths

### Git Workflow
- TBD: confirm branching strategy and commit message conventions

## Domain Context
- Targets WeChat PC Client v3.9.x, monitoring selected groups
- Messages relate to secondary-market trade signals (buy/sell intent)
- LLM extraction expects JSON output with intent, item name, and price

## Important Constraints
- WeChat client must be running and visible on Windows
- `wxauto` is required and can fail if window state changes
- LLM calls require network access and a valid API key
- Data is logged locally to CSV in `data/`

## External Dependencies
- WeChat PC Client v3.9.x
- `wxauto` library
- OpenAI-compatible LLM API endpoint (configured in `config/settings.yaml`)
