"""
LLM Gateway for IM-Insight - L2 Extractor.

This module implements the second layer of the processing pipeline that
uses an LLM to extract structured data from relevant messages.
"""

import json
import asyncio
import httpx
import logging
import time
from collections import deque
from typing import Optional, Dict, Any, List

# Configure logger
logger = logging.getLogger(__name__)


class LLMGateway:
    """Gateway for communicating with an OpenAI-compatible API endpoint."""
    
    def __init__(self):
        """
        Initialize the LLM Gateway.
        Note: Actual API parameters are passed in the analyze method.
        """
        # System prompt for the LLM - strictly asks for JSON array output
        self.system_prompt = (
            "你是一位专业的二级市场（烟酒/礼品）交易情报分析师。请分析用户的聊天消息，提取结构化数据。\n"
            "请准确识别以下信息：\n"
            "1. 意图 (intent): 识别是 'Buy' (求/收/需/高价收) 还是 'Sell' (出/卖/有/出货)。如果无法确定或为闲聊，忽略。\n"
            "2. 品名 (Item Name): 提取商品核心名称，如 '飞天'、'龙年'、'芙蓉王'、'华子'。请自动补全商品全称（如 '散飞' -> '飞天茅台'）。\n"
            "3. 价格 (Price): 提取具体的数字价格。如果包含'xxx'、'私聊'或未明示价格，请填 0。\n"
            "4. 规格 (Specs): 提取年份、包装（原箱/散瓶）、票据（带票/不带票）等细节。\n"
            "\n"
            "输出严格要求：\n"
            "- 必须且仅返回合法的 JSON 数组格式，不要包含 Markdown 标记（如 ```json）。\n"
            "- 数组中的每个对象都必须包含字段：\"intent\", \"Item Name\", \"Price\"。\n"
            "- 如果消息包含多个商品，请以数组形式返回所有商品信息。\n"
            "- 如果消息不包含交易意图，请返回空数组 []。\n"
            "\n"
            "示例 1：\n"
            "输入: '出两个24散飞 2810'\n"
            "输出: [{\"intent\": \"Sell\", \"Item Name\": \"飞天茅台\", \"Price\": 2810}]\n"
            "\n"
            "示例 2：\n"
            "输入: '求购中华，有的私聊'\n"
            "输出: [{\"intent\": \"Buy\", \"Item Name\": \"中华\", \"Price\": 0}]\n"
            "\n"
            "示例 3（多商品）：\n"
            "输入: '出两个24散飞 2810，还有两条芙蓉王 400'\n"
            "输出: [{\"intent\": \"Sell\", \"Item Name\": \"飞天茅台\", \"Price\": 2810}, {\"intent\": \"Sell\", \"Item Name\": \"芙蓉王\", \"Price\": 400}]"
        )
        self._rate_window = deque()
        self._rate_limit = 60
    
    async def _call_api(self, endpoint_url: str, api_key: str, model: str, 
                       messages: list, temperature: float = 0.1, 
                       timeout: int = 10) -> Optional[List[Dict]]:
        """
        Call the LLM API asynchronously with full control over the request.
        
        Args:
            endpoint_url (str): Full endpoint URL for the API
            api_key (str): API key for authentication
            model (str): Model identifier to use for completions
            messages (list): Messages for the chat completion API
            temperature (float): Sampling temperature for the model
            timeout (int): Request timeout in seconds
            
        Returns:
            Optional[List[Dict]]: API response or None if failed
        """
        # Prepare the request payload with required parameters
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "top_p": 0.7,
            "response_format": {"type": "json_object"}  # Force JSON if model supports it
        }
        
        # Create async HTTP client with settings
        async with httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=timeout
        ) as client:
            try:
                # Use the endpoint_url directly without appending paths
                response = await client.post(endpoint_url, json=payload)
                
                # Check for non-200 status codes
                if response.status_code != 200:
                    logger.error(f"LLM API returned non-200 status code: {response.status_code}")
                    logger.error(f"Response body: {response.text}")
                    return None
                
                # Parse the response
                result = response.json()
                
                # Extract the content from the assistant's response
                content = result["choices"][0]["message"]["content"]
                
                # Try to parse as JSON
                try:
                    parsed_data = json.loads(content)
                    return parsed_data
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse LLM response as JSON: {content}")
                    return None
                    
            except httpx.TimeoutException as e:
                logger.error(f"LLM request timed out: {e}")
                return None
            except httpx.RequestError as e:
                logger.error(f"LLM request failed: {e}")
                return None
            except Exception as e:
                logger.error(f"Unexpected error in LLM API call: {e}")
                return None
    
    def analyze(self, text: str, api_key: str, endpoint_url: str, model: str, 
                temperature: float = 0.1, timeout: int = 10) -> List[Dict]:
        """
        Analyze text using the LLM to extract structured data.
        
        Args:
            text (str): Text to analyze
            api_key (str): API key for authentication
            endpoint_url (str): Full endpoint URL for the API
            model (str): Model identifier to use for completions
            temperature (float): Sampling temperature for the model
            timeout (int): Request timeout in seconds
            
        Returns:
            List[Dict]: List of extracted data objects, empty list if no trading intent
        """
        # Rate limit before preparing the messages
        self._throttle()

        # Prepare the messages for the chat completion API
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": text}
        ]
        
        # Run the async method in a new event loop
        try:
            # Create a new event loop for the async call
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self._call_api(endpoint_url, api_key, model, messages, temperature, timeout)
            )
            loop.close()
            
            # Handle backward compatibility and ensure we always return a list
            if result is None:
                return []
            elif isinstance(result, dict):
                # Wrap single dict in a list for backward compatibility
                return [result]
            elif isinstance(result, list):
                # Already a list, return as is
                return result
            else:
                # Unexpected type, return empty list
                logger.warning(f"Unexpected result type from LLM: {type(result)}")
                return []
        except Exception as e:
            logger.error(f"Error running async LLM call: {e}")
            return []

    def _throttle(self) -> None:
        now = time.monotonic()
        window = 60.0
        while self._rate_window and now - self._rate_window[0] > window:
            self._rate_window.popleft()
        if len(self._rate_window) >= self._rate_limit:
            sleep_for = window - (now - self._rate_window[0])
            if sleep_for > 0:
                logger.warning("LLM rate limit reached; delaying request")
                time.sleep(sleep_for)
            now = time.monotonic()
            while self._rate_window and now - self._rate_window[0] > window:
                self._rate_window.popleft()
        self._rate_window.append(time.monotonic())


# Example usage
if __name__ == "__main__":
    # Create gateway
    gateway = LLMGateway()
    
    # Test analysis
    test_text = "Buy 100 shares of AAPL at $150"
    result = gateway.analyze(test_text)
    print(f"Analysis result: {result}")
