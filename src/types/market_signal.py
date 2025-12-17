"""
MarketSignal dataclass for IM-Insight processing layer.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class MarketSignal:
    """Represents a processed market signal extracted from a raw message."""
    raw_msg_id: str
    intent: str
    item: Optional[str] = None
    price: Optional[float] = None
    confidence_score: Optional[float] = None