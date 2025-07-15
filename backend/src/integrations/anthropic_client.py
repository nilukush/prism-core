"""
Anthropic API client integration.
"""

from typing import Dict, Any, List, Optional
import httpx
import logging

from backend.src.core.config import settings

logger = logging.getLogger(__name__)


class AnthropicClient:
    """Client for Anthropic API interactions."""
    
    def __init__(self):
        """Initialize Anthropic client."""
        self.api_key = settings.ANTHROPIC_API_KEY
        self.base_url = "https://api.anthropic.com/v1"
        self.client = httpx.AsyncClient(
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            },
            timeout=60.0
        )
    
    async def create_message(
        self,
        model: str,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a message completion.
        
        Args:
            model: Model name (e.g., "claude-3-opus-20240229")
            messages: List of message dicts with role and content
            system: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Returns:
            Anthropic API response
        """
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs
        }
        
        if system:
            payload["system"] = system
        
        try:
            response = await self.client.post(
                f"{self.base_url}/messages",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Anthropic API error: {str(e)}")
            raise
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()