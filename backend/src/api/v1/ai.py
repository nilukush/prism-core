"""
AI-powered features API endpoints.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field

from backend.src.api.deps import get_current_user
from backend.src.models.user import User
from backend.src.services.ai.base import (
    AIServiceFactory, AIProvider, AIRequest, PromptTemplate
)
from backend.src.middleware.rate_limiting import rate_limit
from backend.src.core.logging import logger
from backend.src.core.telemetry import trace_async
from backend.src.core.config import settings

router = APIRouter(tags=["AI"])


class PRDGenerationRequest(BaseModel):
    """PRD generation request."""
    product_name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    target_audience: str = Field(..., min_length=5, max_length=500)
    key_features: List[str] = Field(..., min_items=1, max_items=10)
    constraints: Optional[List[str]] = Field(default=None, max_items=10)
    provider: Optional[AIProvider] = None
    stream: bool = False


class UserStoryGenerationRequest(BaseModel):
    """User story generation request."""
    requirement: str = Field(..., min_length=10, max_length=1000)
    context: Optional[str] = Field(default=None, max_length=1000)
    story_count: int = Field(default=3, ge=1, le=10)
    include_acceptance_criteria: bool = True
    include_test_scenarios: bool = True
    provider: Optional[AIProvider] = None


class SprintEstimationRequest(BaseModel):
    """Sprint estimation request."""
    stories: List[Dict[str, Any]] = Field(..., min_items=1, max_items=50)
    team_velocity: int = Field(..., ge=1, le=200)
    sprint_duration: int = Field(default=14, ge=1, le=30)
    include_risks: bool = True
    include_dependencies: bool = True
    provider: Optional[AIProvider] = None


class VelocityAnalysisRequest(BaseModel):
    """Velocity analysis request."""
    historical_data: List[Dict[str, Any]] = Field(..., min_items=2, max_items=20)
    current_sprint: Dict[str, Any]
    prediction_sprints: int = Field(default=3, ge=1, le=6)
    include_recommendations: bool = True
    provider: Optional[AIProvider] = None


class AIAssistantRequest(BaseModel):
    """General AI assistant request."""
    query: str = Field(..., min_length=5, max_length=2000)
    context: Optional[Dict[str, Any]] = None
    provider: Optional[AIProvider] = None
    stream: bool = False


@router.post("/generate/prd")
@rate_limit(requests_per_minute=10, requests_per_hour=100)
@trace_async("ai_generate_prd")
async def generate_prd(
    request: Request,
    prd_request: PRDGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Generate a Product Requirements Document using AI.
    
    This endpoint creates a comprehensive PRD based on the provided inputs.
    """
    logger.info(
        "prd_generation_request",
        user_id=current_user.id,
        product_name=prd_request.product_name,
        provider=prd_request.provider.value if prd_request.provider else settings.DEFAULT_LLM_PROVIDER
    )
    
    # Get AI service
    ai_service = await AIServiceFactory.get_service(prd_request.provider)
    
    # Generate prompt
    prompt = PromptTemplate.prd_generation(
        product_name=prd_request.product_name,
        description=prd_request.description,
        target_audience=prd_request.target_audience,
        key_features=prd_request.key_features,
        constraints=prd_request.constraints
    )
    
    # Create AI request
    ai_request = AIRequest(
        prompt=prompt,
        system_prompt=PromptTemplate.system_prompt(),
        temperature=0.7,
        max_tokens=4000
    )
    
    try:
        if prd_request.stream:
            # Stream response
            async def generate():
                async for chunk in ai_service.stream_generate(ai_request):
                    yield chunk
                    
            return StreamingResponse(
                generate(),
                media_type="text/plain"
            )
        else:
            # Generate complete response
            response = await ai_service.generate(ai_request)
            
            # Track usage in background
            background_tasks.add_task(
                _track_ai_usage,
                user_id=current_user.id,
                operation="prd_generation",
                provider=prd_request.provider.value if prd_request.provider else settings.DEFAULT_LLM_PROVIDER,
                tokens=response.usage
            )
            
            return JSONResponse(
                content={
                    "success": True,
                    "prd": response.content,
                    "metadata": {
                        "generated_at": datetime.utcnow().isoformat(),
                        "model": response.model,
                        "provider": response.provider,
                        "tokens_used": response.usage.get("total_tokens", 0)
                    }
                }
            )
            
    except Exception as e:
        logger.error(
            "prd_generation_error",
            error=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate PRD. Please try again."
        )


