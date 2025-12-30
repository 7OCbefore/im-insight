"""
CSV report generation from SQLite storage.
"""
import csv
import logging
import re
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Iterable, List

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate aggregate, per-group, and temporary goods reports."""

    def __init__(self, db_path: str, output_dir: str, temp_valid_days: int = 7):
        self.db_path = db_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_valid_days = temp_valid_days

    def generate_aggregate_report(self) -> Path:
        rows = self._fetch_signals()
        filename = self._dated_filename("aggregate")
        return self._write_report(filename, rows)

    def generate_group_reports(self) -> List[Path]:
        rows_by_group = {}
        for row in self._fetch_signals():
            group_name = row[1] or "Direct_Message"
            rows_by_group.setdefault(group_name, []).append(row)
        report_paths = []
        for group_name, rows in rows_by_group.items():
            filename = self._dated_filename(f"group_{self._sanitize(group_name)}")
            report_paths.append(self._write_report(filename, rows))
        return report_paths

    def generate_temporary_goods_report(self, goods_whitelist: Iterable[str]) -> Path:
        filtered_rows = self._fetch_signals(goods_whitelist=list(goods_whitelist))
        filename = self._dated_filename("temp_goods")
        report_path = self._write_report(filename, filtered_rows)
        self._cleanup_temp_reports()
        return report_path

    def _fetch_signals(self, goods_whitelist: List[str] = None) -> List[tuple]:
        goods_whitelist = goods_whitelist or []
        query = """
            SELECT timestamp, group_name, sender, item, price
            FROM trade_signals
        """
        params = []
        if goods_whitelist:
            clauses = []
            for item in goods_whitelist:
                clauses.append("LOWER(item) LIKE ?")
                params.append(f"%{item.lower()}%")
            query += " WHERE " + " OR ".join(clauses)
        query += " ORDER BY price DESC, timestamp DESC"

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(query, params)
                return cursor.fetchall()
        except sqlite3.Error as exc:
            logger.error(f"Failed to fetch signals for report: {exc}")
            return []

    def _write_report(self, filename: str, rows: List[tuple]) -> Path:
        file_path = self.output_dir / filename
        try:
            with open(file_path, mode="w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(["Time", "Group", "Sender", "Item", "Price"])
                writer.writerows(rows)
            return file_path
        except OSError as exc:
            logger.error(f"Failed to write report {file_path}: {exc}")
            return file_path

    def _cleanup_temp_reports(self) -> None:
        cutoff = datetime.now(UTC) - timedelta(days=self.temp_valid_days)
        for file_path in self.output_dir.glob("report_temp_goods_*.csv"):
            try:
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime, UTC)
                if mtime < cutoff:
                    file_path.unlink()
            except OSError as exc:
                logger.warning(f"Failed to cleanup temp report {file_path}: {exc}")

    def _dated_filename(self, report_type: str) -> str:
        date_str = datetime.now(UTC).strftime("%Y-%m-%d")
        return f"report_{report_type}_{date_str}.csv"

    @staticmethod
    def _sanitize(value: str) -> str:
        value = re.sub(r"\s+", "_", value.strip())
        value = re.sub(r"[^\w\-]+", "", value)
        return value or "Unknown"


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate CSV reports.")
    parser.add_argument("--db", help="Path to SQLite database (optional if using config)")
    parser.add_argument("--out", help="Output directory for reports (optional if using config)")
    parser.add_argument("--temp-items", nargs="*", help="Temporary goods whitelist override")
    parser.add_argument("--temp-valid-days", type=int, help="Temporary report validity days override")
    parser.add_argument("--use-config", action="store_true", help="Load settings from config")
    args = parser.parse_args()

    if args.use_config:
        from src.config.loader import get_settings

        settings = get_settings()
        db_path = settings.storage.db_path
        output_dir = settings.report.output_dir
        temp_valid_days = settings.report.temp_valid_days
        temp_items = settings.report.temp_goods_whitelist
    else:
        db_path = args.db
        output_dir = args.out
        temp_valid_days = args.temp_valid_days or 7
        temp_items = args.temp_items or []

    if not db_path or not output_dir:
        raise SystemExit("db and out are required unless --use-config is set")

    generator = ReportGenerator(db_path, output_dir, temp_valid_days=temp_valid_days)
    generator.generate_aggregate_report()
    generator.generate_group_reports()
    if temp_items:
        generator.generate_temporary_goods_report(temp_items)
