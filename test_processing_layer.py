"""
Test script for IM-Insight Processing Layer
"""

import re
from dataclasses import dataclass
from typing import Optional

# Test the MarketSignal dataclass
@dataclass
class MarketSignal:
    """Represents a processed market signal extracted from a raw message."""
    raw_msg_id: str
    intent: str
    item: Optional[str] = None
    price: Optional[float] = None
    confidence_score: Optional[float] = None

# Test the SignalProcessor class logic
class TestSettings:
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

# Test SignalProcessor logic
def test_is_relevant():
    settings = TestSettings()
    whitelist_patterns = [re.compile(pattern, re.IGNORECASE) 
                         for pattern in settings.whitelist]
    blacklist_patterns = [re.compile(pattern, re.IGNORECASE) 
                         for pattern in settings.blacklist]
    
    def is_relevant(text: str) -> bool:
        # Return False if any blacklist pattern matches
        for pattern in blacklist_patterns:
            if pattern.search(text):
                return False
        
        # Return True only if at least one whitelist pattern matches
        for pattern in whitelist_patterns:
            if pattern.search(text):
                return True
                
        return False
    
    # Test cases
    assert is_relevant("Buy 100 shares of AAPL at $150") == True
    assert is_relevant("This is spam advertisement") == False
    assert is_relevant("Random conversation text") == False
    assert is_relevant("Sell 50 contracts of SPX options") == True
    
    print("All is_relevant tests passed!")

# Test LLMGateway logic (simulated)
def test_llm_analysis():
    # Simulate LLM response
    def analyze(text: str) -> Optional[dict]:
        # Simple simulation - in reality this would call an API
        if "buy" in text.lower():
            return {
                "intent": "Buy",
                "Item Name": "AAPL",
                "Price": 150.0,
                "Quantity": 100
            }
        elif "sell" in text.lower():
            return {
                "intent": "Sell",
                "Item Name": "SPX",
                "Price": None,
                "Quantity": 50
            }
        else:
            return None
    
    # Test cases
    result = analyze("Buy 100 shares of AAPL at $150")
    assert result is not None
    assert result["intent"] == "Buy"
    
    result = analyze("Random text")
    assert result is None
    
    print("All LLM analysis tests passed!")

if __name__ == "__main__":
    test_is_relevant()
    test_llm_analysis()
    print("All tests passed!")