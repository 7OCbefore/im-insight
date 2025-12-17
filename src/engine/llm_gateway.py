"""
LLM Gateway for IM-Insight - L2 Extractor.

This module implements the second layer of the processing pipeline that
uses an LLM to extract structured data from relevant messages.
"""

import json
import time
import httpx
from typing import Optional, Dict, Any


class LLMGateway:
    """Gateway for communicating with an OpenAI-compatible API endpoint."""
    
    def __init__(self, api_base_url: str = "http://localhost:8000/v1", 
                 api_key: str = "sk-test-key", 
                 model: str = "gpt-3.5-turbo"):
        """
        Initialize the LLM Gateway.
        
        Args:
            api_base_url (str): Base URL for the OpenAI-compatible API
            api_key (str): API key for authentication
            model (str): Model identifier to use for completions
        """
        self.api_base_url = api_base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.client = httpx.Client(
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=5.0  # Hard timeout to prevent blocking
        )
        
        # System prompt for the LLM
        self.system_prompt = (
            "You are a trading assistant. Extract the intent (Buy/Sell), "
            "Item Name, Price, and Quantity from the message. "
            "Return strictly JSON. If no trading intent, return null."
        )
    
    def analyze(self, text: str) -> Optional[Dict]:
        """
        Analyze text using the LLM to extract structured data.
        
        Args:
            text (str): Text to analyze
            
        Returns:
            Optional[Dict]: Extracted data or None if no trading intent
            
        Examples:
            >>> gateway = LLMGateway()
            >>> result = gateway.analyze("Buy 100 shares of AAPL at $150")
            >>> isinstance(result, dict)
            True
        """
        # Prepare the messages for the chat completion API
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": text}
        ]
        
        # Prepare the request payload
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 200
        }
        
        # Try up to 3 times with exponential backoff
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.post(
                    f"{self.api_base_url}/chat/completions",
                    json=payload
                )
                
                # Raise an exception for bad status codes
                response.raise_for_status()
                
                # Parse the response
                result = response.json()
                
                # Extract the content from the assistant's response
                content = result["choices"][0]["message"]["content"]
                
                # Try to parse as JSON
                try:
                    parsed_data = json.loads(content)
                    return parsed_data
                except json.JSONDecodeError:
                    # If JSON parsing fails, log and continue
                    print(f"Failed to parse LLM response as JSON: {content}")
                    return None
                    
            except httpx.TimeoutException:
                # Exponential backoff: 1s, 2s, 4s
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"LLM request timed out. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print("LLM request failed after max retries due to timeout")
                    return None
                    
            except httpx.RequestError as e:
                print(f"LLM request failed: {e}")
                return None
                
            except Exception as e:
                print(f"Unexpected error in LLM analysis: {e}")
                return None
        
        return None  # Failed after all retries


# Example usage
if __name__ == "__main__":
    # Create gateway
    gateway = LLMGateway()
    
    # Test analysis
    test_text = "Buy 100 shares of AAPL at $150"
    result = gateway.analyze(test_text)
    print(f"Analysis result: {result}")