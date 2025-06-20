"""Metrics API request and response schemas."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class MetricType(str, Enum):
    """Metric type enumeration."""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    SYSTEM = "system"
    PERFORMANCE = "performance"


class AggregationType(str, Enum):
    """Aggregation type enumeration."""
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    SUM = "sum"
    COUNT = "count"


class IntervalType(str, Enum):
    """Time interval enumeration."""
    FIVE_SECONDS = "5s"
    ONE_MINUTE = "1m"
    FIVE_MINUTES = "5m"
    ONE_HOUR = "1h"
    ONE_DAY = "1d"


class EntityType(str, Enum):
    """Entity type enumeration."""
    SERVER = "server"
    VM = "vm"


class MetricValue(BaseModel):
    """Individual metric value."""
    timestamp: datetime
    value: float
    unit: Optional[str] = None


class MetricData(BaseModel):
    """Metric data with series."""
    name: str
    entity_type: EntityType
    entity_id: int
    values: List[MetricValue]


class VMMetricsResponse(BaseModel):
    """VM metrics response schema."""
    id: int
    name: str
    uuid: str
    timestamp: datetime
    cpu_usage_percent: Optional[float] = None
    cpu_steal_time: Optional[float] = None
    cpu_wait_time: Optional[float] = None
    memory_usage_percent: Optional[float] = None
    memory_active_mb: Optional[float] = None
    memory_inactive_mb: Optional[float] = None
    memory_balloon_mb: Optional[float] = None
    disk_read_ops: Optional[int] = None
    disk_write_ops: Optional[int] = None
    disk_read_bytes: Optional[int] = None
    disk_write_bytes: Optional[int] = None
    network_rx_bytes: Optional[int] = None
    network_tx_bytes: Optional[int] = None
    network_rx_packets: Optional[int] = None
    network_tx_packets: Optional[int] = None
    response_time_ms: Optional[float] = None
    iops: Optional[float] = None


class HistoricalMetricsQuery(BaseModel):
    """Historical metrics query parameters."""
    metric: Optional[List[MetricType]] = Field(None, description="Metrics to retrieve")
    interval: Optional[IntervalType] = Field(IntervalType.FIVE_MINUTES, description="Time interval")
    start: Optional[datetime] = Field(None, description="Start time")
    end: Optional[datetime] = Field(None, description="End time")
    aggregation: Optional[AggregationType] = Field(AggregationType.AVG, description="Aggregation function")


class HistoricalMetricsResponse(BaseModel):
    """Historical metrics response."""
    entity_type: EntityType
    entity_id: int
    entity_name: str
    query: HistoricalMetricsQuery
    metrics: List[MetricData]
    total_points: int


class CustomMetricsQuery(BaseModel):
    """Custom metrics query schema."""
    entity_type: EntityType
    entity_ids: Optional[List[int]] = Field(None, description="Entity IDs to query")
    metrics: List[MetricType] = Field(..., description="Metrics to retrieve")
    start: datetime = Field(..., description="Start time")
    end: datetime = Field(..., description="End time")
    interval: IntervalType = Field(IntervalType.FIVE_MINUTES, description="Time interval")
    aggregation: AggregationType = Field(AggregationType.AVG, description="Aggregation function")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters")


class CustomMetricsResponse(BaseModel):
    """Custom metrics query response."""
    query: CustomMetricsQuery
    results: List[HistoricalMetricsResponse]
    execution_time_ms: float


class AlertRule(BaseModel):
    """Alert rule definition."""
    name: str
    entity_type: EntityType
    metric_type: MetricType
    condition: str  # e.g., "> 90", "< 10%"
    threshold: float
    duration_minutes: int = Field(default=5, description="Duration in minutes")
    severity: str = Field(default="warning", description="Alert severity")
    enabled: bool = Field(default=True)


class AlertStatus(str, Enum):
    """Alert status enumeration."""
    ACTIVE = "active"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"


class Alert(BaseModel):
    """Active alert schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    rule_name: str
    entity_type: EntityType
    entity_id: int
    entity_name: str
    metric_type: MetricType
    current_value: float
    threshold: float
    condition: str
    severity: str
    status: AlertStatus
    triggered_at: datetime
    last_updated: datetime
    duration_minutes: int


class AlertsResponse(BaseModel):
    """Alerts response schema."""
    alerts: List[Alert]
    total: int
    active_count: int
    critical_count: int
    warning_count: int


class MetricsCollectionStatus(BaseModel):
    """Metrics collection status."""
    entity_type: EntityType
    entity_id: int
    last_collection: Optional[datetime] = None
    collection_interval_seconds: int = Field(default=5)
    is_collecting: bool = Field(default=True)
    error_count: int = Field(default=0)
    last_error: Optional[str] = None