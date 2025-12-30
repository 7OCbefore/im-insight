## ADDED Requirements
### Requirement: Price-Sorted Aggregate Report
The system SHALL generate an Excel-compatible CSV report sorted by price from stored trade signals.

#### Scenario: Aggregate report generation
- **WHEN** an aggregate report is requested
- **THEN** the output is a CSV file sorted by price with core fields (time, group, sender, item, price)

### Requirement: Per-Group Reports
The system SHALL generate per-group CSV reports sorted by price from stored trade signals.

#### Scenario: Group reports generation
- **WHEN** per-group reports are requested
- **THEN** the system produces one CSV per group sorted by price

### Requirement: Temporary Goods Report
The system SHALL generate a temporary CSV report filtered by a configurable goods whitelist.

#### Scenario: Temporary goods filtering
- **WHEN** a temporary goods whitelist is provided
- **THEN** the report includes only signals that match the whitelist

#### Scenario: Temporary report validity
- **WHEN** a temporary report is generated
- **THEN** it is considered valid for 7 days

#### Scenario: Temporary report filename
- **WHEN** a temporary report is generated
- **THEN** the filename includes the report type and generation date

### Requirement: Manual Report Trigger
The system SHALL support manual triggering of report generation.

#### Scenario: Manual run
- **WHEN** an operator runs the report command
- **THEN** reports are generated using current configuration
