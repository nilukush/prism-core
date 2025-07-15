"""
Anthropic (Claude) AI service implementation.
"""

from typing import Dict, Any, AsyncGenerator
import httpx
import json
from datetime import datetime

from backend.src.services.ai.base import (
    BaseAIService, AIProvider, AIRequest, AIResponse, AIModel
)
from backend.src.core.config import settings
from backend.src.core.logging import logger


class AnthropicService(BaseAIService):
    """Anthropic (Claude) AI service implementation."""
    
    API_URL = "https://api.anthropic.com/v1/messages"
    API_VERSION = "2023-06-01"
    
    def __init__(self, api_key: str = None):
        """Initialize Anthropic service."""
        super().__init__(AIProvider.ANTHROPIC, api_key or settings.ANTHROPIC_API_KEY)
        self.model_mapping = {
            AIModel.CLAUDE_3_OPUS: "claude-3-opus-20240229",
            AIModel.CLAUDE_3_SONNET: "claude-3-sonnet-20240229",
            AIModel.CLAUDE_3_HAIKU: "claude-3-haiku-20240307",
        }
        
    async def generate(self, request: AIRequest) -> AIResponse:
        """Generate response using Anthropic's API."""
        if not self.api_key:
            raise ValueError("Anthropic API key not configured")
            
        await self.initialize()
        
        if not self.client:
            raise ValueError("HTTP client not initialized")
        
        # Determine model
        model = request.model or settings.DEFAULT_LLM_MODEL
        if model not in self.model_mapping.values():
            # Try to map from enum
            model_enum = next(
                (k for k, v in self.model_mapping.items() if k.value == model),
                AIModel.CLAUDE_3_SONNET
            )
            model = self.model_mapping.get(model_enum, model)
        
        # Build messages
        messages = []
        if request.system_prompt:
            # Anthropic uses system parameter separately
            pass
        
        messages.append({
            "role": "user",
            "content": request.prompt
        })
        
        # Build request payload
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }
        
        # Add system prompt if provided
        if request.system_prompt:
            payload["system"] = request.system_prompt
        
        # Add response format if specified
        if request.response_format and request.response_format.get("type") == "json_object":
            # Anthropic doesn't have a JSON mode, but we can prompt for it
            messages[0]["content"] += "\n\nPlease respond with valid JSON only."
        
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.API_VERSION,
            "content-type": "application/json"
        }
        
        start_time = datetime.utcnow()
        
        logger.debug(
            "anthropic_request",
            model=model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            api_key_prefix=self.api_key[:10] if self.api_key else "None"
        )
        
        try:
            response = await self.client.post(
                self.API_URL,
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            result = response.json()
            
            # Extract content from response
            content = ""
            if result.get("content"):
                content = result["content"][0]["text"]
            
            # Calculate usage
            usage = {
                "prompt_tokens": result.get("usage", {}).get("input_tokens", 0),
                "completion_tokens": result.get("usage", {}).get("output_tokens", 0),
                "total_tokens": 0
            }
            usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]
            
            # Track metrics
            self._track_metrics("generate", model, duration, usage)
            
            logger.info(
                "anthropic_generation_complete",
                model=model,
                tokens=usage["total_tokens"],
                duration=duration
            )
            
            return AIResponse(
                content=content,
                model=model,
                provider=self.provider.value,
                usage=usage,
                metadata={
                    "request_id": result.get("id"),
                    "stop_reason": result.get("stop_reason"),
                    "model_version": result.get("model")
                }
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(
                "anthropic_api_error",
                status_code=e.response.status_code,
                response_text=e.response.text,
                model=model
            )
            if e.response.status_code == 401:
                raise ValueError("Invalid Anthropic API key")
            elif e.response.status_code == 429:
                raise ValueError("Anthropic API rate limit exceeded")
            else:
                raise ValueError(f"Anthropic API error: {e.response.text}")
        except Exception as e:
            logger.error(
                "anthropic_generation_error",
                error=str(e),
                error_type=type(e).__name__,
                model=model
            )
            raise
            
    async def stream_generate(self, request: AIRequest) -> AsyncGenerator[str, None]:
        """Stream response using Anthropic's API."""
        if not self.api_key:
            raise ValueError("Anthropic API key not configured")
            
        await self.initialize()
        
        # Determine model
        model = request.model or settings.DEFAULT_LLM_MODEL
        if model not in self.model_mapping.values():
            model_enum = next(
                (k for k, v in self.model_mapping.items() if k.value == model),
                AIModel.CLAUDE_3_SONNET
            )
            model = self.model_mapping.get(model_enum, model)
        
        # Build messages
        messages = []
        if request.system_prompt:
            # Anthropic uses system parameter separately
            pass
        
        messages.append({
            "role": "user",
            "content": request.prompt
        })
        
        # Build request payload
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "stream": True
        }
        
        # Add system prompt if provided
        if request.system_prompt:
            payload["system"] = request.system_prompt
        
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.API_VERSION,
            "content-type": "application/json"
        }
        
        try:
            async with self.client.stream(
                "POST",
                self.API_URL,
                json=payload,
                headers=headers
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # Remove "data: " prefix
                        if data == "[DONE]":
                            break
                        
                        try:
                            event = json.loads(data)
                            if event.get("type") == "content_block_delta":
                                delta = event.get("delta", {})
                                if delta.get("type") == "text_delta":
                                    text = delta.get("text", "")
                                    if text:
                                        yield text
                        except json.JSONDecodeError:
                            continue
                            
        except httpx.HTTPStatusError as e:
            logger.error(
                "anthropic_stream_error",
                status_code=e.response.status_code,
                model=model
            )
            raise ValueError(f"Anthropic streaming error: {e.response.status_code}")
        except Exception as e:
            logger.error(
                "anthropic_stream_error",
                error=str(e),
                model=model
            )
            raise