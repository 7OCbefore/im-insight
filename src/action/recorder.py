"""
DualTableRecorder for IM-Insight - Silent Recorder implementation.
"""
import csv
import logging
from pathlib import Path
from datetime import datetime
from src.types.market_signal import MarketSignal

logger = logging.getLogger(__name__)


class DualTableRecorder:
    """Records market signals to dual CSV tables: Session Log and Master Log."""

    def _sanitize_text(self, text: str) -> str:
        """
        Sanitize text by flattening control characters and removing whitespaces.

        Transformation: Multi-line text -> Single line with " | " separators

        Args:
            text: Input text (can be None)

        Returns:
            str: Sanitized single-line text
        """
        if text is None:
            return ""

        # Convert to string, replace all CR/LF with separator, strip whitespace
        return str(text).replace('\r', ' | ').replace('\n', ' | ').strip()

    def __init__(self, data_dir: str = "data"):
        """
        Initialize the recorder with dual table strategy.
        
        Args:
            data_dir: Directory for storing CSV files
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Define file paths
        self.session_file = self.data_dir / "session_latest.csv"
        current_month = datetime.now().strftime("%Y-%m")
        self.history_file = self.data_dir / f"history_{current_month}.csv"
        
        # Define CSV headers
        self.headers = ['Time', 'Group', 'Sender', 'Item', 'Price', 'Raw_Content']
        
        # Initialize session file (truncate/overwrite)
        self._init_session_file()
        
        # Initialize history file (append mode, create if not exists)
        self._init_history_file()
        
        # Open file handles
        self.session_fh = open(self.session_file, mode='a', encoding='utf-8-sig', newline='')
        self.history_fh = open(self.history_file, mode='a', encoding='utf-8-sig', newline='')
        
        # Create CSV writers
        self.session_writer = csv.writer(self.session_fh)
        self.history_writer = csv.writer(self.history_fh)

    def _init_session_file(self):
        """Initialize session file with headers."""
        with open(self.session_file, mode='w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(self.headers)

    def _init_history_file(self):
        """Initialize history file with headers if it doesn't exist."""
        if not self.history_file.exists():
            with open(self.history_file, mode='w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(self.headers)

    def save(self, signal: MarketSignal):
        """
        Save a market signal to both session and history logs.

        Args:
            signal: The MarketSignal to save
        """
        try:
            # Format the signal data with sanitization
            time_str = signal.timestamp.strftime("%Y-%m-%d %H:%M:%S") if isinstance(
                signal.timestamp, datetime) else str(signal.timestamp)

            row = [
                time_str,
                # Sanitize group name (may contain control chars)
                self._sanitize_text(signal.group) if signal.group else "Direct Message",
                # Sanitize sender name (may contain control chars)
                self._sanitize_text(signal.sender),
                sanitized_item if (sanitized_item := self._sanitize_text(signal.item)) else "",
                str(signal.price) if signal.price is not None else "",
                # Sanitize raw content (FLATTENING STRATEGY)
                self._sanitize_text(signal.raw_content)
            ]
            
            # Write to both files
            self.session_writer.writerow(row)
            self.history_writer.writerow(row)
            
            # Flush to ensure data is saved even if app crashes
            self.session_fh.flush()
            self.history_fh.flush()
            
        except Exception as e:
            logger.error(f"Failed to save signal to CSV: {e}")

    def close(self):
        """Close file handles."""
        try:
            self.session_fh.close()
            self.history_fh.close()
        except Exception as e:
            logger.error(f"Error closing file handles: {e}")