"""
Agent Executor Service for running AI agents.
"""

from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime
import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.src.models.agent import Agent, AgentExecution
from backend.src.models.user import User
from backend.src.schemas.agent import ExecutionStatus, AgentExecutionCreate
from backend.src.core.database import get_db
from backend.src.core.config import settings
from backend.src.integrations.openai_client import OpenAIClient
from backend.src.integrations.anthropic_client import AnthropicClient

logger = logging.getLogger(__name__)


class AgentExecutorService:
    """Service for executing AI agents."""
    
    def __init__(self):
        """Initialize the agent executor service."""
        self.openai_client = OpenAIClient()
        self.anthropic_client = AnthropicClient()
        self._execution_queue = asyncio.Queue()
        self._workers = []
    
    async def execute_agent(
        self,
        db: AsyncSession,
        agent_id: UUID,
        execution_data: AgentExecutionCreate,
        user: Optional[User] = None
    ) -> AgentExecution:
        """
        Execute an agent with the given input data.
        
        Args:
            db: Database session
            agent_id: Agent ID to execute
            execution_data: Execution input data
            user: User triggering the execution
            
        Returns:
            AgentExecution instance
        """
        # Get agent
        result = await db.execute(
            select(Agent).where(Agent.id == agent_id)
        )
        agent = result.scalar_one_or_none()
        
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        
        if agent.status != "active":
            raise ValueError(f"Agent {agent_id} is not active")
        
        # Create execution record
        execution = AgentExecution(
            agent_id=agent_id,
            agent_version=agent.version,
            status=ExecutionStatus.PENDING,
            input_data=execution_data.input_data,
            context=execution_data.context,
            parameters=execution_data.parameters or agent.parameters,
            executed_by_id=user.id if user else None
        )
        
        db.add(execution)
        await db.commit()
        await db.refresh(execution)
        
        # Queue for async processing
        await self._execution_queue.put({
            "execution_id": execution.id,
            "agent": agent,
            "timeout": execution_data.timeout_seconds
        })
        
        return execution
    
    async def _process_execution(self, execution_data: Dict[str, Any]):
        """Process a single agent execution."""
        execution_id = execution_data["execution_id"]
        agent = execution_data["agent"]
        timeout = execution_data.get("timeout", 300)
        
        async with get_db() as db:
            try:
                # Get execution
                result = await db.execute(
                    select(AgentExecution).where(AgentExecution.id == execution_id)
                )
                execution = result.scalar_one()
                
                # Update status to running
                execution.status = ExecutionStatus.RUNNING
                execution.started_at = datetime.utcnow()
                await db.commit()
                
                # Execute based on provider
                if agent.model_provider == "openai":
                    output = await self._execute_openai(agent, execution)
                elif agent.model_provider == "anthropic":
                    output = await self._execute_anthropic(agent, execution)
                else:
                    raise ValueError(f"Unsupported provider: {agent.model_provider}")
                
                # Update execution with results
                execution.status = ExecutionStatus.COMPLETED
                execution.output_data = output["result"]
                execution.tokens_used = output.get("tokens_used", 0)
                execution.cost_usd = output.get("cost", 0.0)
                execution.completed_at = datetime.utcnow()
                execution.duration_ms = int(
                    (execution.completed_at - execution.started_at).total_seconds() * 1000
                )
                
                # Update agent metrics
                agent.execution_count += 1
                agent.last_executed_at = datetime.utcnow()
                
                await db.commit()
                
            except asyncio.TimeoutError:
                execution.status = ExecutionStatus.TIMEOUT
                execution.error_message = f"Execution timed out after {timeout} seconds"
                await db.commit()
                
            except Exception as e:
                logger.error(f"Agent execution failed: {str(e)}")
                execution.status = ExecutionStatus.FAILED
                execution.error_message = str(e)
                execution.error_details = {"type": type(e).__name__}
                await db.commit()
    
    async def _execute_openai(self, agent: Agent, execution: AgentExecution) -> Dict[str, Any]:
        """Execute agent using OpenAI."""
        # Build messages
        messages = []
        
        if agent.system_prompt:
            messages.append({"role": "system", "content": agent.system_prompt})
        
        if agent.instructions:
            messages.append({"role": "system", "content": agent.instructions})
        
        # Add input as user message
        user_message = execution.input_data.get("prompt", str(execution.input_data))
        messages.append({"role": "user", "content": user_message})
        
        # Call OpenAI
        response = await self.openai_client.create_chat_completion(
            model=agent.model_name,
            messages=messages,
            temperature=agent.temperature,
            max_tokens=agent.max_tokens,
            tools=agent.tools if agent.tools else None
        )
        
        return {
            "result": {
                "content": response["choices"][0]["message"]["content"],
                "model": agent.model_name,
                "finish_reason": response["choices"][0]["finish_reason"]
            },
            "tokens_used": response["usage"]["total_tokens"],
            "cost": self._calculate_cost(
                agent.model_name,
                response["usage"]["prompt_tokens"],
                response["usage"]["completion_tokens"]
            )
        }
    
    async def _execute_anthropic(self, agent: Agent, execution: AgentExecution) -> Dict[str, Any]:
        """Execute agent using Anthropic."""
        # Build messages
        system_content = []
        if agent.system_prompt:
            system_content.append(agent.system_prompt)
        if agent.instructions:
            system_content.append(agent.instructions)
        
        # Call Anthropic
        response = await self.anthropic_client.create_message(
            model=agent.model_name,
            system="\n\n".join(system_content) if system_content else None,
            messages=[{
                "role": "user",
                "content": execution.input_data.get("prompt", str(execution.input_data))
            }],
            temperature=agent.temperature,
            max_tokens=agent.max_tokens
        )
        
        return {
            "result": {
                "content": response["content"][0]["text"],
                "model": agent.model_name,
                "stop_reason": response["stop_reason"]
            },
            "tokens_used": response["usage"]["input_tokens"] + response["usage"]["output_tokens"],
            "cost": self._calculate_cost(
                agent.model_name,
                response["usage"]["input_tokens"],
                response["usage"]["output_tokens"]
            )
        }
    
    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on model and token usage."""
        # Simplified pricing - should be loaded from config
        pricing = {
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
            "gpt-4": {"input": 0.03, "output": 0.06},
            "claude-3-opus": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet": {"input": 0.003, "output": 0.015}
        }
        
        model_pricing = pricing.get(model, {"input": 0.001, "output": 0.002})
        return (input_tokens * model_pricing["input"] + output_tokens * model_pricing["output"]) / 1000
    
    async def start_workers(self, num_workers: int = 3):
        """Start background workers for processing executions."""
        for i in range(num_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self._workers.append(worker)
    
    async def stop_workers(self):
        """Stop all background workers."""
        for worker in self._workers:
            worker.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
    
    async def _worker(self, name: str):
        """Background worker for processing executions."""
        logger.info(f"Starting agent executor worker: {name}")
        
        while True:
            try:
                execution_data = await self._execution_queue.get()
                await self._process_execution(execution_data)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {name} error: {str(e)}")


# Global instance
agent_executor_service = AgentExecutorService()