## ADDED Requirements
### Requirement: Staged Whitelist Filtering
The system SHALL apply intent whitelist and blacklist filters before any LLM call.

#### Scenario: Intent whitelist gate
- **WHEN** a message does not match the intent whitelist
- **THEN** the message is not sent to the LLM

### Requirement: LLM Extraction Validation
The system SHALL validate LLM outputs and discard results without required fields (intent and item).

#### Scenario: Missing fields are dropped
- **WHEN** the LLM response omits intent or item
- **THEN** no structured signal is produced

### Requirement: Trade Relevance Classification
The system SHALL classify messages as trade-related or non-trade-related for persistence decisions.

#### Scenario: Non-trade message
- **WHEN** a message is classified as non-trade
- **THEN** it is excluded from persistent trade signal storage

### Requirement: LLM Rate Limit
The system SHALL limit LLM calls to 60 requests per minute.

#### Scenario: Rate limit reached
- **WHEN** the LLM request rate reaches 60 per minute
- **THEN** additional requests are delayed or skipped with a logged warning

### Requirement: Multi-Item Extraction
The system SHALL support extracting multiple items from a single message into separate signals.

#### Scenario: Multiple goods in one message
- **WHEN** a message contains multiple goods with buy or sell intent
- **THEN** the system creates one signal per extracted item

### Requirement: Temporary Goods Whitelist Configuration
The system SHALL load a temporary goods whitelist from configuration for temporary report filtering.

#### Scenario: Whitelist configured
- **WHEN** a temporary goods whitelist is configured
- **THEN** the system uses it to filter temporary reports

#### Scenario: Hot reload
- **WHEN** the temporary goods whitelist is updated in configuration
- **THEN** the next report run uses the latest whitelist without restarting the service
