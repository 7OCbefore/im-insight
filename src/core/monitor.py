import random
import hashlib
import logging
from collections import deque
from datetime import datetime
from typing import List, Dict, Any, Optional
from functools import wraps

# Local imports
from src.types.message import RawMessage
from src.config.loader import get_settings

# Configure logger
logger = logging.getLogger(__name__)


def wait_jitter():
    """Helper function to simulate human-like delays."""
    import time
    delay = random.uniform(0.5, 1.5)
    time.sleep(delay)


def apply_jitter(func):
    """Decorator to apply jitter before function execution."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        wait_jitter()
        return func(*args, **kwargs)
    return wrapper


class MessageDeduplicator:
    """Handles deduplication of messages using a rolling window."""
    
    def __init__(self, maxlen: int = 1000):
        self.seen_hashes = deque(maxlen=maxlen)
    
    def _generate_hash(self, timestamp: datetime, sender: str, content: str) -> str:
        """Generate a unique hash for a message."""
        hash_input = f"{timestamp.isoformat()}{sender}{content}"
        return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
    
    def is_duplicate(self, timestamp: datetime, sender: str, content: str) -> bool:
        """Check if a message is a duplicate."""
        msg_hash = self._generate_hash(timestamp, sender, content)
        if msg_hash in self.seen_hashes:
            return True
        else:
            self.seen_hashes.append(msg_hash)
            return False
    
    def add_message(self, timestamp: datetime, sender: str, content: str) -> str:
        """Add a message and return its hash."""
        msg_hash = self._generate_hash(timestamp, sender, content)
        self.seen_hashes.append(msg_hash)
        return msg_hash


class WeChatClient:
    """Wrapper for wxauto.WeChat with defensive error handling."""
    
    def __init__(self):
        self.deduplicator = MessageDeduplicator()
        try:
            from wxauto import WeChat
            self.wechat = WeChat()
            logger.info("WeChat client initialized successfully")
        except ImportError:
            logger.error("wxauto library not installed")
            raise ImportError("wxauto library is required but not installed")
        except Exception as e:
            logger.error(f"Failed to initialize WeChat client: {e}")
            raise
    
    @apply_jitter
    def get_recent_messages(self) -> List[RawMessage]:
        """
        Fetch recent messages from WeChat client.
        
        Returns:
            List of RawMessage objects
        """
        try:
            # Get new messages from WeChat
            raw_data = self.wechat.GetNextNewMessage()
            
            # Load settings for filtering
            settings = get_settings()
            monitor_groups = settings.ingestion.monitor_groups
            monitor_all = any(g.lower() == "all" for g in monitor_groups)
            
            # Convert to RawMessage objects
            messages = []
            if isinstance(raw_data, dict):
                for chat_name, msg_list in raw_data.items():
                    if not isinstance(msg_list, list):
                        continue
                    
                    for msg in msg_list:
                        # Extract message attributes
                        try:
                            content = getattr(msg, 'content', '')
                            sender = getattr(msg, 'sender', '')
                            
                            # Try to get timestamp, fallback to current time if not available
                            timestamp = getattr(msg, 'time', datetime.now())
                            if not isinstance(timestamp, datetime):
                                timestamp = datetime.now()
                            
                            # Check for duplicates
                            if self.deduplicator.is_duplicate(timestamp, sender, content):
                                continue
                            
                            # Generate message ID
                            msg_id = self.deduplicator._generate_hash(timestamp, sender, content)
                            
                            # Create RawMessage object
                            raw_msg = RawMessage(
                                id=msg_id,
                                content=content,
                                sender=sender,
                                room=chat_name if chat_name != sender else None,  # Assume room if different from sender
                                timestamp=timestamp
                            )
                            
                            # Apply Group Filtering
                            if not monitor_all:
                                if raw_msg.room not in monitor_groups:
                                    logger.debug(f"Ignored message from {raw_msg.room}")
                                    continue
                            
                            messages.append(raw_msg)
                        except Exception as e:
                            logger.warning(f"Failed to process individual message: {e}")
                            continue
            
            return messages
            
        except Exception as e:
            logger.error(f"Error fetching messages from WeChat: {e}")
            return []  # Return empty list on error to prevent crashes