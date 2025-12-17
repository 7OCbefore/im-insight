from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class RawMessage:
    """Dataclass representing a raw message from WeChat client."""
    id: str  # Hash of timestamp + sender + content
    content: str
    sender: str
    room: Optional[str]  # None if direct message, room name if group chat
    timestamp: datetime