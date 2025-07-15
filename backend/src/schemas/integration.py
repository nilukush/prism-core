"""
Integration-related Pydantic schemas.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, HttpUrl

from backend.src.schemas.common import TimestampMixin, PaginatedResponse


class IntegrationType(str, Enum):
    """Integration type enum."""
    JIRA = "jira"
    CONFLUENCE = "confluence"
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"
    SLACK = "slack"
    TEAMS = "teams"
    TRELLO = "trello"
    ASANA = "asana"
    LINEAR = "linear"
    NOTION = "notion"
    GOOGLE_DRIVE = "google_drive"
    CUSTOM = "custom"


class IntegrationStatus(str, Enum):
    """Integration status."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    PENDING = "pending"
    EXPIRED = "expired"


class SyncStatus(str, Enum):
    """Sync status."""
    IDLE = "idle"
    SYNCING = "syncing"
    COMPLETED = "completed"
    FAILED = "failed"


class IntegrationBase(BaseModel):
    """Base integration schema."""
    name: str = Field(min_length=1, max_length=255, description="Integration name")
    type: IntegrationType
    description: Optional[str] = Field(default=None, max_length=1000)
    
    model_config = ConfigDict(from_attributes=True)


class IntegrationResponse(IntegrationBase, TimestampMixin):
    """Integration response schema."""
    id: UUID
    workspace_id: Optional[UUID] = None
    organization_id: UUID
    status: IntegrationStatus = IntegrationStatus.DISCONNECTED
    is_active: bool = True
    config: Dict[str, Any] = Field(default_factory=dict, description="Public config")
    capabilities: List[str] = Field(default_factory=list)
    last_sync_at: Optional[datetime] = None
    next_sync_at: Optional[datetime] = None
    sync_status: SyncStatus = SyncStatus.IDLE
    error_message: Optional[str] = None
    connected_by_id: Optional[UUID] = None
    connected_by_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class IntegrationListResponse(PaginatedResponse[IntegrationResponse]):
    """Paginated integration list response."""
    pass


class IntegrationConnectRequest(BaseModel):
    """Request to connect an integration."""
    workspace_id: Optional[UUID] = Field(default=None, description="Workspace to connect to")
    config: Dict[str, Any] = Field(description="Integration configuration")
    
    # OAuth flow
    oauth_code: Optional[str] = Field(default=None, description="OAuth authorization code")
    oauth_state: Optional[str] = Field(default=None, description="OAuth state parameter")
    
    # API key/token flow
    api_key: Optional[str] = Field(default=None, description="API key or token")
    api_secret: Optional[str] = Field(default=None, description="API secret")
    
    # Webhook configuration
    webhook_url: Optional[HttpUrl] = Field(default=None, description="Webhook URL")
    webhook_secret: Optional[str] = Field(default=None, description="Webhook secret")


class IntegrationConnectResponse(BaseModel):
    """Response from connecting an integration."""
    integration_id: UUID
    status: IntegrationStatus
    message: str
    oauth_url: Optional[str] = Field(default=None, description="OAuth authorization URL")
    requires_oauth: bool = False
    next_steps: Optional[List[str]] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)


class IntegrationDisconnectResponse(BaseModel):
    """Response from disconnecting an integration."""
    message: str
    data_retained: bool = Field(description="Whether data was retained")
    
    model_config = ConfigDict(from_attributes=True)


class IntegrationSyncRequest(BaseModel):
    """Request to sync an integration."""
    full_sync: bool = Field(default=False, description="Perform full sync")
    entities: Optional[List[str]] = Field(default=None, description="Specific entities to sync")
    since: Optional[datetime] = Field(default=None, description="Sync changes since")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict)


class IntegrationSyncResponse(BaseModel):
    """Response from integration sync."""
    sync_id: UUID
    status: SyncStatus
    started_at: datetime
    estimated_duration_seconds: Optional[int] = None
    message: str
    
    model_config = ConfigDict(from_attributes=True)


class IntegrationSyncResult(BaseModel, TimestampMixin):
    """Integration sync result."""
    id: UUID
    integration_id: UUID
    status: SyncStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    entities_synced: Dict[str, int] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)


class IntegrationWebhookPayload(BaseModel):
    """Integration webhook payload."""
    integration_id: UUID
    event_type: str
    event_id: Optional[str] = None
    timestamp: datetime
    data: Dict[str, Any]
    signature: Optional[str] = None


class IntegrationMapping(BaseModel):
    """Integration field mapping."""
    id: UUID
    integration_id: UUID
    entity_type: str = Field(description="Entity type (story, project, etc)")
    local_field: str
    remote_field: str
    transform: Optional[str] = Field(default=None, description="Transform function")
    is_required: bool = False
    
    model_config = ConfigDict(from_attributes=True)


class IntegrationMappingCreate(BaseModel):
    """Create integration mapping."""
    entity_type: str
    local_field: str
    remote_field: str
    transform: Optional[str] = None
    is_required: bool = False


class IntegrationLog(BaseModel):
    """Integration activity log."""
    id: UUID
    integration_id: UUID
    timestamp: datetime
    level: str = Field(pattern="^(debug|info|warning|error)$")
    action: str
    message: str
    details: Optional[Dict[str, Any]] = None
    user_id: Optional[UUID] = None
    
    model_config = ConfigDict(from_attributes=True)


class IntegrationStats(BaseModel):
    """Integration statistics."""
    integration_id: UUID
    total_syncs: int
    successful_syncs: int
    failed_syncs: int
    last_sync_duration_seconds: Optional[int] = None
    average_sync_duration_seconds: Optional[float] = None
    entities_synced_total: Dict[str, int]
    data_volume_mb: float
    
    model_config = ConfigDict(from_attributes=True)


class IntegrationTestRequest(BaseModel):
    """Request to test integration connection."""
    config: Optional[Dict[str, Any]] = Field(default_factory=dict)


class IntegrationTestResponse(BaseModel):
    """Response from integration test."""
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None
    capabilities_available: List[str] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)