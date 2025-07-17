"""
Vector store service for RAG and semantic search.
Uses Qdrant as the vector database.
"""

from typing import List, Dict, Any, Optional
import hashlib
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter, FieldCondition, 
    Range, MatchValue, SearchRequest, ScoredPoint
)
from qdrant_client.http import models as rest

from backend.src.core.config import settings
from backend.src.core.logging import get_logger

logger = get_logger(__name__)


class VectorStore:
    """Vector store service for semantic search and RAG."""
    
    def __init__(self):
        """Initialize vector store service."""
        self.client: Optional[QdrantClient] = None
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        self.vector_size = 1536  # OpenAI embedding size
        self.enabled = True  # Track if vector store is available
    
    async def initialize(self) -> None:
        """Initialize connection to Qdrant."""
        try:
            if settings.QDRANT_USE_CLOUD and settings.QDRANT_API_KEY:
                # Use Qdrant Cloud
                self.client = QdrantClient(
                    url=settings.QDRANT_URL,
                    api_key=settings.QDRANT_API_KEY,
                )
            else:
                # Use local Qdrant
                self.client = QdrantClient(
                    url=settings.QDRANT_URL,
                    timeout=30,
                )
            
            # Create collection if it doesn't exist
            await self._ensure_collection()
            
            logger.info("vector_store_initialized", url=settings.QDRANT_URL)
        except Exception as e:
            logger.warning("vector_store_initialization_skipped", error=str(e))
            self.enabled = False
            # Don't raise - allow app to run without vector store
    
    async def close(self) -> None:
        """Close vector store connection."""
        if self.client:
            self.client.close()
            logger.info("vector_store_closed")
    
    async def health_check(self) -> bool:
        """Check if vector store is healthy."""
        try:
            if not self.client:
                return False
            
            # Try to get collection info
            self.client.get_collection(self.collection_name)
            return True
        except Exception as e:
            logger.error("vector_store_health_check_failed", error=str(e))
            return False
    
    async def _ensure_collection(self) -> None:
        """Ensure collection exists with proper configuration."""
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            
            if not exists:
                # Create collection
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE,
                    ),
                )
                
                # Create indexes for metadata fields
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="document_type",
                    field_schema="keyword",
                )
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="project_id",
                    field_schema="integer",
                )
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="organization_id",
                    field_schema="integer",
                )
                
                logger.info("vector_collection_created", name=self.collection_name)
        except Exception as e:
            logger.warning("collection_creation_skipped", error=str(e), reason="Vector database not available in free tier")
            # Don't raise - allow app to run without vector store
            self.enabled = False
    
    def generate_id(self, content: str, metadata: Dict[str, Any]) -> str:
        """Generate deterministic ID for content."""
        # Create a unique string from content and key metadata
        unique_string = f"{content}:{metadata.get('document_type', '')}:{metadata.get('document_id', '')}"
        return hashlib.sha256(unique_string.encode()).hexdigest()
    
    async def upsert(
        self,
        content: str,
        embedding: List[float],
        metadata: Dict[str, Any],
        document_id: Optional[str] = None,
    ) -> str:
        """
        Upsert document embedding into vector store.
        
        Args:
            content: Text content
            embedding: Vector embedding
            metadata: Document metadata
            document_id: Optional document ID
            
        Returns:
            Document ID
        """
        if not self.enabled or not self.client:
            logger.debug("vector_store_disabled_skipping_upsert")
            return str(uuid.uuid4())  # Return dummy ID when disabled
            
        try:
            # Generate ID if not provided
            if not document_id:
                document_id = self.generate_id(content, metadata)
            
            # Create point
            point = PointStruct(
                id=document_id,
                vector=embedding,
                payload={
                    "content": content,
                    "content_hash": hashlib.md5(content.encode()).hexdigest(),
                    **metadata,
                }
            )
            
            # Upsert to collection
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point],
            )
            
            logger.debug("vector_upserted", document_id=document_id)
            return document_id
            
        except Exception as e:
            logger.error("vector_upsert_failed", error=str(e))
            raise
    
    async def search(
        self,
        query_embedding: List[float],
        limit: int = 10,
        score_threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        
        Args:
            query_embedding: Query vector
            limit: Maximum results
            score_threshold: Minimum similarity score
            filters: Metadata filters
            
        Returns:
            List of search results
        """
        try:
            # Build filter conditions
            filter_conditions = []
            if filters:
                for key, value in filters.items():
                    if isinstance(value, list):
                        # Handle list values (OR condition)
                        filter_conditions.append(
                            FieldCondition(
                                key=key,
                                match=MatchValue(value=value),
                            )
                        )
                    elif isinstance(value, dict) and "min" in value:
                        # Handle range queries
                        filter_conditions.append(
                            FieldCondition(
                                key=key,
                                range=Range(
                                    gte=value.get("min"),
                                    lte=value.get("max"),
                                ),
                            )
                        )
                    else:
                        # Handle exact match
                        filter_conditions.append(
                            FieldCondition(
                                key=key,
                                match=MatchValue(value=value),
                            )
                        )
            
            # Create search request
            search_filter = Filter(must=filter_conditions) if filter_conditions else None
            
            # Perform search
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=search_filter,
                limit=limit,
                score_threshold=score_threshold,
            )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "id": result.id,
                    "score": result.score,
                    "content": result.payload.get("content", ""),
                    "metadata": {
                        k: v for k, v in result.payload.items() 
                        if k not in ["content", "content_hash"]
                    },
                })
            
            logger.debug(
                "vector_search_completed",
                query_results=len(formatted_results),
                score_threshold=score_threshold,
            )
            
            return formatted_results
            
        except Exception as e:
            logger.error("vector_search_failed", error=str(e))
            raise
    
    async def delete(self, document_ids: List[str]) -> None:
        """
        Delete documents from vector store.
        
        Args:
            document_ids: List of document IDs to delete
        """
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=rest.PointIdsList(points=document_ids),
            )
            
            logger.debug("vectors_deleted", count=len(document_ids))
            
        except Exception as e:
            logger.error("vector_deletion_failed", error=str(e))
            raise
    
    async def delete_by_metadata(self, filters: Dict[str, Any]) -> None:
        """
        Delete documents by metadata filters.
        
        Args:
            filters: Metadata filters
        """
        try:
            # Build filter conditions
            filter_conditions = []
            for key, value in filters.items():
                filter_conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value),
                    )
                )
            
            # Delete by filter
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=rest.FilterSelector(
                    filter=Filter(must=filter_conditions)
                ),
            )
            
            logger.debug("vectors_deleted_by_metadata", filters=filters)
            
        except Exception as e:
            logger.error("vector_deletion_by_metadata_failed", error=str(e))
            raise
    
    async def update_metadata(
        self,
        document_id: str,
        metadata: Dict[str, Any],
    ) -> None:
        """
        Update document metadata.
        
        Args:
            document_id: Document ID
            metadata: New metadata
        """
        try:
            self.client.update_payload(
                collection_name=self.collection_name,
                payload=metadata,
                points=[document_id],
            )
            
            logger.debug("vector_metadata_updated", document_id=document_id)
            
        except Exception as e:
            logger.error("vector_metadata_update_failed", error=str(e))
            raise
    
    async def get_collection_info(self) -> Dict[str, Any]:
        """Get collection information."""
        try:
            info = self.client.get_collection(self.collection_name)
            
            return {
                "name": info.config.params.vectors.size,
                "vector_size": info.config.params.vectors.size,
                "distance": info.config.params.vectors.distance,
                "points_count": info.points_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "status": info.status,
            }
            
        except Exception as e:
            logger.error("get_collection_info_failed", error=str(e))
            raise


# Global vector store instance
vector_store = VectorStore()