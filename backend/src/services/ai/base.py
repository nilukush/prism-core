"""
Base AI service interface and configuration.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum
import asyncio
from datetime import datetime
import json

from pydantic import BaseModel, Field
import httpx

from backend.src.core.config import settings
from backend.src.core.logging import logger
from backend.src.core.telemetry import trace_async, metrics


# Metrics
ai_requests = metrics.counter(
    "ai_requests_total",
    "Total number of AI requests",
    ["provider", "model", "operation"]
)

ai_request_duration = metrics.histogram(
    "ai_request_duration_seconds",
    "AI request duration",
    ["provider", "model", "operation"]
)

ai_tokens_used = metrics.counter(
    "ai_tokens_used_total",
    "Total tokens used",
    ["provider", "model", "type"]  # type: prompt, completion, total
)


class AIProvider(str, Enum):
    """Supported AI providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    MOCK = "mock"  # For testing


class AIModel(str, Enum):
    """Available AI models."""
    # OpenAI
    GPT4_TURBO = "gpt-4-turbo-preview"
    GPT4 = "gpt-4"
    GPT35_TURBO = "gpt-3.5-turbo"
    
    # Anthropic
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"
    
    # Local/Ollama
    LLAMA2 = "llama2"
    MIXTRAL = "mixtral"
    
    # Mock
    MOCK_MODEL = "mock-model"


class AIRequest(BaseModel):
    """Base AI request model."""
    prompt: str
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=2000, ge=1, le=32000)
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    response_format: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AIResponse(BaseModel):
    """Base AI response model."""
    content: str
    model: str
    provider: str
    usage: Dict[str, int] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BaseAIService(ABC):
    """Base interface for AI services."""
    
    def __init__(self, provider: AIProvider, api_key: Optional[str] = None):
        self.provider = provider
        self.api_key = api_key
        self.client: Optional[httpx.AsyncClient] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        
    async def initialize(self):
        """Initialize the AI service."""
        if not self.client:
            self.client = httpx.AsyncClient(
                timeout=httpx.Timeout(settings.LLM_REQUEST_TIMEOUT),
                limits=httpx.Limits(max_keepalive_connections=5)
            )
            
    async def close(self):
        """Close the AI service."""
        if self.client:
            await self.client.aclose()
            self.client = None
            
    @abstractmethod
    async def generate(self, request: AIRequest) -> AIResponse:
        """Generate AI response."""
        pass
        
    @abstractmethod
    async def stream_generate(self, request: AIRequest):
        """Stream AI response."""
        pass
        
    def _track_metrics(self, operation: str, model: str, duration: float, usage: Dict[str, int]):
        """Track AI metrics."""
        ai_requests.labels(
            provider=self.provider.value,
            model=model,
            operation=operation
        ).inc()
        
        ai_request_duration.labels(
            provider=self.provider.value,
            model=model,
            operation=operation
        ).observe(duration)
        
        if usage:
            for token_type, count in usage.items():
                ai_tokens_used.labels(
                    provider=self.provider.value,
                    model=model,
                    type=token_type
                ).inc(count)


