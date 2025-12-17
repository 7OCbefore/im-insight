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

# Mock settings object - in a real implementation this would come from a config
class Settings:
    def __init__(self):
        self.whitelist = [
            r'\b(buy|sell)\b',
            r'\b(stock|option|future)\b',
            r'\b(price|value)\b'
        ]
        self.blacklist = [
            r'\b(spam|advertisement)\b',
            r'\b(ignore|discard)\b'
        ]
        self.intelligence = type('obj', (object,), {'enabled': True})()

# Global settings instance
settings = Settings()


class SignalProcessor:
    """Processes raw messages and filters them based on relevance criteria."""
    
    def __init__(self):
        """Initialize the SignalProcessor with compiled regex patterns and LLM gateway."""
        self.whitelist_patterns = [re.compile(pattern, re.IGNORECASE) 
                                 for pattern in settings.whitelist]
        self.blacklist_patterns = [re.compile(pattern, re.IGNORECASE) 
                                 for pattern in settings.blacklist]
        self.llm_gateway = LLMGateway()
    
    def is_relevant(self, text: str) -> bool:
        """
        Determine if a message is relevant based on whitelist/blacklist.
        
        Args:
            text (str): The text to evaluate
            
        Returns:
            bool: True if relevant, False otherwise
            
        Examples:
            >>> processor = SignalProcessor()
            >>> processor.is_relevant("Buy 100 shares of AAPL at $150")
            True
            >>> processor.is_relevant("This is spam advertisement")
            False
            >>> processor.is_relevant("Random conversation text")
            False
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
    
    def process(self, message: RawMessage) -> MarketSignal:
        """
        Process a raw message through the L1 filter.
        
        Args:
            message (RawMessage): The raw message to process
            
        Returns:
            MarketSignal: Processed market signal
        """
        # Run is_relevant check
        if not self.is_relevant(message.content):
            # In a real implementation, we might return None or a special marker
            # For now, we'll return a basic signal indicating manual check needed
            return MarketSignal(
                raw_msg_id=message.id,
                intent="manual_check"
            )
        
        # Log "L1 Hit" - in a real implementation this would be proper logging
        print(f"L1 Hit: {message.content}")
        
        # Check if intelligence is enabled
        if settings.intelligence.enabled:
            # Call LLMGateway.analyze() for intelligent extraction
            llm_result = self.llm_gateway.analyze(message.content)
            
            # If LLM succeeds, use its result
            if llm_result:
                return MarketSignal(
                    raw_msg_id=message.id,
                    intent=llm_result.get("intent", "unknown"),
                    item=llm_result.get("Item Name"),
                    price=llm_result.get("Price"),
                    confidence_score=0.9  # High confidence for LLM extraction
                )
            else:
                # If LLM fails, fall back to basic extraction
                return self._extract_basic_info(message)
        else:
            # Return basic result with manual_check intent
            return MarketSignal(
                raw_msg_id=message.id,
                intent="manual_check"
            )
    
    def _extract_basic_info(self, message: RawMessage) -> MarketSignal:
        """
        Extract basic information from a relevant message.
        
        Args:
            message (RawMessage): The relevant message
            
        Returns:
            MarketSignal: Basic market signal with extracted info
        """
        # This is a simplified extraction - in reality, this would be replaced
        # by the LLM analysis in the complete implementation
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
                
        return MarketSignal(
            raw_msg_id=message.id,
            intent=intent,
            item=item,
            confidence_score=0.5  # Low confidence for basic extraction
        )


# Example usage
if __name__ == "__main__":
    # Create processor
    processor = SignalProcessor()
    
    # Test messages
    test_messages = [
        RawMessage("1", "Buy 100 shares of AAPL at $150", "trader1", "trading_room", "2023-01-01T10:00:00"),
        RawMessage("2", "This is spam advertisement", "spammer", "general", "2023-01-01T10:01:00"),
        RawMessage("3", "Random conversation text", "user", "general", "2023-01-01T10:02:00"),
        RawMessage("4", "Sell 50 contracts of SPX options", "trader2", "derivatives", "2023-01-01T10:03:00")
    ]
    
    # Process messages
    for msg in test_messages:
        signal = processor.process(msg)
        print(f"Message: {msg.content}")
        print(f"Signal: {signal}\n")