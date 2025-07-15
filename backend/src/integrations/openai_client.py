"""
OpenAI API client integration.
"""

from typing import Dict, Any, List, Optional
import httpx
import logging

from backend.src.core.config import settings

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Client for OpenAI API interactions."""
    
    def __init__(self):
        """Initialize OpenAI client."""
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = "https://api.openai.com/v1"
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=60.0
        )
    
    async def create_chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a chat completion.
        
        Args:
            model: Model name (e.g., "gpt-3.5-turbo")
            messages: List of message dicts with role and content
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            tools: Optional tools/functions
            **kwargs: Additional parameters
            
        Returns:
            OpenAI API response
        """
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            **kwargs
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        if tools:
            payload["tools"] = tools
        
        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
    
    async def create_embedding(
        self,
        model: str,
        input: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create text embedding.
        
        Args:
            model: Model name (e.g., "text-embedding-ada-002")
            input: Text to embed
            **kwargs: Additional parameters
            
        Returns:
            OpenAI API response with embedding
        """
        payload = {
            "model": model,
            "input": input,
            **kwargs
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/embeddings",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"OpenAI embedding error: {str(e)}")
            raise
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()