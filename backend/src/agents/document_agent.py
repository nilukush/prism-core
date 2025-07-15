"""
Document Agent for generating various types of documentation.
Creates PRDs, technical specs, and other product documentation.
"""

from typing import Dict, Any, List, Optional
from enum import Enum
import json

from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate

from backend.src.agents.base import BaseAgent, AgentError
from backend.src.core.logging import get_logger

logger = get_logger(__name__)


class DocumentSection(BaseModel):
    """A section within a document."""
    
    title: str = Field(description="Section title")
    content: str = Field(description="Section content in markdown format")
    subsections: List["DocumentSection"] = Field(
        description="Nested subsections",
        default_factory=list
    )


class DocumentOutput(BaseModel):
    """Output format for generated documents."""
    
    title: str = Field(description="Document title")
    type: str = Field(description="Document type (prd, tech_spec, etc.)")
    summary: str = Field(description="Executive summary")
    sections: List[DocumentSection] = Field(description="Document sections")
    metadata: Dict[str, Any] = Field(
        description="Document metadata",
        default_factory=dict
    )


# Allow recursive model
DocumentSection.model_rebuild()


class DocumentType(str, Enum):
    """Supported document types."""
    PRD = "prd"
    TECH_SPEC = "tech_spec"
    DESIGN_DOC = "design_doc"
    USER_GUIDE = "user_guide"
    API_DOC = "api_doc"
    RETROSPECTIVE = "retrospective"


