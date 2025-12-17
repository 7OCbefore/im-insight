"""
MarketSignal dataclass for IM-Insight processing layer.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class MarketSignal:
    """Represents a processed market signal extracted from a raw message."""
    raw_msg_id: str
    intent: str
    timestamp: datetime
    group: Optional[str]
    sender: str
    raw_content: str
    item: Optional[str] = None
    price: Optional[float] = None
    specs: Optional[str] = None
    confidence_score: Optional[float] = None