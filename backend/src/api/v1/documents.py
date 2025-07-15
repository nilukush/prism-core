"""
Documents API endpoints.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, Field

from backend.src.core.database import get_db
from backend.src.models.user import User
from backend.src.models.document import Document, DocumentType, DocumentStatus
from backend.src.models.project import Project
from backend.src.api.deps import get_current_user
from backend.src.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


class DocumentCreateRequest(BaseModel):
    """Request model for creating a document."""
    title: str = Field(..., description="Document title")
    type: DocumentType = Field(default=DocumentType.PRD, description="Document type")
    content: Dict[str, Any] = Field(..., description="Document content")
    summary: Optional[str] = Field(None, description="Document summary")
    project_id: int = Field(..., description="Project ID")
    status: DocumentStatus = Field(default=DocumentStatus.DRAFT, description="Document status")
    ai_generated: bool = Field(default=False, description="Whether AI generated")
    ai_model: Optional[str] = Field(None, description="AI model used")
    generation_context: Optional[Dict[str, Any]] = Field(None, description="Generation context")


class DocumentUpdateRequest(BaseModel):
    """Request model for updating a document."""
    title: Optional[str] = Field(None, description="Document title")
    content: Optional[Dict[str, Any]] = Field(None, description="Document content")
    summary: Optional[str] = Field(None, description="Document summary")
    status: Optional[DocumentStatus] = Field(None, description="Document status")


@router.get("/")
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    document_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    List all documents for the current user.
    """
    try:
        # Build base query
        query = select(Document).where(Document.is_deleted == False)
        
        # Filter by document type if specified
        if document_type:
            # Convert string to DocumentType enum
            try:
                doc_type = DocumentType(document_type.upper())
                query = query.where(Document.type == doc_type)
            except ValueError:
                logger.warning(f"Invalid document type filter: {document_type}")
        
        # TODO: Add proper access control based on user's project/organization membership
        # For now, show documents where user is creator or documents that are published
        from sqlalchemy import or_
        query = query.where(
            or_(
                Document.creator_id == current_user.id,
                Document.status == DocumentStatus.PUBLISHED
            )
        )
        
        # Order by most recent first
        query = query.order_by(Document.created_at.desc())
        
        # Get total count before pagination
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Execute query
        result = await db.execute(query)
        documents = result.scalars().all()
        
        # Format response
        documents_data = []
        for doc in documents:
            # Get project info for each document
            project = await db.get(Project, doc.project_id)
            project_info = {
                "id": project.id,
                "name": project.name,
                "key": project.key
            } if project else None
            
            # Get creator info for each document
            creator = await db.get(User, doc.creator_id)
            creator_info = {
                "id": creator.id,
                "email": creator.email,
                "full_name": creator.full_name
            } if creator else None
            
            documents_data.append({
                "id": doc.id,
                "title": doc.title,
                "slug": doc.slug,
                "type": doc.type.value,
                "summary": doc.summary,
                "status": doc.status.value,
                "project_id": doc.project_id,
                "project": project_info,
                "creator_id": doc.creator_id,
                "creator": creator_info,
                "ai_generated": doc.ai_generated,
                "ai_model": doc.ai_model,
                "created_at": doc.created_at.isoformat(),
                "updated_at": doc.updated_at.isoformat(),
                "version": doc.version
            })
        
        logger.info(
            "documents_listed",
            user_id=current_user.id,
            document_type=document_type,
            count=len(documents_data),
            total=total
        )
        
        return {
            "documents": documents_data,
            "total": total,
            "skip": skip,
            "limit": limit,
            "document_type": document_type,
        }
        
    except Exception as e:
        logger.error("document_listing_failed", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.get("/{document_id}")
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get a specific document by ID.
    """
    try:
        # Get document with project info
        document = await db.get(Document, document_id)
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Check if user has access to the document
        # TODO: Implement proper project-based access control
        # For now, allow if user is the creator or if document is published
        if document.creator_id != current_user.id and document.status != DocumentStatus.PUBLISHED:
            # Check if user has access to the project
            project = await db.get(Project, document.project_id)
            if not project:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Associated project not found"
                )
            # TODO: Check if user is member of project's workspace
        
        logger.info(
            "document_retrieved",
            document_id=document.id,
            user_id=current_user.id
        )
        
        return JSONResponse(
            content={
                "id": document.id,
                "title": document.title,
                "slug": document.slug,
                "type": document.type.value,
                "content": document.content,
                "summary": document.summary,
                "status": document.status.value,
                "creator_id": document.creator_id,
                "project_id": document.project_id,
                "ai_generated": document.ai_generated,
                "ai_model": document.ai_model,
                "generation_context": document.generation_context,
                "created_at": document.created_at.isoformat(),
                "updated_at": document.updated_at.isoformat(),
                "version": document.version
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("document_retrieval_failed", error=str(e), document_id=document_id, user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve document: {str(e)}"
        )


@router.post("/")
async def create_document(
    request: Request,
    document_data: DocumentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create a new document (PRD, tech spec, etc.).
    """
    try:
        # Verify project exists and user has access
        project = await db.get(Project, document_data.project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Check if user has access to the project
        # TODO: Implement proper project access control
        
        # Generate slug from title
        import re
        slug = re.sub(r'[^a-z0-9-]', '-', document_data.title.lower())
        slug = re.sub(r'-+', '-', slug).strip('-')
        
        # Make slug unique by appending timestamp if needed
        existing = await db.execute(
            select(Document).where(Document.slug == slug)
        )
        if existing.scalar_one_or_none():
            slug = f"{slug}-{int(datetime.utcnow().timestamp())}"
        
        # Create document
        document = Document(
            title=document_data.title,
            slug=slug,
            type=document_data.type,
            content=document_data.content,
            summary=document_data.summary,
            status=document_data.status,
            creator_id=current_user.id,
            project_id=document_data.project_id,
            ai_generated=document_data.ai_generated,
            ai_model=document_data.ai_model,
            generation_context=document_data.generation_context,
            created_by_id=current_user.id,
            updated_by_id=current_user.id
        )
        
        db.add(document)
        await db.commit()
        await db.refresh(document)
        
        logger.info(
            "document_created",
            document_id=document.id,
            title=document.title,
            type=document.type.value,
            status=document.status.value,
            user_id=current_user.id
        )
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "success": True,
                "document": {
                    "id": document.id,
                    "title": document.title,
                    "slug": document.slug,
                    "type": document.type.value,
                    "status": document.status.value,
                    "created_at": document.created_at.isoformat(),
                    "updated_at": document.updated_at.isoformat()
                },
                "message": "Document created successfully"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("document_creation_failed", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create document: {str(e)}"
        )


@router.put("/{document_id}")
async def update_document(
    request: Request,
    document_id: int,
    update_data: DocumentUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update an existing document.
    """
    try:
        # Get document
        document = await db.get(Document, document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Check if user has permission to update
        # TODO: Implement proper permission checking
        if document.creator_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this document"
            )
        
        # Update fields
        if update_data.title is not None:
            document.title = update_data.title
        if update_data.content is not None:
            document.content = update_data.content
        if update_data.summary is not None:
            document.summary = update_data.summary
        if update_data.status is not None:
            document.status = update_data.status
        
        document.updated_by_id = current_user.id
        
        await db.commit()
        await db.refresh(document)
        
        logger.info(
            "document_updated",
            document_id=document.id,
            user_id=current_user.id
        )
        
        return JSONResponse(
            content={
                "success": True,
                "document": {
                    "id": document.id,
                    "title": document.title,
                    "slug": document.slug,
                    "type": document.type.value,
                    "status": document.status.value,
                    "updated_at": document.updated_at.isoformat()
                },
                "message": "Document updated successfully"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("document_update_failed", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update document: {str(e)}"
        )


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Upload a new document.
    """
    # TODO: Implement document upload logic
    return {
        "id": 1,
        "name": file.filename,
        "type": file.content_type,
        "message": "Document uploaded successfully",
    }


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Delete a document.
    """
    # TODO: Implement document deletion logic
    return {
        "message": f"Document {document_id} deleted successfully",
    }