@router.post("/generate/stories")
@rate_limit(requests_per_minute=20, requests_per_hour=200)
@trace_async("ai_generate_stories")
async def generate_user_stories(
    request: Request,
    story_request: UserStoryGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Generate user stories from requirements using AI.
    
    Creates detailed user stories with acceptance criteria and test scenarios.
    """
    logger.info(
        "story_generation_request",
        user_id=current_user.id,
        story_count=story_request.story_count,
        provider=story_request.provider.value if story_request.provider else settings.DEFAULT_LLM_PROVIDER
    )
    
    # Get AI service
    ai_service = await AIServiceFactory.get_service(story_request.provider)
    
    # Generate prompt
    prompt = PromptTemplate.user_story_generation(
        requirement=story_request.requirement,
        context=story_request.context,
        story_count=story_request.story_count
    )
    
    # Create AI request with JSON response format
    ai_request = AIRequest(
        prompt=prompt,
        system_prompt=PromptTemplate.system_prompt(),
        temperature=0.8,
        max_tokens=3000,
        response_format={"type": "json_object"}
    )
    
    try:
        response = await ai_service.generate(ai_request)
        
        # Parse JSON response
        try:
            stories = json.loads(response.content)
            if not isinstance(stories, list):
                stories = [stories]
        except json.JSONDecodeError:
            # Fallback for non-JSON responses
            stories = [{
                "title": "Generated Story",
                "story": response.content,
                "acceptance_criteria": [],
                "story_points": 0,
                "priority": "Medium"
            }]
        
        # Track usage
        background_tasks.add_task(
            _track_ai_usage,
            user_id=current_user.id,
            operation="story_generation",
            provider=story_request.provider.value if story_request.provider else settings.DEFAULT_LLM_PROVIDER,
            tokens=response.usage
        )
        
        return JSONResponse(
            content={
                "success": True,
                "stories": stories,
                "count": len(stories),
                "metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "model": response.model,
                    "provider": response.provider,
                    "tokens_used": response.usage.get("total_tokens", 0)
                }
            }
        )
        
    except Exception as e:
        logger.error(
            "story_generation_error",
            error=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate user stories. Please try again."
        )


@router.post("/estimate/sprint")
@rate_limit(requests_per_minute=15, requests_per_hour=150)
@trace_async("ai_estimate_sprint")
async def estimate_sprint(
    request: Request,
    sprint_request: SprintEstimationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get AI-powered sprint estimation and recommendations.
    
    Analyzes stories and provides optimal sprint composition.
    """
    logger.info(
        "sprint_estimation_request",
        user_id=current_user.id,
        story_count=len(sprint_request.stories),
        team_velocity=sprint_request.team_velocity
    )
    
    # Get AI service
    ai_service = await AIServiceFactory.get_service(sprint_request.provider)
    
    # Generate prompt
    prompt = PromptTemplate.sprint_estimation(
        stories=sprint_request.stories,
        team_velocity=sprint_request.team_velocity,
        sprint_duration=sprint_request.sprint_duration
    )
    
    # Create AI request
    ai_request = AIRequest(
        prompt=prompt,
        system_prompt=PromptTemplate.system_prompt(),
        temperature=0.6,
        max_tokens=2000,
        response_format={"type": "json_object"}
    )
    
    try:
        response = await ai_service.generate(ai_request)
        
        # Parse JSON response
        try:
            estimation = json.loads(response.content)
        except json.JSONDecodeError:
            estimation = {
                "recommendation": response.content,
                "confidence": 0.7
            }
        
        # Track usage
        background_tasks.add_task(
            _track_ai_usage,
            user_id=current_user.id,
            operation="sprint_estimation",
            provider=sprint_request.provider.value if sprint_request.provider else settings.DEFAULT_LLM_PROVIDER,
            tokens=response.usage
        )
        
        return JSONResponse(
            content={
                "success": True,
                "estimation": estimation,
                "metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "model": response.model,
                    "provider": response.provider,
                    "tokens_used": response.usage.get("total_tokens", 0)
                }
            }
        )
        
    except Exception as e:
        logger.error(
            "sprint_estimation_error",
            error=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to estimate sprint. Please try again."
        )


