# IM-Insight (Ingestion Layer)

This project implements a WeChat monitoring system that passively captures messages from the WeChat PC Client (v3.9.x) using the `wxauto` library.

## Features

- Passive message collection using `wxauto`
- Defensive error handling for WeChat window states
- Message deduplication to avoid processing duplicates
- Human simulation with random jitter delays
- Structured message data with timestamps and metadata

## Components

### Core Modules

1. **WeChatClient** (`src/core/monitor.py`)
   - Wrapper around `wxauto.WeChat` with error handling
   - Fetches new messages using `GetNextNewMessage()`
   - Handles exceptions gracefully (returns empty list on error)

2. **MessageDeduplicator** (`src/core/monitor.py`)
   - Tracks recently seen messages using a rolling deque
   - Generates unique hashes based on timestamp, sender, and content
   - Prevents duplicate processing of the same messages

3. **RawMessage** (`src/types/message.py`)
   - Dataclass representing a WeChat message
   - Contains: id (hash), content, sender, room, timestamp

### Utilities

- **wait_jitter()**: Adds human-like delays before API calls
- **apply_jitter()**: Decorator for applying jitter to functions

## Installation

```bash
pip install -r requirements.txt
```

Note: Requires WeChat PC Client v3.9.x to be installed and running.

## Usage

```bash
python main.py
```

The program will continuously monitor for new WeChat messages and log them to the console.

## Error Handling

- If the WeChat window is not found or is minimized, the system logs an error and continues
- All external library calls are wrapped in try-except blocks
- The system never crashes due to WeChat errors