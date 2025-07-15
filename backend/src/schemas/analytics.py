"""
Analytics-related Pydantic schemas.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict

from backend.src.schemas.common import TimestampMixin


class TimeGranularity(str, Enum):
    """Time granularity for analytics."""
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class MetricType(str, Enum):
    """Metric type."""
    COUNT = "count"
    SUM = "sum"
    AVERAGE = "average"
    MEDIAN = "median"
    PERCENTILE = "percentile"
    RATE = "rate"


class ChartType(str, Enum):
    """Chart type for visualization."""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    DONUT = "donut"
    AREA = "area"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    FUNNEL = "funnel"
    GAUGE = "gauge"
    TABLE = "table"


class DateRange(BaseModel):
    """Date range for analytics."""
    start_date: date
    end_date: date
    
    model_config = ConfigDict(from_attributes=True)


class TimeSeriesDataPoint(BaseModel):
    """Time series data point."""
    timestamp: datetime
    value: float
    label: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class MetricValue(BaseModel):
    """Metric value with metadata."""
    name: str
    value: float
    unit: Optional[str] = None
    change_percentage: Optional[float] = None
    change_direction: Optional[str] = Field(default=None, pattern="^(up|down|flat)$")
    
    model_config = ConfigDict(from_attributes=True)


class AnalyticsOverviewResponse(BaseModel):
    """Analytics overview response."""
    period: DateRange
    workspace_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    
    # Key metrics
    total_stories: MetricValue
    completed_stories: MetricValue
    active_users: MetricValue
    velocity: MetricValue
    cycle_time: MetricValue
    
    # Progress metrics
    completion_rate: float
    on_track_percentage: float
    
    # Team metrics
    team_productivity: Dict[str, float]
    workload_distribution: Dict[str, int]
    
    # Recent activity
    recent_activities: List[Dict[str, Any]]
    
    model_config = ConfigDict(from_attributes=True)


class UsageAnalyticsRequest(BaseModel):
    """Request for usage analytics."""
    date_range: DateRange
    granularity: TimeGranularity = TimeGranularity.DAY
    workspace_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    group_by: Optional[List[str]] = Field(default_factory=list)


class UsageAnalyticsResponse(BaseModel):
    """Usage analytics response."""
    period: DateRange
    granularity: TimeGranularity
    
    # API usage
    api_calls: List[TimeSeriesDataPoint]
    api_calls_by_endpoint: Dict[str, int]
    
    # User activity
    active_users: List[TimeSeriesDataPoint]
    user_sessions: List[TimeSeriesDataPoint]
    actions_per_user: Dict[str, int]
    
    # AI usage
    ai_requests: List[TimeSeriesDataPoint]
    ai_tokens_used: List[TimeSeriesDataPoint]
    ai_cost: List[TimeSeriesDataPoint]
    ai_by_provider: Dict[str, int]
    
    # Storage usage
    storage_used_mb: List[TimeSeriesDataPoint]
    documents_created: List[TimeSeriesDataPoint]
    
    model_config = ConfigDict(from_attributes=True)


class ProductivityAnalytics(BaseModel):
    """Productivity analytics."""
    period: DateRange
    
    # Velocity metrics
    velocity_trend: List[TimeSeriesDataPoint]
    average_velocity: float
    velocity_by_team: Dict[str, float]
    
    # Throughput metrics
    stories_completed: List[TimeSeriesDataPoint]
    story_points_completed: List[TimeSeriesDataPoint]
    
    # Efficiency metrics
    cycle_time_trend: List[TimeSeriesDataPoint]
    lead_time_trend: List[TimeSeriesDataPoint]
    average_cycle_time_days: float
    average_lead_time_days: float
    
    # Quality metrics
    defect_rate: List[TimeSeriesDataPoint]
    rework_percentage: float
    
    model_config = ConfigDict(from_attributes=True)


class TrendsAnalyticsRequest(BaseModel):
    """Request for trends analytics."""
    metrics: List[str] = Field(description="Metrics to analyze")
    date_range: DateRange
    granularity: TimeGranularity = TimeGranularity.DAY
    workspace_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    compare_to_previous: bool = Field(default=False)


class TrendsAnalyticsResponse(BaseModel):
    """Trends analytics response."""
    period: DateRange
    granularity: TimeGranularity
    
    # Trend data by metric
    trends: Dict[str, List[TimeSeriesDataPoint]]
    
    # Statistical analysis
    statistics: Dict[str, Dict[str, float]]  # min, max, avg, median, std_dev
    
    # Predictions (if available)
    predictions: Optional[Dict[str, List[TimeSeriesDataPoint]]] = None
    
    # Comparisons
    period_over_period: Optional[Dict[str, float]] = None
    
    model_config = ConfigDict(from_attributes=True)


class ExportAnalyticsRequest(BaseModel):
    """Request for analytics export."""
    report_type: str = Field(description="Type of report to export")
    date_range: DateRange
    format: str = Field(default="csv", pattern="^(csv|excel|pdf|json)$")
    workspace_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    include_charts: bool = Field(default=False)
    email_to: Optional[str] = Field(default=None, description="Email address to send report")


class ExportAnalyticsResponse(BaseModel):
    """Analytics export response."""
    export_id: UUID
    status: str = Field(pattern="^(pending|processing|completed|failed)$")
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    message: str
    
    model_config = ConfigDict(from_attributes=True)


class BurndownChart(BaseModel):
    """Burndown chart data."""
    sprint_id: UUID
    sprint_name: str
    start_date: date
    end_date: date
    total_points: int
    
    # Daily data points
    ideal_burndown: List[TimeSeriesDataPoint]
    actual_burndown: List[TimeSeriesDataPoint]
    
    # Current status
    remaining_points: int
    remaining_days: int
    is_on_track: bool
    projected_completion: Optional[date] = None
    
    model_config = ConfigDict(from_attributes=True)


class VelocityChart(BaseModel):
    """Velocity chart data."""
    project_id: UUID
    sprints: List[Dict[str, Any]]  # sprint info with completed/committed points
    average_velocity: float
    velocity_trend: str = Field(pattern="^(increasing|decreasing|stable)$")
    predictability_score: float = Field(ge=0, le=100)
    
    model_config = ConfigDict(from_attributes=True)


class CumulativeFlowDiagram(BaseModel):
    """Cumulative flow diagram data."""
    project_id: UUID
    date_range: DateRange
    
    # Status categories with daily counts
    data_by_status: Dict[str, List[TimeSeriesDataPoint]]
    
    # Metrics
    average_wip: float
    throughput_rate: float
    
    model_config = ConfigDict(from_attributes=True)


class DashboardWidget(BaseModel):
    """Dashboard widget configuration."""
    id: UUID
    title: str
    type: ChartType
    metric: str
    config: Dict[str, Any]
    position: Dict[str, int]  # x, y, width, height
    
    model_config = ConfigDict(from_attributes=True)


class CustomDashboard(BaseModel):
    """Custom analytics dashboard."""
    id: UUID
    name: str
    description: Optional[str] = None
    widgets: List[DashboardWidget]
    is_public: bool = False
    created_by_id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)