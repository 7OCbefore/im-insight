"""
Action Dispatcher - CSV Exporter for IM-Insight.
"""

import csv
import logging
from pathlib import Path
from datetime import datetime
from src.types.market_signal import MarketSignal

logger = logging.getLogger(__name__)


class CsvExporter:
    """Exports market signals to CSV files."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.columns = [
            "Time", "Group", "Sender", "Item", "Price", "Raw_Content"
        ]

    def save(self, signal: MarketSignal):
        """
        Save a market signal to the daily CSV log.
        
        Args:
            signal: The MarketSignal to save.
        """
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"market_log_{today}.csv"
        file_path = self.data_dir / filename

        file_exists = file_path.exists()

        try:
            with open(file_path, mode="a", encoding="utf-8-sig",
                      newline="") as f:
                writer = csv.DictWriter(f, fieldnames=self.columns)

                if not file_exists:
                    writer.writeheader()

                # Format time string from datetime object
                time_str = signal.timestamp.strftime(
                    "%Y-%m-%d %H:%M:%S") if isinstance(
                        signal.timestamp, datetime) else str(signal.timestamp)

                row = {
                    "Time": time_str,
                    "Group":
                    signal.group if signal.group else "Direct Message",
                    "Sender": signal.sender,
                    "Item": signal.item if signal.item else "",
                    "Price": signal.price if signal.price is not None else "",
                    "Raw_Content": signal.raw_content
                }

                writer.writerow(row)

        except PermissionError:
            logger.error(
                f"PermissionError: Could not write to {file_path}. Is it open in Excel?"
            )
        except Exception as e:
            logger.error(f"Failed to save signal to CSV: {e}")