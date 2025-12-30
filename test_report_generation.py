import csv
import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory

from src.action.report import ReportGenerator


def _init_db(db_path: Path) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE trade_signals (
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
                created_at TEXT NOT NULL
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO trade_signals
                (id, raw_msg_id, intent, item, price, specs, confidence,
                 group_name, sender, timestamp, raw_content, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                ("1", "r1", "Sell", "飞天茅台", 3000, None, 0.9, "群A", "张三",
                 "2025-01-01 10:00:00", "出飞天 3000", "2025-01-01 10:00:01"),
                ("2", "r2", "Sell", "中华", 800, None, 0.9, "群B", "李四",
                 "2025-01-01 11:00:00", "出中华 800", "2025-01-01 11:00:01"),
                ("3", "r3", "Sell", "飞天茅台", 3500, None, 0.9, "群A", "王五",
                 "2025-01-01 12:00:00", "出飞天 3500", "2025-01-01 12:00:01"),
            ],
        )


def test_report_generation():
    with TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        output_dir = Path(temp_dir) / "reports"
        _init_db(db_path)

        generator = ReportGenerator(str(db_path), str(output_dir), temp_valid_days=7)
        aggregate_path = generator.generate_aggregate_report()
        group_paths = generator.generate_group_reports()
        temp_path = generator.generate_temporary_goods_report(["飞天"])

        assert aggregate_path.exists()
        assert temp_path.exists()
        assert len(group_paths) == 2

        with open(aggregate_path, newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.reader(handle))[1:]
            prices = [float(row[4]) for row in rows]
            assert prices == sorted(prices, reverse=True)

        with open(temp_path, newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.reader(handle))[1:]
            assert all("飞天" in row[3] for row in rows)
