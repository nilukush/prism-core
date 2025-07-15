"""
Ollama (local LLM) AI service implementation.
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


class OllamaService(BaseAIService):
    """Ollama local LLM service implementation."""
    
    def __init__(self, api_url: str = None):
        """Initialize Ollama service."""
        super().__init__(AIProvider.OLLAMA, api_key=None)
        self.api_url = api_url or settings.OLLAMA_BASE_URL or "http://localhost:11434"
        self.model_mapping = {
            AIModel.LLAMA2: "llama2",
            AIModel.MIXTRAL: "mixtral",
        }
        
    async def generate(self, request: AIRequest) -> AIResponse:
        """Generate response using Ollama API."""
        await self.initialize()
        
        # Determine model
        model = request.model or "llama2"
        if model in [m.value for m in AIModel]:
            # Map from enum value
            model_enum = next((m for m in AIModel if m.value == model), None)
            if model_enum in self.model_mapping:
                model = self.model_mapping[model_enum]
        
        # Build prompt with system message if provided
        prompt = request.prompt
        if request.system_prompt:
            prompt = f"{request.system_prompt}\n\n{prompt}"
        
        # Build request payload
        payload = {
            "model": model,
            "prompt": prompt,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
            },
            "stream": False
        }
        
        # Add response format hint if specified
        if request.response_format and request.response_format.get("type") == "json_object":
            prompt += "\n\nPlease respond with valid JSON only."
            payload["prompt"] = prompt
        
        start_time = datetime.utcnow()
        
        try:
            response = await self.client.post(
                f"{self.api_url}/api/generate",
                json=payload,
                timeout=settings.LLM_REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            result = response.json()
            
            # Extract content from response
            content = result.get("response", "")
            
            # Estimate tokens (Ollama doesn't always provide exact counts)
            usage = {
                "prompt_tokens": len(prompt.split()) * 2,  # Rough estimate
                "completion_tokens": len(content.split()) * 2,  # Rough estimate
                "total_tokens": 0
            }
            usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]
            
            # Track metrics
            self._track_metrics("generate", model, duration, usage)
            
            logger.info(
                "ollama_generation_complete",
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
                    "done": result.get("done"),
                    "context": result.get("context"),
                    "total_duration": result.get("total_duration"),
                    "load_duration": result.get("load_duration"),
                    "eval_duration": result.get("eval_duration")
                }
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(
                "ollama_api_error",
                status_code=e.response.status_code,
                response_text=e.response.text,
                model=model
            )
            if e.response.status_code == 404:
                raise ValueError(f"Model '{model}' not found in Ollama. Please pull the model first.")
            else:
                raise ValueError(f"Ollama API error: {e.response.text}")
        except httpx.ConnectError:
            raise ValueError(
                "Cannot connect to Ollama. Please ensure Ollama is running "
                f"and accessible at {self.api_url}"
            )
        except Exception as e:
            logger.error(
                "ollama_generation_error",
                error=str(e),
                model=model
            )
            raise
            
    async def stream_generate(self, request: AIRequest) -> AsyncGenerator[str, None]:
        """Stream response using Ollama API."""
        await self.initialize()
        
        # Determine model
        model = request.model or "llama2"
        if model in [m.value for m in AIModel]:
            model_enum = next((m for m in AIModel if m.value == model), None)
            if model_enum in self.model_mapping:
                model = self.model_mapping[model_enum]
        
        # Build prompt with system message if provided
        prompt = request.prompt
        if request.system_prompt:
            prompt = f"{request.system_prompt}\n\n{prompt}"
        
        # Build request payload
        payload = {
            "model": model,
            "prompt": prompt,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
            },
            "stream": True
        }
        
        try:
            async with self.client.stream(
                "POST",
                f"{self.api_url}/api/generate",
                json=payload,
                timeout=settings.LLM_REQUEST_TIMEOUT
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if data.get("response"):
                                yield data["response"]
                            if data.get("done"):
                                break
                        except json.JSONDecodeError:
                            continue
                            
        except httpx.HTTPStatusError as e:
            logger.error(
                "ollama_stream_error",
                status_code=e.response.status_code,
                model=model
            )
            raise ValueError(f"Ollama streaming error: {e.response.status_code}")
        except httpx.ConnectError:
            raise ValueError(
                "Cannot connect to Ollama. Please ensure Ollama is running "
                f"and accessible at {self.api_url}"
            )
        except Exception as e:
            logger.error(
                "ollama_stream_error",
                error=str(e),
                model=model
            )
            raise