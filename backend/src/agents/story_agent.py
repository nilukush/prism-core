"""
Story Agent for generating user stories.
Creates well-structured agile user stories with acceptance criteria.
"""

from typing import Dict, Any, List, Optional
import json

from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate

from backend.src.agents.base import BaseAgent, AgentError
from backend.src.core.logging import get_logger

logger = get_logger(__name__)


class UserStoryOutput(BaseModel):
    """Output format for user stories."""
    
    title: str = Field(description="Brief, descriptive title for the story")
    user_type: str = Field(description="Type of user in 'As a...' format")
    user_story: str = Field(description="What the user wants in 'I want...' format")
    benefit: str = Field(description="Why they want it in 'So that...' format")
    acceptance_criteria: List[str] = Field(
        description="List of testable acceptance criteria",
        min_items=3,
        max_items=10
    )
    story_points: Optional[int] = Field(
        description="Estimated story points (1,2,3,5,8,13)",
        default=None
    )
    technical_notes: Optional[str] = Field(
        description="Technical implementation notes",
        default=None
    )
    dependencies: List[str] = Field(
        description="List of dependencies or prerequisites",
        default_factory=list
    )
    risks: List[str] = Field(
        description="Potential risks or challenges",
        default_factory=list
    )


class StoryAgent(BaseAgent[UserStoryOutput]):
    """Agent for generating user stories."""
    
    def __init__(self, **kwargs):
        """Initialize story agent."""
        super().__init__(
            name="story_agent",
            description="Generates well-structured agile user stories",
            **kwargs
        )
        
        # Create output parser
        self.output_parser = PydanticOutputParser(pydantic_object=UserStoryOutput)
        
        # Create prompts
        self.system_prompt = """You are an expert agile coach and product manager who creates clear, 
        well-structured user stories following best practices. Your stories are:
        
        1. Independent - Can be developed and tested on their own
        2. Negotiable - Leave room for discussion and refinement
        3. Valuable - Deliver clear value to users
        4. Estimable - Can be reasonably estimated
        5. Small - Can be completed in one sprint
        6. Testable - Have clear acceptance criteria
        
        Focus on user value and business outcomes rather than technical implementation details.
        Write acceptance criteria using Given-When-Then format when appropriate."""
        
        self.user_prompt_template = PromptTemplate(
            template="""Create a user story based on the following requirement:

Requirement: {requirement}

Context: {context}

Target Users: {target_users}

Priority: {priority}

Additional Notes: {notes}

{format_instructions}

Generate a comprehensive user story that captures the essence of this requirement.""",
            input_variables=["requirement", "context", "target_users", "priority", "notes"],
            partial_variables={"format_instructions": self.output_parser.get_format_instructions()}
        )
    
    def _validate_input(self, input_data: Dict[str, Any]) -> None:
        """Validate input data."""
        if not input_data.get("requirement"):
            raise AgentError("Requirement is required")
        
        if len(input_data["requirement"]) < 10:
            raise AgentError("Requirement is too short")
        
        if len(input_data["requirement"]) > 2000:
            raise AgentError("Requirement is too long")
    
    async def _process(self, input_data: Dict[str, Any]) -> UserStoryOutput:
        """Process input and generate user story."""
        # Extract inputs with defaults
        requirement = input_data["requirement"]
        context = input_data.get("context", "General product development")
        target_users = input_data.get("target_users", "End users")
        priority = input_data.get("priority", "Medium")
        notes = input_data.get("notes", "None provided")
        
        # Format user prompt
        user_prompt = self.user_prompt_template.format(
            requirement=requirement,
            context=context,
            target_users=target_users,
            priority=priority,
            notes=notes
        )
        
        # Create messages
        messages = self.create_messages(self.system_prompt, user_prompt)
        
        # Generate response
        response = await self.generate(messages)
        
        # Parse response
        try:
            story = self.output_parser.parse(response)
            
            # Post-process story points if needed
            if story.story_points and story.story_points not in [1, 2, 3, 5, 8, 13]:
                # Round to nearest Fibonacci number
                fibonacci = [1, 2, 3, 5, 8, 13]
                story.story_points = min(fibonacci, key=lambda x: abs(x - story.story_points))
            
            logger.info(
                "story_generated",
                title=story.title,
                story_points=story.story_points,
                criteria_count=len(story.acceptance_criteria)
            )
            
            return story
            
        except Exception as e:
            logger.error("story_parsing_failed", error=str(e), response=response)
            raise AgentError(f"Failed to parse story: {str(e)}")
    
    async def generate_multiple(
        self,
        requirement: str,
        count: int = 3,
        variations: bool = True,
        **kwargs
    ) -> List[UserStoryOutput]:
        """
        Generate multiple user stories for a requirement.
        
        Args:
            requirement: Base requirement
            count: Number of stories to generate
            variations: Whether to create variations
            **kwargs: Additional input parameters
            
        Returns:
            List of user stories
        """
        stories = []
        
        for i in range(count):
            input_data = {
                "requirement": requirement,
                **kwargs
            }
            
            if variations and i > 0:
                # Add variation instructions
                input_data["notes"] = f"Create a different perspective or approach than previous stories. Focus on variation {i+1} of {count}."
            
            result = await self.execute(input_data)
            
            if result.success and result.data:
                stories.append(result.data)
            else:
                logger.warning(
                    "story_generation_failed",
                    index=i,
                    error=result.error
                )
        
        return stories
    
    async def refine_story(
        self,
        story: UserStoryOutput,
        feedback: str
    ) -> UserStoryOutput:
        """
        Refine an existing story based on feedback.
        
        Args:
            story: Existing story
            feedback: Refinement feedback
            
        Returns:
            Refined story
        """
        refinement_prompt = f"""Please refine this user story based on the feedback:

Original Story:
Title: {story.title}
As a {story.user_type}, I want {story.user_story} so that {story.benefit}

Acceptance Criteria:
{json.dumps(story.acceptance_criteria, indent=2)}

Feedback: {feedback}

Create an improved version addressing the feedback while maintaining the story structure."""
        
        messages = self.create_messages(self.system_prompt, refinement_prompt)
        response = await self.generate(messages)
        
        try:
            refined_story = self.output_parser.parse(response)
            
            logger.info(
                "story_refined",
                original_title=story.title,
                refined_title=refined_story.title
            )
            
            return refined_story
            
        except Exception as e:
            logger.error("story_refinement_failed", error=str(e))
            raise AgentError(f"Failed to refine story: {str(e)}")
    
    async def split_story(
        self,
        story: UserStoryOutput,
        max_points: int = 8
    ) -> List[UserStoryOutput]:
        """
        Split a large story into smaller ones.
        
        Args:
            story: Story to split
            max_points: Maximum points per story
            
        Returns:
            List of smaller stories
        """
        if story.story_points and story.story_points <= max_points:
            return [story]
        
        split_prompt = f"""This user story is too large and needs to be split into smaller, independent stories:

Title: {story.title}
As a {story.user_type}, I want {story.user_story} so that {story.benefit}
Story Points: {story.story_points}

Please split this into 2-4 smaller stories, each with no more than {max_points} story points.
Each story should be independently valuable and testable."""
        
        messages = self.create_messages(self.system_prompt, split_prompt)
        response = await self.generate(messages)
        
        # Parse multiple stories from response
        # This is a simplified version - in production, you'd use a more sophisticated parser
        stories = []
        try:
            # Attempt to parse as JSON array
            stories_data = json.loads(response)
            for story_data in stories_data:
                story = UserStoryOutput(**story_data)
                stories.append(story)
        except:
            # Fall back to parsing single story
            try:
                story = self.output_parser.parse(response)
                stories.append(story)
            except Exception as e:
                logger.error("story_splitting_failed", error=str(e))
                raise AgentError(f"Failed to split story: {str(e)}")
        
        logger.info(
            "story_split",
            original_title=story.title,
            split_count=len(stories)
        )
        
        return stories