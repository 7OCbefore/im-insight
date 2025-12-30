## 1. Implementation
- [ ] 1.1 Define SQLite schema for raw messages and trade signals (idempotent keys)
- [ ] 1.2 Add incremental cursor/dedup persistence across runs
- [ ] 1.3 Implement staged filtering (goods whitelist + intent whitelist) before LLM
- [ ] 1.4 Store raw messages and structured signals in SQLite
- [ ] 1.5 Generate Excel-compatible CSV reports (aggregate + per-group + temporary goods whitelist)
- [ ] 1.6 Update configuration for new filters and storage/report paths
- [ ] 1.7 Define temporary goods whitelist config and report filename convention
- [ ] 1.8 Ensure report command reloads config on each manual run

## 2. Tests
- [ ] 2.1 Unit tests for filtering stages and persistence logic
- [ ] 2.2 Report sorting test on sample signals
