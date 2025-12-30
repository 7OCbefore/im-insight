"""
Signal Processor for IM-Insight - L1 Regex Engine.

This module implements the first layer of the processing pipeline that filters
incoming messages based on whitelist and blacklist patterns.
"""

import re
import logging
from typing import List, Dict, Any
from src.types.message import RawMessage
from src.types.market_signal import MarketSignal
from src.engine.llm_gateway import LLMGateway
from src.config.loader import get_settings

# Load application settings
settings = get_settings()
logger = logging.getLogger(__name__)


class SignalProcessor:
    """Processes raw messages and filters them based on relevance criteria."""
    
    def __init__(self):
        """Initialize the SignalProcessor with compiled regex patterns and LLM gateway."""
        self.intent_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in settings.rules.intent_whitelist
        ]
        self.blacklist_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in settings.rules.blacklist
        ]
        self.llm_gateway = LLMGateway()
    
    def _contains_any(self, text: str, patterns) -> bool:
        """
        Check if text contains any of the compiled patterns.

        Args:
            text (str): The text to check
            patterns: List of compiled regex patterns

        Returns:
            bool: True if any pattern matches, False otherwise
        """
        for pattern in patterns:
            if pattern.search(text):
                return True
        return False

    def is_trade_related(self, message: RawMessage) -> bool:
        """Classify if a message is trade-related based on blacklist and intent whitelist."""
        if self._contains_any(message.content, self.blacklist_patterns):
            return False
        if not self.intent_patterns:
            return True
        return self._contains_any(message.content, self.intent_patterns)

    def process(self, message: RawMessage) -> List[MarketSignal]:
        """
        Process a raw message through the L1 filter.
        
        Args:
            message (RawMessage): The raw message to process
            
        Returns:
            List[MarketSignal]: List of processed market signals
        """
        # Step 1: Blacklist Check
        if self._contains_any(message.content, self.blacklist_patterns):
            return []  # Drop

        # Step 2: Intent Whitelist Check (trade relevance)
        if self.intent_patterns and not self._contains_any(message.content, self.intent_patterns):
            logger.debug(f"Ignored non-trade message: {message.content[:50]}...")
            return []  # Drop

        # Step 3: LLM Extraction (Only reachable if Steps 1-2 passed)
        if settings.intelligence.enabled:
            # Call LLMGateway.analyze() for intelligent extraction
            llm_results = self.llm_gateway.analyze(
                message.content,
                api_key=settings.intelligence.api_key.get_secret_value(),
                endpoint_url=settings.intelligence.endpoint_url,
                model=settings.intelligence.model,
                temperature=settings.intelligence.temperature,
                timeout=settings.intelligence.timeout
            )

            # If LLM succeeds and returns valid signals, use them
            if llm_results:
                signals = []
                for llm_result in llm_results:
                    # CRITICAL: Verify that LLM actually extracted meaningful data
                    intent = llm_result.get("intent", "").strip()
                    item_name = llm_result.get("Item Name", "").strip() if llm_result.get("Item Name") else ""

                    # Only create signal if both intent and item are present
                    if intent and item_name:
                        signals.append(MarketSignal(
                            raw_msg_id=message.id,
                            intent=intent,
                            timestamp=message.timestamp,
                            group=message.room,
                            sender=message.sender,
                            raw_content=message.content,
                            item=item_name,
                            price=llm_result.get("Price"),
                            specs=llm_result.get("Specs"),
                            confidence_score=0.9  # High confidence for LLM extraction
                        ))
                    else:
                        logger.debug(f"Dropped (LLM extracted insufficient data): intent={intent}, item={item_name}")

                return signals
            else:
                # LLM failed or returned empty - try fallback ONLY if content has clear trading keywords
                return self._extract_basic_info(message)
        else:
            # Step 4: Fallback (Regex extraction if LLM disabled)
            return self._extract_basic_info(message)
    
    def _extract_basic_info(self, message: RawMessage) -> List[MarketSignal]:
        """
        Extract basic information from a relevant message using simple regex matching.
        Only creates signals for messages with CLEAR trading intent.

        Args:
            message (RawMessage): The relevant message

        Returns:
            List[MarketSignal]: List containing basic market signal, or empty list if no clear intent
        """
        content = message.content.lower()
        content_stripped = content.strip()

        # Define clear trading intent keywords
        buy_keywords = ["求购", "收", "买", "需求", "要"]
        sell_keywords = ["出", "卖", "出售", "有货", "供应"]

        # Check for clear BUY intent
        for keyword in buy_keywords:
            if keyword in content_stripped:
                logger.debug(f"Detected BUY intent via keyword '{keyword}'")

                # Simple item extraction - get text after the keyword
                parts = content_stripped.split(keyword, 1)
                if len(parts) > 1:
                    item = parts[1].split()[0].upper() if parts[1].split() else "UNKNOWN"

                    return [MarketSignal(
                        raw_msg_id=message.id,
                        intent="buy",
                        timestamp=message.timestamp,
                        group=message.room,
                        sender=message.sender,
                        raw_content=message.content,
                        item=item,
                        confidence_score=0.6  # Medium confidence for basic extraction
                    )]

        # Check for clear SELL intent
        for keyword in sell_keywords:
            if keyword in content_stripped:
                logger.debug(f"Detected SELL intent via keyword '{keyword}'")

                # Simple item extraction - get text after the keyword
                parts = content_stripped.split(keyword, 1)
                if len(parts) > 1:
                    item = parts[1].split()[0].upper() if parts[1].split() else "UNKNOWN"

                    return [MarketSignal(
                        raw_msg_id=message.id,
                        intent="sell",
                        timestamp=message.timestamp,
                        group=message.room,
                        sender=message.sender,
                        raw_content=message.content,
                        item=item,
                        confidence_score=0.6  # Medium confidence for basic extraction
                    )]

        # CRITICAL: No clear trading intent found - return empty list
        logger.debug(f"Dropped (No clear trading intent): {content[:50]}...")
        return []
