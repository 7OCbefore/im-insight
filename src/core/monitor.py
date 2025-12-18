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
    
    def _is_target_group(self, room_name: str) -> bool:
        """
        Check if the room is in the target monitor groups using fuzzy matching.
        Logic:
        1. Retrieve monitor_groups from settings.
        2. If 'all' in groups (case-insensitive), return True.
        3. Check if any configured group is a substring of room_name (case-insensitive).
        """
        if not room_name:
            return False

        settings = get_settings()
        monitor_groups = settings.ingestion.monitor_groups
        
        # Check for 'all' (case-insensitive)
        if any(g.lower() == "all" for g in monitor_groups):
            return True

        # Case-insensitive substring matching
        room_lower = room_name.lower()
        for target in monitor_groups:
            # Normalize target to lowercase
            target_lower = target.lower()
            # Check if target is a substring of room_name
            if target_lower in room_lower:
                return True
        
        return False

    @apply_jitter
    def get_recent_messages(self) -> List[RawMessage]:
        """
        Fetch recent messages from WeChat client using targeted filtering.

        Returns:
            List of RawMessage objects
        """
        messages = []

        try:
            # Get new messages from WeChat (keeps original API for compatibility)
            raw_data = self.wechat.GetNextNewMessage()

            if isinstance(raw_data, dict):
                # Extract chat_name and msg list explicitly from the dict
                chat_name = raw_data.get('chat_name', 'Unknown')
                msg_list = raw_data.get('msg', [])

                # EARLY FILTERING: Check if chat_name is a target group BEFORE processing
                # This prevents processing non-target sessions (Personal DMs, irrelevant groups)
                if not self._is_target_group(chat_name):
                    logger.debug(f"Skipping non-target session: {chat_name}")
                    return []  # Return empty list - don't process non-targets

                logger.info(f"Processing target session: {chat_name}")

                # Only process messages from target groups
                if isinstance(msg_list, list):
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
                                room=chat_name if chat_name != sender else None,
                                timestamp=timestamp
                            )

                            # Add to messages list
                            messages.append(raw_msg)

                        except Exception as e:
                            logger.warning(f"Failed to process individual message: {e}")
                            continue

            return messages

        except Exception as e:
            logger.error(f"Error fetching messages from WeChat: {e}")
            return []