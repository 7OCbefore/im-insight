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
        self.whitelist_patterns = [re.compile(pattern, re.IGNORECASE) 
                                 for pattern in settings.rules.whitelist]
        self.blacklist_patterns = [re.compile(pattern, re.IGNORECASE) 
                                 for pattern in settings.rules.blacklist]
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

        # Step 2: Whitelist Check (Critical Fix)
        # This MUST happen BEFORE any LLM call
        if not self._contains_any(message.content, self.whitelist_patterns):
            # Log and drop irrelevant messages (e.g., "中午吃什么")
            logger.debug(f"Ignored irrelevant message: {message.content[:50]}...")
            return []  # Drop (Ignore irrelevant messages)

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

            # If LLM succeeds, use its results
            if llm_results:
                signals = []
                for llm_result in llm_results:
                    signals.append(MarketSignal(
                        raw_msg_id=message.id,
                        intent=llm_result.get("intent", "unknown"),
                        timestamp=message.timestamp,
                        group=message.room,
                        sender=message.sender,
                        raw_content=message.content,
                        item=llm_result.get("Item Name"),
                        price=llm_result.get("Price"),
                        specs=llm_result.get("Specs"),
                        confidence_score=0.9  # High confidence for LLM extraction
                    ))
                return signals
            else:
                # If LLM fails, fall back to basic extraction
                return self._extract_basic_info(message)
        else:
            # Step 4: Fallback (Regex extraction if LLM disabled)
            return self._extract_basic_info(message)
    
    def _extract_basic_info(self, message: RawMessage) -> List[MarketSignal]:
        """
        Extract basic information from a relevant message.
        
        Args:
            message (RawMessage): The relevant message
            
        Returns:
            List[MarketSignal]: List containing basic market signal with extracted info
        """
        content = message.content.lower()
        
        # Simple intent detection
        intent = "unknown"
        if "buy" in content:
            intent = "buy"
        elif "sell" in content:
            intent = "sell"
            
        # Simple item extraction (very basic)
        item = None
        words = content.split()
        for i, word in enumerate(words):
            if word in ["buy", "sell"] and i + 1 < len(words):
                item = words[i + 1].upper()
                break
                
        return [MarketSignal(
            raw_msg_id=message.id,
            intent=intent,
            timestamp=message.timestamp,
            group=message.room,
            sender=message.sender,
            raw_content=message.content,
            item=item,
            confidence_score=0.5  # Low confidence for basic extraction
        )]