@router.post("/analyze/velocity")
@rate_limit(requests_per_minute=10, requests_per_hour=100)
@trace_async("ai_analyze_velocity")
async def analyze_velocity(
    request: Request,
    velocity_request: VelocityAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Analyze team velocity and provide predictive insights.
    
    Uses historical data to predict future velocity and identify trends.
    """
    logger.info(
        "velocity_analysis_request",
        user_id=current_user.id,
        historical_sprints=len(velocity_request.historical_data),
        prediction_sprints=velocity_request.prediction_sprints
    )
    
    # Get AI service
    ai_service = await AIServiceFactory.get_service(velocity_request.provider)
    
    # Generate prompt
    prompt = PromptTemplate.velocity_analysis(
        historical_data=velocity_request.historical_data,
        current_sprint=velocity_request.current_sprint
    )
    
    # Create AI request
    ai_request = AIRequest(
        prompt=prompt,
        system_prompt=PromptTemplate.system_prompt(),
        temperature=0.5,
        max_tokens=2500,
        response_format={"type": "json_object"}
    )
    
    try:
        response = await ai_service.generate(ai_request)
        
        # Parse JSON response
        try:
            analysis = json.loads(response.content)
        except json.JSONDecodeError:
            analysis = {
                "analysis": response.content,
                "confidence": 0.75
            }
        
        # Track usage
        background_tasks.add_task(
            _track_ai_usage,
            user_id=current_user.id,
            operation="velocity_analysis",
            provider=velocity_request.provider.value if velocity_request.provider else settings.DEFAULT_LLM_PROVIDER,
            tokens=response.usage
        )
        
        return JSONResponse(
            content={
                "success": True,
                "analysis": analysis,
                "metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "model": response.model,
                    "provider": response.provider,
                    "tokens_used": response.usage.get("total_tokens", 0)
                }
            }
        )
        
    except Exception as e:
        logger.error(
            "velocity_analysis_error",
            error=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze velocity. Please try again."
        )


@router.post("/assistant/chat")
@rate_limit(requests_per_minute=30, requests_per_hour=300)
@trace_async("ai_assistant_chat")
async def ai_assistant_chat(
    request: Request,
    assistant_request: AIAssistantRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    General AI assistant for product management queries.
    
    Handles various product management questions and provides assistance.
    """
    logger.info(
        "ai_assistant_request",
        user_id=current_user.id,
        query_length=len(assistant_request.query),
        provider=assistant_request.provider.value if assistant_request.provider else settings.DEFAULT_LLM_PROVIDER
    )
    
    # Get AI service
    ai_service = await AIServiceFactory.get_service(assistant_request.provider)
    
    # Build context-aware prompt
    context_prompt = ""
    if assistant_request.context:
        context_prompt = f"\n\nContext:\n{json.dumps(assistant_request.context, indent=2)}\n\n"
    
    # Create AI request
    ai_request = AIRequest(
        prompt=f"{context_prompt}User Query: {assistant_request.query}",
        system_prompt=PromptTemplate.system_prompt(),
        temperature=0.7,
        max_tokens=1500
    )
    
    try:
        if assistant_request.stream:
            # Stream response
            async def generate():
                async for chunk in ai_service.stream_generate(ai_request):
                    yield chunk
                    
            return StreamingResponse(
                generate(),
                media_type="text/plain"
            )
        else:
            response = await ai_service.generate(ai_request)
            
            # Track usage
            background_tasks.add_task(
                _track_ai_usage,
                user_id=current_user.id,
                operation="assistant_chat",
                provider=assistant_request.provider.value if assistant_request.provider else settings.DEFAULT_LLM_PROVIDER,
                tokens=response.usage
            )
            
            return JSONResponse(
                content={
                    "success": True,
                    "response": response.content,
                    "metadata": {
                        "generated_at": datetime.utcnow().isoformat(),
                        "model": response.model,
                        "provider": response.provider,
                        "tokens_used": response.usage.get("total_tokens", 0)
                    }
                }
            )
            
    except Exception as e:
        logger.error(
            "ai_assistant_error",
            error=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI assistant encountered an error. Please try again."
        )


@router.get("/usage/stats")
async def get_ai_usage_stats(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get AI usage statistics for the current user.
    
    Returns token usage, operation counts, and cost estimates.
    """
    # TODO: Implement actual usage tracking from database
    return {
        "user_id": current_user.id,
        "current_month": {
            "total_tokens": 45678,
            "total_operations": 234,
            "breakdown": {
                "prd_generation": {"count": 12, "tokens": 15000},
                "story_generation": {"count": 89, "tokens": 20000},
                "sprint_estimation": {"count": 45, "tokens": 5678},
                "velocity_analysis": {"count": 23, "tokens": 3000},
                "assistant_chat": {"count": 65, "tokens": 2000}
            },
            "estimated_cost": 4.57
        },
        "limits": {
            "monthly_tokens": 1000000,
            "daily_operations": 500,
            "rate_limits": {
                "prd_generation": "10/min, 100/hour",
                "story_generation": "20/min, 200/hour",
                "sprint_estimation": "15/min, 150/hour",
                "velocity_analysis": "10/min, 100/hour",
                "assistant_chat": "30/min, 300/hour"
            }
        }
    }


async def _track_ai_usage(
    user_id: int,
    operation: str,
    provider: str,
    tokens: Dict[str, int]
) -> None:
    """Track AI usage for billing and analytics."""
    try:
        logger.info(
            "ai_usage_tracked",
            user_id=user_id,
            operation=operation,
            provider=provider,
            tokens=tokens
        )
        # TODO: Save to database for actual tracking
    except Exception as e:
        logger.error(
            "ai_usage_tracking_error",
            error=str(e),
            user_id=user_id
        )