class PromptTemplate:
    """Reusable prompt templates."""
    
    @staticmethod
    def system_prompt() -> str:
        """Get default system prompt."""
        return """You are PRISM AI, an intelligent assistant for product management. 
You help product managers create user stories, PRDs, sprint plans, and provide insights.
Always be professional, concise, and focus on delivering value to the product team."""

    @staticmethod
    def prd_generation(
        product_name: str,
        description: str,
        target_audience: str,
        key_features: List[str],
        constraints: Optional[List[str]] = None
    ) -> str:
        """Generate PRD prompt."""
        features_list = "\n".join(f"- {feature}" for feature in key_features)
        constraints_list = "\n".join(f"- {c}" for c in constraints) if constraints else "None specified"
        
        return f"""Create a comprehensive Product Requirements Document (PRD) for the following product:

Product Name: {product_name}
Description: {description}
Target Audience: {target_audience}

Key Features:
{features_list}

Constraints:
{constraints_list}

Please structure the PRD with the following sections:
1. Executive Summary
2. Problem Statement
3. Objectives and Success Metrics
4. User Personas
5. User Stories and Use Cases
6. Functional Requirements
7. Non-Functional Requirements
8. Technical Architecture Overview
9. Dependencies and Risks
10. Timeline and Milestones
11. Open Questions

Make it detailed, professional, and ready for stakeholder review."""

    @staticmethod
    def user_story_generation(
        requirement: str,
        context: Optional[str] = None,
        story_count: int = 3
    ) -> str:
        """Generate user story prompt."""
        context_text = f"\nContext: {context}" if context else ""
        
        return f"""Generate {story_count} detailed user stories based on the following requirement:

Requirement: {requirement}{context_text}

For each user story, provide:
1. Title
2. User story in the format: "As a [persona], I want to [action], so that [benefit]"
3. Acceptance criteria (at least 3-5 criteria in Given-When-Then format)
4. Story points estimate (using Fibonacci sequence: 1, 2, 3, 5, 8, 13)
5. Priority (High, Medium, Low)
6. Dependencies (if any)
7. Test scenarios (at least 2-3)

Format the response as structured JSON."""

    @staticmethod
    def sprint_estimation(
        stories: List[Dict[str, Any]],
        team_velocity: int,
        sprint_duration: int = 14
    ) -> str:
        """Generate sprint estimation prompt."""
        stories_text = json.dumps(stories, indent=2)
        
        return f"""Analyze the following user stories and provide sprint planning recommendations:

Team Velocity: {team_velocity} story points per sprint
Sprint Duration: {sprint_duration} days

User Stories:
{stories_text}

Please provide:
1. Recommended story allocation for the next sprint
2. Dependencies and sequencing
3. Risk assessment for each story
4. Suggested story point adjustments (if needed)
5. Sprint goal recommendation
6. Capacity planning insights
7. Potential blockers and mitigation strategies

Consider team velocity, dependencies, and story complexity in your recommendations."""

    @staticmethod
    def velocity_analysis(
        historical_data: List[Dict[str, Any]],
        current_sprint: Dict[str, Any]
    ) -> str:
        """Generate velocity analysis prompt."""
        history_text = json.dumps(historical_data, indent=2)
        current_text = json.dumps(current_sprint, indent=2)
        
        return f"""Analyze team velocity and provide predictive insights:

Historical Sprint Data:
{history_text}

Current Sprint:
{current_text}

Please provide:
1. Velocity trend analysis
2. Predicted velocity for next 3 sprints
3. Factors affecting velocity (positive and negative)
4. Recommendations for velocity improvement
5. Risk indicators based on current progress
6. Confidence level in predictions
7. Actionable insights for the team

Use statistical analysis and consider seasonal patterns, team changes, and project complexity."""


class AIServiceFactory:
    """Factory for creating AI service instances."""
    
    _instances: Dict[AIProvider, BaseAIService] = {}
    
    @classmethod
    async def get_service(
        cls,
        provider: Optional[AIProvider] = None,
        model: Optional[str] = None
    ) -> BaseAIService:
        """Get AI service instance."""
        if provider is None:
            provider = AIProvider(settings.DEFAULT_LLM_PROVIDER)
            
        # Return cached instance if available
        if provider in cls._instances:
            return cls._instances[provider]
            
        # Create new instance based on provider
        if provider == AIProvider.OPENAI:
            from backend.src.services.ai.openai_service import OpenAIService
            service = OpenAIService(api_key=settings.OPENAI_API_KEY)
        elif provider == AIProvider.ANTHROPIC:
            from backend.src.services.ai.anthropic_service import AnthropicService
            service = AnthropicService(api_key=settings.ANTHROPIC_API_KEY)
        elif provider == AIProvider.OLLAMA:
            from backend.src.services.ai.ollama_service import OllamaService
            service = OllamaService()
        elif provider == AIProvider.MOCK:
            from backend.src.services.ai.mock_service import MockAIService
            service = MockAIService()
        else:
            raise ValueError(f"Unsupported AI provider: {provider}")
            
        # Initialize and cache
        await service.initialize()
        cls._instances[provider] = service
        
        return service
        
    @classmethod
    async def cleanup(cls):
        """Cleanup all service instances."""
        for service in cls._instances.values():
            await service.close()
        cls._instances.clear()