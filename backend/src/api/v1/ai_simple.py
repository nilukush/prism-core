"""
Simplified AI endpoints for testing.
"""

from typing import Dict, Any
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["AI"])


class PRDRequest(BaseModel):
    product_name: str
    description: str
    target_audience: str
    key_features: list[str]
    provider: str = "mock"


@router.post("/generate/prd")
async def generate_prd(request: PRDRequest) -> Dict[str, Any]:
    """Generate a mock PRD for testing."""
    
    mock_prd = f"""# Product Requirements Document

## Product: {request.product_name}

### Description
{request.description}

### Target Audience
{request.target_audience}

### Key Features
{chr(10).join(f"- {feature}" for feature in request.key_features)}

### Executive Summary
This PRD outlines the requirements for {request.product_name}, designed to serve {request.target_audience}.

### Success Metrics
- User adoption rate > 80%
- Customer satisfaction score > 4.5/5
- Feature usage rate > 70%

### Technical Requirements
- Scalable architecture
- 99.9% uptime
- Response time < 200ms

This is a mock PRD generated for testing purposes.
"""
    
    return {
        "success": True,
        "prd": mock_prd,
        "metadata": {
            "provider": request.provider,
            "model": "mock-model",
            "tokens_used": len(mock_prd.split())
        }
    }


@router.get("/test")
async def test_endpoint():
    """Simple test endpoint."""
    return {"status": "AI endpoints working"}