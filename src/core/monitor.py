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
    def _scan_target_sessions(self) -> List[RawMessage]:
        """
        Scan and process ONLY target sessions from the UI tree.

        This implements Look-Before-Leap strategy:
        1. Inspect SessionBox UI element without clicking randomly
        2. Filter sessions by monitor_groups settings
        3. ONLY click sessions that match target groups
        4. Retrieve messages from matched sessions only

        Returns:
            List of RawMessage objects from target sessions only
        """
        messages = []

        try:
            # Get the main WeChat window
            wxchat = self.wechat

            # Access SessionList through wxauto's GetSessionList method if available
            # Fall back to GetNextNewMessage with filtering if direct UI access not possible
            try:
                # Try to get session list using wxauto's method
                if hasattr(wxchat, 'GetSessionList'):
                    session_list = wxchat.GetSessionList()
                else:
                    # Fallback: Get all new messages and filter by target groups
                    raw_data = wxchat.GetNextNewMessage()
                    if raw_data and isinstance(raw_data, dict):
                        chat_name = raw_data.get('chat_name', 'Unknown')
                        if self._is_target_group(chat_name):
                            logger.info(f"Processing target session: {chat_name}")
                            raw_data_list = [raw_data]
                        else:
                            logger.debug(f"Skipping non-target session: {chat_name}")
                            return []
                    else:
                        return []
                # Process the session(s)
                if 'session_list' in locals():
                    # Iterate through actual session list
                    for session_item in session_list:
                        try:
                            # Extract session name - Try multiple attributes for compatibility
                            session_name = getattr(session_item, 'name', '') or \
                                         getattr(session_item, 'Title', '') or \
                                         getattr(session_item, 'Text', '') or \
                                         str(session_item)

                            if not session_name:
                                continue

                            # Filter by target groups - THIS IS THE CRITICAL CHECK
                            if not self._is_target_group(session_name):
                                logger.debug(f"Skipping non-target session: {session_name}")
                                continue  # SKIP - No click, no read

                            # TARGET SESSION - Click and read
                            logger.info(f"Target session found: {session_name}, clicking to read...")
                            session_item.click()

                            # Small delay to ensure UI updates
                            import time
                            time.sleep(0.2)

                            # Get all messages from this target session
                            session_messages = wxchat.GetAllMessage(savepic=False)

                            # Process messages from this target session
                            if isinstance(session_messages, dict):
                                chat_name = session_messages.get('chat_name', session_name)
                                msg_list = session_messages.get('msg', [])

                                if isinstance(msg_list, list):
                                    for msg in msg_list:
                                        try:
                                            content = getattr(msg, 'content', '')
                                            sender = getattr(msg, 'sender', '')
                                            timestamp = getattr(msg, 'time', datetime.now())
                                            if not isinstance(timestamp, datetime):
                                                timestamp = datetime.now()

                                            # Check for duplicates
                                            if self.deduplicator.is_duplicate(timestamp, sender, content):
                                                continue

                                            msg_id = self.deduplicator._generate_hash(timestamp, sender, content)

                                            raw_msg = RawMessage(
                                                id=msg_id,
                                                content=content,
                                                sender=sender,
                                                room=chat_name if chat_name != sender else None,
                                                timestamp=timestamp
                                            )
                                            messages.append(raw_msg)

                                        except Exception as e:
                                            logger.warning(f"Failed to process message from {session_name}: {e}")
                                            continue

                        except Exception as e:
                            logger.warning(f"Failed to process session {session_name if 'session_name' in locals() else 'unknown'}: {e}")
                            continue
                elif 'raw_data_list' in locals():
                    # Process filtered data from fallback path
                    for raw_data in raw_data_list:
                        if isinstance(raw_data, dict):
                            chat_name = raw_data.get('chat_name', 'Unknown')
                            msg_list = raw_data.get('msg', [])

                            if isinstance(msg_list, list):
                                for msg in msg_list:
                                    try:
                                        content = getattr(msg, 'content', '')
                                        sender = getattr(msg, 'sender', '')
                                        timestamp = getattr(msg, 'time', datetime.now())
                                        if not isinstance(timestamp, datetime):
                                            timestamp = datetime.now()

                                        if self.deduplicator.is_duplicate(timestamp, sender, content):
                                            continue

                                        msg_id = self.deduplicator._generate_hash(timestamp, sender, content)

                                        raw_msg = RawMessage(
                                            id=msg_id,
                                            content=content,
                                            sender=sender,
                                            room=chat_name if chat_name != sender else None,
                                            timestamp=timestamp
                                        )
                                        messages.append(raw_msg)

                                    except Exception as e:
                                        logger.warning(f"Failed to process individual message: {e}")
                                        continue

            except AttributeError:
                # If GetSessionList doesn't exist, fall back to targeted GetNextNewMessage
                logger.debug("GetSessionList not available, using fallback method")
                raw_data = wxchat.GetNextNewMessage()

                if raw_data and isinstance(raw_data, dict):
                    chat_name = raw_data.get('chat_name', 'Unknown')

                    # CRITICAL: Check target BEFORE processing
                    if not self._is_target_group(chat_name):
                        logger.debug(f"Skipping non-target session: {chat_name}")
                        return []  # Early return - don't process non-targets

                    logger.info(f"Processing target session: {chat_name}")

                    msg_list = raw_data.get('msg', [])
                    if isinstance(msg_list, list):
                        for msg in msg_list:
                            try:
                                content = getattr(msg, 'content', '')
                                sender = getattr(msg, 'sender', '')
                                timestamp = getattr(msg, 'time', datetime.now())
                                if not isinstance(timestamp, datetime):
                                    timestamp = datetime.now()

                                if self.deduplicator.is_duplicate(timestamp, sender, content):
                                    continue

                                msg_id = self.deduplicator._generate_hash(timestamp, sender, content)

                                raw_msg = RawMessage(
                                    id=msg_id,
                                    content=content,
                                    sender=sender,
                                    room=chat_name if chat_name != sender else None,
                                    timestamp=timestamp
                                )
                                messages.append(raw_msg)

                            except Exception as e:
                                logger.warning(f"Failed to process individual message: {e}")
                                continue

            return messages

        except Exception as e:
            logger.error(f"Error in _scan_target_sessions: {e}")
            return []

    def get_recent_messages(self) -> List[RawMessage]:
        """
        Fetch recent messages from WeChat client using targeted scanning.

        Returns:
            List of RawMessage objects
        """
        # Call the protected scanning method that enforces target filtering
        return self._scan_target_sessions()