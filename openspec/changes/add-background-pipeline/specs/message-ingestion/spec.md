## ADDED Requirements
### Requirement: Background Incremental Ingestion
The system SHALL capture new WeChat messages incrementally without requiring manual UI monitoring.

#### Scenario: Continuous background capture
- **WHEN** the WeChat client is running
- **THEN** the system continues ingesting new messages on a schedule without user attention

### Requirement: Targeted Group Selection
The system SHALL ingest messages only from configured target groups or direct messages.

#### Scenario: Non-target group ignored
- **WHEN** a message arrives from an unconfigured group
- **THEN** the message is skipped from ingestion

### Requirement: Persistent Deduplication
The system SHALL persist a deduplication key or watermark so that reprocessing the same message across restarts is avoided.

#### Scenario: Restart does not duplicate
- **WHEN** the service restarts
- **THEN** previously ingested messages are not reprocessed
