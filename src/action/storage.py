"""
SQLite storage for raw messages and trade signals.
"""
import hashlib
import logging
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable, Optional

from src.types.message import RawMessage
from src.types.market_signal import MarketSignal

logger = logging.getLogger(__name__)


class SqliteStore:
    """Persist raw messages and trade signals with idempotency."""

    def __init__(self, db_path: str, raw_retention_days: int = 60):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.raw_retention_days = raw_retention_days
        self._conn = sqlite3.connect(self.db_path)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._init_schema()

    def _init_schema(self) -> None:
        with self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS raw_messages (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    room TEXT,
                    timestamp TEXT NOT NULL,
                    ingested_at TEXT NOT NULL,
                    is_trade INTEGER NOT NULL
                )
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS trade_signals (
                    id TEXT PRIMARY KEY,
                    raw_msg_id TEXT NOT NULL,
                    intent TEXT NOT NULL,
                    item TEXT NOT NULL,
                    price REAL,
                    specs TEXT,
                    confidence REAL,
                    group_name TEXT,
                    sender TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    raw_content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(raw_msg_id) REFERENCES raw_messages(id)
                )
                """
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_signals_group ON trade_signals(group_name)"
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_signals_price ON trade_signals(price)"
            )

    def save_raw_message(self, message: RawMessage, is_trade: bool) -> None:
        timestamp = message.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        ingested_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self._conn:
                self._conn.execute(
                    """
                    INSERT OR IGNORE INTO raw_messages
                        (id, content, sender, room, timestamp, ingested_at, is_trade)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        message.id,
                        message.content,
                        message.sender,
                        message.room,
                        timestamp,
                        ingested_at,
                        1 if is_trade else 0,
                    ),
                )
        except sqlite3.Error as exc:
            logger.error(f"Failed to save raw message: {exc}")

    def save_signals(self, signals: Iterable[MarketSignal]) -> None:
        now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
        rows = []
        for signal in signals:
            signal_id = self._signal_id(signal)
            timestamp = (
                signal.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                if isinstance(signal.timestamp, datetime)
                else str(signal.timestamp)
            )
            rows.append(
                (
                    signal_id,
                    signal.raw_msg_id,
                    signal.intent,
                    signal.item or "",
                    signal.price,
                    signal.specs,
                    signal.confidence_score,
                    signal.group,
                    signal.sender,
                    timestamp,
                    signal.raw_content,
                    now,
                )
            )
        if not rows:
            return
        try:
            with self._conn:
                self._conn.executemany(
                    """
                    INSERT OR IGNORE INTO trade_signals
                        (id, raw_msg_id, intent, item, price, specs, confidence,
                         group_name, sender, timestamp, raw_content, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    rows,
                )
        except sqlite3.Error as exc:
            logger.error(f"Failed to save trade signals: {exc}")

    def cleanup_raw_messages(self) -> None:
        try:
            with self._conn:
                self._conn.execute(
                    """
                    DELETE FROM raw_messages
                    WHERE ingested_at < datetime('now', ?)
                    """,
                    (f"-{self.raw_retention_days} days",),
                )
        except sqlite3.Error as exc:
            logger.error(f"Failed to cleanup raw messages: {exc}")

    def close(self) -> None:
        try:
            self._conn.close()
        except sqlite3.Error as exc:
            logger.error(f"Failed to close SQLite connection: {exc}")

    @staticmethod
    def _signal_id(signal: MarketSignal) -> str:
        payload = f"{signal.raw_msg_id}|{signal.intent}|{signal.item}|{signal.price}|{signal.specs}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
