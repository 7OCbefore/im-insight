"""
Signal Processor for IM-Insight - L1 Regex Engine.

This module implements the first layer of the processing pipeline that filters
incoming messages based on whitelist and blacklist patterns.
"""

import re
from typing import List, Dict, Any
from src.types.message import RawMessage
from src.types.market_signal import MarketSignal
from src.engine.llm_gateway import LLMGateway
from src.config.loader import get_settings

# Load application settings
settings = get_settings()


class SignalProcessor:
    """Processes raw messages and filters them based on relevance criteria."""
    
    def __init__(self):
        """Initialize the SignalProcessor with compiled regex patterns and LLM gateway."""
        self.whitelist_patterns = [re.compile(pattern, re.IGNORECASE) 
                                 for pattern in settings.rules.whitelist]
        self.blacklist_patterns = [re.compile(pattern, re.IGNORECASE) 
                                 for pattern in settings.rules.blacklist]
        self.llm_gateway = LLMGateway()
    
    def is_relevant(self, text: str) -> bool:
        """
        Determine if a message is relevant based on whitelist/blacklist.
        
        Args:
            text (str): The text to evaluate
            
        Returns:
            bool: True if relevant, False otherwise
        """
        # Return False if any blacklist pattern matches
        for pattern in self.blacklist_patterns:
            if pattern.search(text):
                return False
        
        # Return True only if at least one whitelist pattern matches
        for pattern in self.whitelist_patterns:
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
        # Run is_relevant check
        if not self.is_relevant(message.content):
            # Return a basic signal indicating manual check needed
            return [MarketSignal(
                raw_msg_id=message.id,
                intent="manual_check",
                timestamp=message.timestamp,
                group=message.room,
                sender=message.sender,
                raw_content=message.content
            )]
        

        
        # Check if intelligence is enabled
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
                return [self._extract_basic_info(message)]
        else:
            # Return basic result with manual_check intent
            return [MarketSignal(
                raw_msg_id=message.id,
                intent="manual_check",
                timestamp=message.timestamp,
                group=message.room,
                sender=message.sender,
                raw_content=message.content
            )]
    
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