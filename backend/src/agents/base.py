"""
Base agent class for all AI agents.
Provides common functionality and interfaces.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic
from datetime import datetime
import hashlib
import json

from pydantic import BaseModel, Field
from langchain.chat_models.base import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.schema import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain.callbacks import AsyncCallbackHandler

from backend.src.core.config import settings
from backend.src.core.logging import get_logger
from backend.src.core.cache_unified import cache, agent_cache_key
from backend.src.core.monitoring import track_llm_request, track_agent_execution

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


class AgentError(Exception):
    """Base exception for agent errors."""
    pass


class AgentResult(BaseModel):
    """Standard result format for agents."""
    
    success: bool = Field(description="Whether the agent execution was successful")
    data: Optional[Any] = Field(default=None, description="Result data")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    execution_time: float = Field(description="Execution time in seconds")
    cached: bool = Field(default=False, description="Whether result was from cache")
    model_used: Optional[str] = Field(default=None, description="LLM model used")
    tokens_used: Optional[Dict[str, int]] = Field(default=None, description="Token usage")


class AgentCallbackHandler(AsyncCallbackHandler):
    """Callback handler for tracking agent metrics."""
    
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.start_time = None
        self.tokens = {"prompt": 0, "completion": 0}
    
    async def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs) -> None:
        """Called when LLM starts."""
        self.start_time = datetime.utcnow()
    
    async def on_llm_end(self, response: Any, **kwargs) -> None:
        """Called when LLM ends."""
        if self.start_time:
            duration = (datetime.utcnow() - self.start_time).total_seconds()
            
            # Extract token usage if available
            if hasattr(response, "llm_output") and response.llm_output:
                token_usage = response.llm_output.get("token_usage", {})
                self.tokens["prompt"] = token_usage.get("prompt_tokens", 0)
                self.tokens["completion"] = token_usage.get("completion_tokens", 0)
            
            # Track metrics
            track_llm_request(
                provider=settings.DEFAULT_LLM_PROVIDER,
                model=settings.DEFAULT_LLM_MODEL,
                status="success",
                duration=duration,
                prompt_tokens=self.tokens["prompt"],
                completion_tokens=self.tokens["completion"],
            )


class BaseAgent(ABC, Generic[T]):
    """Base class for all AI agents."""
    
    def __init__(
        self,
        name: str,
        description: str,
        llm_provider: Optional[str] = None,
        llm_model: Optional[str] = None,
        temperature: Optional[float] = None,
        cache_ttl: Optional[int] = 3600,
    ):
        """
        Initialize base agent.
        
        Args:
            name: Agent name
            description: Agent description
            llm_provider: LLM provider to use
            llm_model: LLM model to use
            temperature: Temperature for generation
            cache_ttl: Cache TTL in seconds
        """
        self.name = name
        self.description = description
        self.llm_provider = llm_provider or settings.DEFAULT_LLM_PROVIDER
        self.llm_model = llm_model or settings.DEFAULT_LLM_MODEL
        self.temperature = temperature or settings.LLM_TEMPERATURE
        self.cache_ttl = cache_ttl
        
        # Initialize LLM
        self.llm = self._create_llm()
        
        # Set up callback handler
        self.callback_handler = AgentCallbackHandler(self.name)
    
    def _create_llm(self) -> BaseChatModel:
        """Create LLM instance based on provider."""
        config = settings.get_llm_config(self.llm_provider)
        config["temperature"] = self.temperature
        
        if self.llm_provider == "openai":
            return ChatOpenAI(
                model=self.llm_model,
                api_key=config["api_key"],
                organization=config.get("organization"),
                base_url=config.get("base_url"),
                temperature=self.temperature,
                max_tokens=config.get("max_tokens"),
                timeout=config.get("timeout"),
            )
        elif self.llm_provider == "anthropic":
            return ChatAnthropic(
                model=self.llm_model or "claude-3-opus-20240229",
                anthropic_api_key=config["api_key"],
                temperature=self.temperature,
                max_tokens=config.get("max_tokens"),
                timeout=config.get("timeout"),
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")
    
    def _generate_cache_key(self, input_data: Dict[str, Any]) -> str:
        """Generate cache key for input data."""
        # Create stable hash of input
        input_str = json.dumps(input_data, sort_keys=True)
        input_hash = hashlib.md5(input_str.encode()).hexdigest()
        return agent_cache_key(self.name, input_hash)
    
    async def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Get result from cache."""
        if self.cache_ttl <= 0:
            return None
        
        try:
            cached_result = await cache.get(cache_key)
            if cached_result:
                logger.debug("agent_cache_hit", agent=self.name, key=cache_key)
                return cached_result
        except Exception as e:
            logger.warning("agent_cache_error", agent=self.name, error=str(e))
        
        return None
    
    async def _save_to_cache(self, cache_key: str, result: Any) -> None:
        """Save result to cache."""
        if self.cache_ttl <= 0:
            return
        
        try:
            await cache.set(cache_key, result, ttl=self.cache_ttl)
            logger.debug("agent_cache_saved", agent=self.name, key=cache_key)
        except Exception as e:
            logger.warning("agent_cache_save_error", agent=self.name, error=str(e))
    
    @abstractmethod
    async def _process(self, input_data: Dict[str, Any]) -> T:
        """
        Process input and return result.
        
        Args:
            input_data: Input data for processing
            
        Returns:
            Processed result
        """
        pass
    
    @abstractmethod
    def _validate_input(self, input_data: Dict[str, Any]) -> None:
        """
        Validate input data.
        
        Args:
            input_data: Input data to validate
            
        Raises:
            AgentError: If validation fails
        """
        pass
    
    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Execute agent with input data.
        
        Args:
            input_data: Input data for agent
            
        Returns:
            Agent execution result
        """
        start_time = datetime.utcnow()
        
        try:
            # Validate input
            self._validate_input(input_data)
            
            # Check cache
            cache_key = self._generate_cache_key(input_data)
            cached_result = await self._get_from_cache(cache_key)
            
            if cached_result:
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                track_agent_execution(self.name, "cache_hit", execution_time)
                
                return AgentResult(
                    success=True,
                    data=cached_result,
                    execution_time=execution_time,
                    cached=True,
                    model_used=self.llm_model,
                )
            
            # Process input
            result = await self._process(input_data)
            
            # Save to cache
            await self._save_to_cache(cache_key, result)
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Track metrics
            track_agent_execution(self.name, "success", execution_time)
            
            return AgentResult(
                success=True,
                data=result,
                execution_time=execution_time,
                model_used=self.llm_model,
                tokens_used={
                    "prompt": self.callback_handler.tokens["prompt"],
                    "completion": self.callback_handler.tokens["completion"],
                },
            )
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.error(
                "agent_execution_failed",
                agent=self.name,
                error=str(e),
                execution_time=execution_time,
            )
            
            # Track metrics
            track_agent_execution(self.name, "error", execution_time)
            
            return AgentResult(
                success=False,
                error=str(e),
                execution_time=execution_time,
                model_used=self.llm_model,
            )
    
    def create_messages(
        self,
        system_prompt: str,
        user_prompt: str,
        history: Optional[List[BaseMessage]] = None,
    ) -> List[BaseMessage]:
        """
        Create message list for LLM.
        
        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            history: Optional conversation history
            
        Returns:
            List of messages
        """
        messages = [SystemMessage(content=system_prompt)]
        
        if history:
            messages.extend(history)
        
        messages.append(HumanMessage(content=user_prompt))
        
        return messages
    
    async def generate(
        self,
        messages: List[BaseMessage],
        **kwargs
    ) -> str:
        """
        Generate response from LLM.
        
        Args:
            messages: Messages to send to LLM
            **kwargs: Additional arguments for LLM
            
        Returns:
            Generated response
        """
        response = await self.llm.ainvoke(
            messages,
            callbacks=[self.callback_handler],
            **kwargs
        )
        
        return response.content