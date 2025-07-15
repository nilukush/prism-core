"""
AI/LLM-related Pydantic schemas.
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict

from backend.src.schemas.common import TimestampMixin


class AIProvider(str, Enum):
    """AI provider enum."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    COHERE = "cohere"
    HUGGINGFACE = "huggingface"
    OLLAMA = "ollama"
    CUSTOM = "custom"


class AIModelType(str, Enum):
    """AI model type."""
    CHAT = "chat"
    COMPLETION = "completion"
    EMBEDDING = "embedding"
    CLASSIFICATION = "classification"
    GENERATION = "generation"


class ContentType(str, Enum):
    """Content type for generation."""
    USER_STORY = "user_story"
    ACCEPTANCE_CRITERIA = "acceptance_criteria"
    TEST_CASES = "test_cases"
    DOCUMENTATION = "documentation"
    CODE_REVIEW = "code_review"
    MEETING_SUMMARY = "meeting_summary"
    REQUIREMENTS = "requirements"
    TECHNICAL_SPEC = "technical_spec"
    RELEASE_NOTES = "release_notes"
    CUSTOM = "custom"


class AnalysisType(str, Enum):
    """Analysis type."""
    SENTIMENT = "sentiment"
    SUMMARY = "summary"
    KEY_POINTS = "key_points"
    ENTITIES = "entities"
    CLASSIFICATION = "classification"
    TRANSLATION = "translation"
    GRAMMAR_CHECK = "grammar_check"


class ChatMessage(BaseModel):
    """Chat message schema."""
    role: str = Field(pattern="^(system|user|assistant)$")
    content: str
    name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class GenerateContentRequest(BaseModel):
    """Request for content generation."""
    type: ContentType = Field(description="Type of content to generate")
    context: Dict[str, Any] = Field(description="Context for generation")
    template_id: Optional[UUID] = Field(default=None, description="Template to use")
    model_provider: Optional[AIProvider] = Field(default=AIProvider.OPENAI)
    model_name: Optional[str] = Field(default="gpt-3.5-turbo")
    temperature: Optional[float] = Field(default=0.7, ge=0, le=2)
    max_tokens: Optional[int] = Field(default=2000, ge=1, le=32000)
    language: Optional[str] = Field(default="en", description="Output language")
    additional_instructions: Optional[str] = None


class GenerateContentResponse(BaseModel):
    """Response from content generation."""
    content: str = Field(description="Generated content")
    type: ContentType
    model_used: str
    tokens_used: int
    generation_time_ms: int
    cost_estimate: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(from_attributes=True)


class AnalyzeTextRequest(BaseModel):
    """Request for text analysis."""
    text: str = Field(min_length=1, max_length=50000, description="Text to analyze")
    analysis_types: List[AnalysisType] = Field(description="Types of analysis to perform")
    language: Optional[str] = Field(default=None, description="Text language")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict)


class AnalyzeTextResponse(BaseModel):
    """Response from text analysis."""
    results: Dict[str, Any] = Field(description="Analysis results by type")
    text_stats: Dict[str, int] = Field(description="Text statistics")
    language_detected: Optional[str] = None
    confidence_scores: Dict[str, float] = Field(default_factory=dict)
    
    model_config = ConfigDict(from_attributes=True)


class ChatCompletionRequest(BaseModel):
    """Request for chat completion."""
    messages: List[ChatMessage] = Field(description="Chat messages")
    model_provider: Optional[AIProvider] = Field(default=AIProvider.OPENAI)
    model_name: Optional[str] = Field(default="gpt-3.5-turbo")
    temperature: Optional[float] = Field(default=0.7, ge=0, le=2)
    max_tokens: Optional[int] = Field(default=2000, ge=1, le=32000)
    stream: bool = Field(default=False, description="Stream response")
    workspace_id: Optional[UUID] = Field(default=None, description="Workspace context")
    project_id: Optional[UUID] = Field(default=None, description="Project context")
    save_conversation: bool = Field(default=True)


class ChatCompletionResponse(BaseModel):
    """Response from chat completion."""
    message: ChatMessage
    conversation_id: Optional[UUID] = None
    model_used: str
    tokens_used: int
    finish_reason: str
    
    model_config = ConfigDict(from_attributes=True)


class AIModelInfo(BaseModel):
    """AI model information."""
    provider: AIProvider
    name: str
    type: AIModelType
    description: Optional[str] = None
    max_tokens: int
    supports_streaming: bool = False
    supports_functions: bool = False
    cost_per_1k_tokens: Optional[float] = None
    
    model_config = ConfigDict(from_attributes=True)


class AIModelListResponse(BaseModel):
    """List of available AI models."""
    models: List[AIModelInfo]
    default_model: str
    
    model_config = ConfigDict(from_attributes=True)


class AIConversation(BaseModel, TimestampMixin):
    """AI conversation/chat history."""
    id: UUID
    workspace_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    user_id: UUID
    title: str
    messages: List[ChatMessage]
    model_provider: AIProvider
    model_name: str
    total_tokens: int
    total_cost: Optional[float] = None
    
    model_config = ConfigDict(from_attributes=True)


class AIUsageStats(BaseModel):
    """AI usage statistics."""
    period: str = Field(description="Time period")
    total_requests: int
    total_tokens: int
    total_cost: float
    by_provider: Dict[str, int]
    by_model: Dict[str, int]
    by_content_type: Dict[str, int]
    by_user: Dict[str, int]
    average_tokens_per_request: float
    
    model_config = ConfigDict(from_attributes=True)


class EmbeddingRequest(BaseModel):
    """Request for text embedding."""
    texts: List[str] = Field(description="Texts to embed")
    model_provider: Optional[AIProvider] = Field(default=AIProvider.OPENAI)
    model_name: Optional[str] = Field(default="text-embedding-ada-002")
    
    
class EmbeddingResponse(BaseModel):
    """Response from embedding generation."""
    embeddings: List[List[float]] = Field(description="Generated embeddings")
    model_used: str
    dimensions: int
    tokens_used: int
    
    model_config = ConfigDict(from_attributes=True)


class SemanticSearchRequest(BaseModel):
    """Request for semantic search."""
    query: str = Field(description="Search query")
    workspace_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    document_types: Optional[List[str]] = None
    limit: int = Field(default=10, ge=1, le=100)
    threshold: float = Field(default=0.7, ge=0, le=1)


class SemanticSearchResult(BaseModel):
    """Semantic search result."""
    id: UUID
    type: str
    title: str
    content: str
    score: float
    metadata: Dict[str, Any]
    
    model_config = ConfigDict(from_attributes=True)


class SemanticSearchResponse(BaseModel):
    """Response from semantic search."""
    results: List[SemanticSearchResult]
    query_embedding_generated: bool
    search_time_ms: int
    
    model_config = ConfigDict(from_attributes=True)