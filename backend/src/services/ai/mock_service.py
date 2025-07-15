"""
Mock AI service for testing.
"""

import asyncio
import json
import random
from typing import AsyncGenerator
from datetime import datetime

from backend.src.services.ai.base import (
    BaseAIService, AIProvider, AIRequest, AIResponse
)
from backend.src.core.logging import logger


class MockAIService(BaseAIService):
    """Mock AI service for testing without real API calls."""
    
    def __init__(self):
        super().__init__(AIProvider.MOCK, api_key="mock-key")
        self.responses = {
            "prd": self._generate_mock_prd,
            "story": self._generate_mock_story,
            "sprint": self._generate_mock_sprint_estimation,
            "velocity": self._generate_mock_velocity_analysis,
            "default": self._generate_default_response
        }
        
    async def initialize(self):
        """Initialize mock service."""
        logger.info("mock_ai_service_initialized")
        
    async def generate(self, request: AIRequest) -> AIResponse:
        """Generate mock response based on prompt content."""
        # Simulate API delay
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        # Determine response type from prompt
        prompt_lower = request.prompt.lower()
        
        if "prd" in prompt_lower or "product requirements" in prompt_lower:
            content = self._generate_mock_prd()
        elif "user stor" in prompt_lower:
            content = self._generate_mock_story()
        elif "sprint" in prompt_lower and "estimat" in prompt_lower:
            content = self._generate_mock_sprint_estimation()
        elif "velocity" in prompt_lower:
            content = self._generate_mock_velocity_analysis()
        else:
            content = self._generate_default_response(request.prompt)
            
        # Mock usage stats
        prompt_tokens = len(request.prompt.split())
        completion_tokens = len(content.split())
        
        return AIResponse(
            content=content,
            model="mock-model",
            provider=self.provider.value,
            usage={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens
            },
            metadata={
                "mock": True,
                "response_type": "generated"
            }
        )
        
    async def stream_generate(self, request: AIRequest) -> AsyncGenerator[str, None]:
        """Stream mock response."""
        response = await self.generate(request)
        
        # Simulate streaming by yielding words
        words = response.content.split()
        for i, word in enumerate(words):
            if i > 0:
                yield " "
            yield word
            await asyncio.sleep(0.05)  # Simulate typing delay
            
    def _generate_mock_prd(self) -> str:
        """Generate mock PRD content."""
        return """# Product Requirements Document (PRD)

## 1. Executive Summary

This PRD outlines the requirements for implementing an AI-powered feature enhancement system that will revolutionize how users interact with our product management platform.

## 2. Problem Statement

Product managers currently spend 40% of their time on repetitive tasks that could be automated. This includes writing user stories, estimating complexity, and analyzing team velocity.

## 3. Objectives and Success Metrics

### Objectives:
- Reduce time spent on story creation by 70%
- Improve estimation accuracy to within 85%
- Increase team productivity by 25%

### Success Metrics:
- Time to create user stories: < 2 minutes (from 15 minutes)
- Estimation accuracy: > 85% (from 60%)
- User satisfaction score: > 4.5/5

## 4. User Personas

### Primary: Product Manager
- Needs: Quick story creation, accurate estimations
- Pain points: Repetitive tasks, inconsistent formatting

### Secondary: Development Team
- Needs: Clear requirements, realistic timelines
- Pain points: Ambiguous stories, poor estimates

## 5. User Stories and Use Cases

### Story 1: AI-Powered Story Generation
As a product manager, I want to generate user stories from high-level requirements, so that I can focus on strategic planning.

### Story 2: Intelligent Sprint Planning
As a scrum master, I want AI to suggest optimal sprint compositions, so that we maximize team velocity.

## 6. Functional Requirements

- AI story generation with customizable templates
- Real-time estimation based on historical data
- Sprint optimization algorithms
- Integration with existing tools

## 7. Non-Functional Requirements

- Response time < 2 seconds
- 99.9% uptime
- GDPR compliant
- SOC2 certified

## 8. Technical Architecture Overview

- Microservices architecture
- OpenAI GPT-4 for NLP
- Redis for caching
- PostgreSQL for data persistence

## 9. Dependencies and Risks

### Dependencies:
- OpenAI API availability
- Historical data quality

### Risks:
- AI hallucination mitigation required
- Data privacy concerns

## 10. Timeline and Milestones

- Phase 1 (Weeks 1-4): Core AI integration
- Phase 2 (Weeks 5-8): Sprint optimization
- Phase 3 (Weeks 9-12): Analytics and reporting

## 11. Open Questions

- Preferred AI model for different use cases?
- Integration priority with third-party tools?
- Custom training data requirements?"""
        
    def _generate_mock_story(self) -> str:
        """Generate mock user story."""
        return json.dumps([
            {
                "title": "Implement AI Story Generation",
                "story": "As a product manager, I want to generate user stories using AI, so that I can create comprehensive stories faster",
                "acceptance_criteria": [
                    "Given I have a high-level requirement, When I click 'Generate Story', Then AI creates a detailed user story",
                    "Given the AI generates a story, When I review it, Then I can edit any part before saving",
                    "Given I save an AI story, When I view analytics, Then generation metrics are tracked"
                ],
                "story_points": 8,
                "priority": "High",
                "dependencies": ["AI Service Integration"],
                "test_scenarios": [
                    "Test story generation with various input lengths",
                    "Verify edit functionality works correctly",
                    "Confirm metrics are accurately tracked"
                ]
            },
            {
                "title": "Add Story Template Management",
                "story": "As a team lead, I want to manage story templates, so that our team maintains consistent formatting",
                "acceptance_criteria": [
                    "Given I'm an admin, When I access settings, Then I can create custom templates",
                    "Given templates exist, When generating stories, Then I can select which template to use",
                    "Given I update a template, When team uses it, Then they see the latest version"
                ],
                "story_points": 5,
                "priority": "Medium",
                "dependencies": [],
                "test_scenarios": [
                    "Create, update, and delete templates",
                    "Verify template selection in story generation",
                    "Test template versioning"
                ]
            }
        ], indent=2)
        
    def _generate_mock_sprint_estimation(self) -> str:
        """Generate mock sprint estimation."""
        return json.dumps({
            "recommended_stories": [
                {"id": "STORY-123", "points": 8, "title": "Implement AI Story Generation"},
                {"id": "STORY-124", "points": 5, "title": "Add Story Template Management"},
                {"id": "STORY-125", "points": 3, "title": "Create Analytics Dashboard"}
            ],
            "total_points": 16,
            "confidence": 0.85,
            "sprint_goal": "Deliver core AI features for story management",
            "risks": [
                {
                    "story_id": "STORY-123",
                    "risk": "OpenAI API integration complexity",
                    "mitigation": "Spike in current sprint to validate approach"
                }
            ],
            "dependencies": {
                "STORY-124": ["STORY-123"],
                "STORY-125": ["STORY-124"]
            },
            "capacity_analysis": {
                "available_capacity": 20,
                "allocated_capacity": 16,
                "buffer_percentage": 20,
                "recommendation": "Sprint is well-balanced with appropriate buffer"
            }
        }, indent=2)
        
    def _generate_mock_velocity_analysis(self) -> str:
        """Generate mock velocity analysis."""
        return json.dumps({
            "velocity_trend": {
                "current": 22,
                "average_last_3": 20,
                "average_last_6": 18,
                "trend": "increasing",
                "confidence": 0.78
            },
            "predictions": {
                "next_sprint": 23,
                "sprint_plus_2": 24,
                "sprint_plus_3": 24,
                "confidence_interval": [20, 26]
            },
            "factors": {
                "positive": [
                    "Team familiarity with codebase increasing",
                    "CI/CD improvements reducing deployment time",
                    "Better story refinement process"
                ],
                "negative": [
                    "Upcoming team member vacation",
                    "Technical debt accumulation",
                    "External dependency delays"
                ]
            },
            "recommendations": [
                "Allocate 20% of sprint for technical debt",
                "Consider pair programming for knowledge transfer",
                "Implement automated testing to maintain velocity"
            ],
            "risk_indicators": [
                {
                    "indicator": "Increasing bug rate",
                    "severity": "medium",
                    "impact": "May reduce velocity by 10-15%"
                }
            ]
        }, indent=2)
        
    def _generate_default_response(self, prompt: str) -> str:
        """Generate default mock response."""
        return f"""Based on your request: "{prompt[:100]}..."

Here's a comprehensive response:

1. **Analysis**: I've analyzed your requirements and identified key areas for improvement.

2. **Recommendations**:
   - Implement automated workflows to reduce manual effort
   - Use AI-powered insights for better decision making
   - Focus on metrics that matter for your team

3. **Next Steps**:
   - Prioritize high-impact features
   - Gather team feedback
   - Iterate based on results

4. **Expected Outcomes**:
   - 30% improvement in efficiency
   - Better team collaboration
   - Data-driven decision making

This is a mock response for testing purposes. In production, this would be replaced with actual AI-generated content tailored to your specific needs."""