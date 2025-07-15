"""
OpenAI service implementation.
"""

from typing import Dict, Any, Optional, AsyncGenerator
import json
from datetime import datetime
import time

import httpx
from openai import AsyncOpenAI

from backend.src.services.ai.base import (
    BaseAIService, AIProvider, AIModel, AIRequest, AIResponse
)
from backend.src.core.config import settings
from backend.src.core.logging import logger
from backend.src.core.telemetry import trace_async


class OpenAIService(BaseAIService):
    """OpenAI service implementation."""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(AIProvider.OPENAI, api_key)
        self.client: Optional[AsyncOpenAI] = None
        self.model_mapping = {
            AIModel.GPT4_TURBO: "gpt-4-turbo-preview",
            AIModel.GPT4: "gpt-4",
            AIModel.GPT35_TURBO: "gpt-3.5-turbo",
        }
        
    async def initialize(self):
        """Initialize OpenAI client."""
        if not self.client:
            api_key = self.api_key or getattr(settings, "OPENAI_API_KEY", None)
            if not api_key:
                raise ValueError("OpenAI API key not provided")
                
            self.client = AsyncOpenAI(
                api_key=api_key,
                timeout=getattr(settings, "LLM_REQUEST_TIMEOUT", 60.0),
                max_retries=3
            )
            logger.info("openai_service_initialized")
            
    async def close(self):
        """Close OpenAI client."""
        if self.client:
            await self.client.close()
            self.client = None
            
    @trace_async("openai_generate")
    async def generate(self, request: AIRequest) -> AIResponse:
        """Generate response using OpenAI."""
        start_time = time.time()
        
        if not self.client:
            await self.initialize()
            
        # Determine model
        model = request.model
        if not model:
            model = getattr(settings, "DEFAULT_OPENAI_MODEL", AIModel.GPT4_TURBO.value)
            
        # Map to actual OpenAI model name
        if model in self.model_mapping:
            model_name = self.model_mapping[model]
        else:
            model_name = model
            
        # Build messages
        messages = []
        if request.system_prompt:
            messages.append({
                "role": "system",
                "content": request.system_prompt
            })
        messages.append({
            "role": "user",
            "content": request.prompt
        })
        
        # Add response format if specified
        kwargs = {
            "model": model_name,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        
        if request.response_format:
            kwargs["response_format"] = request.response_format
            
        try:
            # Make API call
            logger.info(
                "openai_request",
                model=model_name,
                prompt_length=len(request.prompt),
                temperature=request.temperature
            )
            
            response = await self.client.chat.completions.create(**kwargs)
            
            # Extract content and usage
            content = response.choices[0].message.content
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            # Track metrics
            duration = time.time() - start_time
            self._track_metrics("generate", model_name, duration, usage)
            
            logger.info(
                "openai_response",
                model=model_name,
                duration=duration,
                usage=usage
            )
            
            return AIResponse(
                content=content,
                model=model_name,
                provider=self.provider.value,
                usage=usage,
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "response_id": response.id,
                    "created": response.created
                }
            )
            
        except Exception as e:
            logger.error(
                "openai_generate_error",
                error=str(e),
                model=model_name
            )
            raise
            
    async def stream_generate(
        self, 
        request: AIRequest
    ) -> AsyncGenerator[str, None]:
        """Stream response from OpenAI."""
        if not self.client:
            await self.initialize()
            
        # Determine model
        model = request.model
        if not model:
            model = getattr(settings, "DEFAULT_OPENAI_MODEL", AIModel.GPT4_TURBO.value)
            
        # Map to actual OpenAI model name
        if model in self.model_mapping:
            model_name = self.model_mapping[model]
        else:
            model_name = model
            
        # Build messages
        messages = []
        if request.system_prompt:
            messages.append({
                "role": "system",
                "content": request.system_prompt
            })
        messages.append({
            "role": "user",
            "content": request.prompt
        })
        
        # Stream response
        try:
            stream = await self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(
                "openai_stream_error",
                error=str(e),
                model=model_name
            )
            raise


class OpenAIEmbeddingService:
    """OpenAI embedding service for vector search."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, "OPENAI_API_KEY", None)
        self.client: Optional[AsyncOpenAI] = None
        self.model = "text-embedding-ada-002"
        
    async def initialize(self):
        """Initialize embedding client."""
        if not self.client:
            if not self.api_key:
                raise ValueError("OpenAI API key not provided")
                
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                timeout=30.0
            )
            
    async def close(self):
        """Close embedding client."""
        if self.client:
            await self.client.close()
            self.client = None
            
    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding for text."""
        if not self.client:
            await self.initialize()
            
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(
                "openai_embedding_error",
                error=str(e)
            )
            raise
            
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        if not self.client:
            await self.initialize()
            
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            return [item.embedding for item in response.data]
            
        except Exception as e:
            logger.error(
                "openai_batch_embedding_error",
                error=str(e),
                batch_size=len(texts)
            )
            raise