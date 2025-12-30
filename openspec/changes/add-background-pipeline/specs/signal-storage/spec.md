## ADDED Requirements
### Requirement: SQLite Persistence
The system SHALL store raw messages and structured trade signals in SQLite.

#### Scenario: Persist raw and signals
- **WHEN** a trade-related message is ingested
- **THEN** raw message data and extracted signals are written to SQLite

### Requirement: Idempotent Storage
The system SHALL prevent duplicate records using a stable unique key per message and per signal.

#### Scenario: Duplicate insert ignored
- **WHEN** the same message is processed twice
- **THEN** SQLite contains only one record for that message

### Requirement: Raw Message Retention
The system SHALL retain raw messages for 60 days in SQLite and remove older raw records.

#### Scenario: Retention cleanup
- **WHEN** a raw message is older than 60 days
- **THEN** it is deleted from raw message storage

### Requirement: Signal Detail Fields
The system SHALL store trade signals with time and group fields to support backtracking to senders.

#### Scenario: Signal contains context
- **WHEN** a signal is persisted
- **THEN** it includes timestamp and group name fields in storage