class DocumentAgent(BaseAgent[DocumentOutput]):
    """Agent for generating documentation."""
    
    def __init__(self, **kwargs):
        """Initialize document agent."""
        super().__init__(
            name="document_agent",
            description="Generates comprehensive product documentation",
            **kwargs
        )
        
        # Create output parser
        self.output_parser = PydanticOutputParser(pydantic_object=DocumentOutput)
        
        # System prompts for different document types
        self.system_prompts = {
            DocumentType.PRD: """You are an expert product manager creating comprehensive Product Requirements Documents (PRDs).
            Your PRDs are clear, actionable, and align engineering efforts with business goals. Include:
            - Clear problem statement and solution
            - User personas and use cases
            - Functional and non-functional requirements
            - Success metrics and KPIs
            - Timeline and milestones
            - Risks and mitigations""",
            
            DocumentType.TECH_SPEC: """You are a senior software architect creating detailed technical specifications.
            Your specs provide clear implementation guidance while allowing flexibility. Include:
            - Architecture overview and diagrams
            - Technology stack and dependencies
            - API design and data models
            - Security and performance considerations
            - Testing strategy
            - Deployment and monitoring plan""",
            
            DocumentType.DESIGN_DOC: """You are a system designer creating comprehensive design documents.
            Focus on clarity, completeness, and addressing all stakeholder concerns. Include:
            - Problem context and constraints
            - Proposed solution and alternatives
            - System architecture and components
            - Data flow and interactions
            - Trade-offs and decisions
            - Implementation plan""",
            
            DocumentType.USER_GUIDE: """You are a technical writer creating user-friendly documentation.
            Write clear, concise guides that help users accomplish their goals. Include:
            - Getting started guide
            - Feature explanations with examples
            - Common use cases and workflows
            - Troubleshooting section
            - FAQ section
            - Best practices""",
        }
        
        # Document templates
        self.templates = {
            DocumentType.PRD: self._get_prd_template(),
            DocumentType.TECH_SPEC: self._get_tech_spec_template(),
            DocumentType.DESIGN_DOC: self._get_design_doc_template(),
            DocumentType.USER_GUIDE: self._get_user_guide_template(),
        }
    
    def _get_prd_template(self) -> List[str]:
        """Get PRD section template."""
        return [
            "Executive Summary",
            "Problem Statement",
            "Goals and Objectives",
            "User Personas",
            "User Stories and Use Cases",
            "Functional Requirements",
            "Non-Functional Requirements",
            "Success Metrics",
            "Timeline and Milestones",
            "Risks and Mitigations",
            "Open Questions",
        ]
    
    def _get_tech_spec_template(self) -> List[str]:
        """Get technical specification template."""
        return [
            "Overview",
            "Architecture",
            "Technology Stack",
            "API Design",
            "Data Models",
            "Security Considerations",
            "Performance Requirements",
            "Testing Strategy",
            "Deployment Plan",
            "Monitoring and Observability",
        ]
    
    def _get_design_doc_template(self) -> List[str]:
        """Get design document template."""
        return [
            "Context and Scope",
            "Goals and Non-Goals",
            "Proposed Solution",
            "Alternative Solutions",
            "System Design",
            "Implementation Details",
            "Testing Plan",
            "Rollout Strategy",
            "Future Considerations",
        ]
    
    def _get_user_guide_template(self) -> List[str]:
        """Get user guide template."""
        return [
            "Introduction",
            "Getting Started",
            "Core Features",
            "Advanced Features",
            "Use Cases and Examples",
            "Troubleshooting",
            "FAQ",
            "Best Practices",
            "Support and Resources",
        ]
    
    def _validate_input(self, input_data: Dict[str, Any]) -> None:
        """Validate input data."""
        if not input_data.get("title"):
            raise AgentError("Document title is required")
        
        if not input_data.get("type"):
            raise AgentError("Document type is required")
        
        doc_type = input_data["type"]
        if doc_type not in [t.value for t in DocumentType]:
            raise AgentError(f"Unsupported document type: {doc_type}")
        
        if not input_data.get("context"):
            raise AgentError("Document context is required")
    
    async def _process(self, input_data: Dict[str, Any]) -> DocumentOutput:
        """Process input and generate document."""
        # Extract inputs
        title = input_data["title"]
        doc_type = input_data["type"]
        context = input_data["context"]
        requirements = input_data.get("requirements", {})
        audience = input_data.get("audience", "General audience")
        
        # Get appropriate system prompt and template
        system_prompt = self.system_prompts.get(
            DocumentType(doc_type),
            self.system_prompts[DocumentType.PRD]
        )
        
        template_sections = self.templates.get(
            DocumentType(doc_type),
            self.templates[DocumentType.PRD]
        )
        
        # Create user prompt
        user_prompt = f"""Create a comprehensive {doc_type} document with the following details:

Title: {title}
Target Audience: {audience}

Context:
{context}

Requirements:
{json.dumps(requirements, indent=2)}

Please structure the document with these sections:
{json.dumps(template_sections, indent=2)}

Provide detailed content for each section. Use markdown formatting for better readability.

{self.output_parser.get_format_instructions()}"""
        
        # Create messages
        messages = self.create_messages(system_prompt, user_prompt)
        
        # Generate response
        response = await self.generate(messages)
        
        # Parse response
        try:
            document = self.output_parser.parse(response)
            
            # Add metadata
            document.metadata.update({
                "generator": "document_agent",
                "template_used": template_sections,
                "audience": audience,
            })
            
            logger.info(
                "document_generated",
                title=document.title,
                type=document.type,
                sections=len(document.sections)
            )
            
            return document
            
        except Exception as e:
            logger.error("document_parsing_failed", error=str(e), response=response)
            raise AgentError(f"Failed to parse document: {str(e)}")
    
    async def generate_section(
        self,
        doc_type: str,
        section_title: str,
        context: Dict[str, Any]
    ) -> DocumentSection:
        """
        Generate a specific document section.
        
        Args:
            doc_type: Document type
            section_title: Section to generate
            context: Context for generation
            
        Returns:
            Generated section
        """
        system_prompt = self.system_prompts.get(
            DocumentType(doc_type),
            self.system_prompts[DocumentType.PRD]
        )
        
        user_prompt = f"""Generate detailed content for the "{section_title}" section of a {doc_type}.

Context:
{json.dumps(context, indent=2)}

Provide comprehensive content that:
1. Is well-structured and easy to read
2. Includes specific details and examples
3. Addresses all relevant aspects
4. Uses appropriate markdown formatting

Return the section in this format:
{{
    "title": "{section_title}",
    "content": "detailed markdown content here",
    "subsections": []
}}"""
        
        messages = self.create_messages(system_prompt, user_prompt)
        response = await self.generate(messages)
        
        try:
            section_data = json.loads(response)
            section = DocumentSection(**section_data)
            
            logger.info(
                "section_generated",
                doc_type=doc_type,
                section=section_title
            )
            
            return section
            
        except Exception as e:
            logger.error("section_generation_failed", error=str(e))
            raise AgentError(f"Failed to generate section: {str(e)}")
    
    async def update_document(
        self,
        document: DocumentOutput,
        updates: Dict[str, Any],
        regenerate_sections: List[str] = None
    ) -> DocumentOutput:
        """
        Update an existing document.
        
        Args:
            document: Existing document
            updates: Updates to apply
            regenerate_sections: Sections to regenerate
            
        Returns:
            Updated document
        """
        # Apply direct updates
        if "title" in updates:
            document.title = updates["title"]
        if "summary" in updates:
            document.summary = updates["summary"]
        
        # Regenerate specified sections
        if regenerate_sections:
            context = {
                "document_title": document.title,
                "document_type": document.type,
                "existing_summary": document.summary,
                "updates": updates,
            }
            
            for section_title in regenerate_sections:
                # Find and replace section
                for i, section in enumerate(document.sections):
                    if section.title == section_title:
                        new_section = await self.generate_section(
                            document.type,
                            section_title,
                            context
                        )
                        document.sections[i] = new_section
                        break
        
        logger.info(
            "document_updated",
            title=document.title,
            updates=list(updates.keys()),
            regenerated=regenerate_sections
        )
        
        return document
    
    def to_markdown(self, document: DocumentOutput) -> str:
        """
        Convert document to markdown format.
        
        Args:
            document: Document to convert
            
        Returns:
            Markdown string
        """
        def render_section(section: DocumentSection, level: int = 2) -> str:
            """Recursively render section."""
            markdown = f"{'#' * level} {section.title}\n\n"
            markdown += f"{section.content}\n\n"
            
            for subsection in section.subsections:
                markdown += render_section(subsection, level + 1)
            
            return markdown
        
        # Start with title and metadata
        markdown = f"# {document.title}\n\n"
        markdown += f"**Type:** {document.type}\n"
        markdown += f"**Generated:** {document.metadata.get('generated_at', 'N/A')}\n\n"
        
        # Add summary
        markdown += "## Executive Summary\n\n"
        markdown += f"{document.summary}\n\n"
        
        # Add sections
        for section in document.sections:
            markdown += render_section(section)
        
        return markdown