"""Metrics API endpoints."""

from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from core.auth import get_current_active_user, require_permissions
from core.logging import get_logger
from models.base import DatabaseSession
from models.user import User
from services.metrics_service import MetricsService
from services.alerts_service import AlertsService
from schemas.metrics import (
    EntityType, MetricType, AggregationType, IntervalType,
    VMMetricsResponse, HistoricalMetricsQuery, HistoricalMetricsResponse,
    CustomMetricsQuery, CustomMetricsResponse, AlertsResponse,
    MetricsCollectionStatus
)
from schemas.server import ServerMetricsResponse

logger = get_logger("metrics_api")
router = APIRouter()


def get_db() -> Session:
    """Get database session."""
    return DatabaseSession.get_session()


def get_metrics_service(db: Session = Depends(get_db)) -> MetricsService:
    """Get metrics service instance."""
    return MetricsService(db)


def get_alerts_service(db: Session = Depends(get_db)) -> AlertsService:
    """Get alerts service instance."""
    return AlertsService(db)


@router.get("/servers/{server_id}", response_model=ServerMetricsResponse)
async def get_server_metrics(
    server_id: int,
    current_user: User = Depends(get_current_active_user),
    metrics_service: MetricsService = Depends(get_metrics_service)
):
    """Get current server metrics."""
    
    # Check permissions (basic implementation)
    # In a real system, you'd check if user has access to this server
    
    metrics_data = metrics_service.get_server_metrics(server_id)
    if not metrics_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    # Convert to response format
    return ServerMetricsResponse(
        id=metrics_data["id"],
        hostname=metrics_data["hostname"],
        timestamp=metrics_data["timestamp"],
        cpu_usage_percent=metrics_data["metrics"].get("cpu_usage", {}).get("value"),
        memory_usage_percent=metrics_data["metrics"].get("memory_usage", {}).get("value"),
        memory_used_gb=None,  # Would calculate from available data
        memory_total_gb=None,  # Would get from server specs
        disk_usage_percent=metrics_data["metrics"].get("disk_usage", {}).get("value"),
        disk_used_gb=None,  # Would calculate from available data
        disk_total_gb=None,  # Would get from server specs
        network_rx_bytes=metrics_data["metrics"].get("network_rx", {}).get("value"),
        network_tx_bytes=metrics_data["metrics"].get("network_tx", {}).get("value"),
        load_average=metrics_data["metrics"].get("load_average", {}).get("value")
    )


@router.get("/vms/{vm_id}", response_model=VMMetricsResponse)
async def get_vm_metrics(
    vm_id: int,
    current_user: User = Depends(get_current_active_user),
    metrics_service: MetricsService = Depends(get_metrics_service)
):
    """Get current VM metrics."""
    
    vm_metrics = metrics_service.get_vm_metrics(vm_id)
    if not vm_metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VM not found"
        )
    
    return vm_metrics


@router.get("/servers/{server_id}/history", response_model=HistoricalMetricsResponse)
async def get_server_historical_metrics(
    server_id: int,
    metric: Optional[List[MetricType]] = Query(None, description="Metrics to retrieve"),
    interval: Optional[IntervalType] = Query(IntervalType.FIVE_MINUTES, description="Time interval"),
    start: Optional[datetime] = Query(None, description="Start time"),
    end: Optional[datetime] = Query(None, description="End time"),
    aggregation: Optional[AggregationType] = Query(AggregationType.AVG, description="Aggregation function"),
    current_user: User = Depends(get_current_active_user),
    metrics_service: MetricsService = Depends(get_metrics_service)
):
    """Get historical server metrics."""
    
    # Set default time range if not provided
    if not end:
        end = datetime.now()
    if not start:
        start = end - timedelta(hours=24)  # Last 24 hours by default
    
    query = HistoricalMetricsQuery(
        metric=metric,
        interval=interval,
        start=start,
        end=end,
        aggregation=aggregation
    )
    
    result = metrics_service.get_historical_metrics(EntityType.SERVER, server_id, query)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    return result


@router.get("/vms/{vm_id}/history", response_model=HistoricalMetricsResponse)
async def get_vm_historical_metrics(
    vm_id: int,
    metric: Optional[List[MetricType]] = Query(None, description="Metrics to retrieve"),
    interval: Optional[IntervalType] = Query(IntervalType.FIVE_MINUTES, description="Time interval"),
    start: Optional[datetime] = Query(None, description="Start time"),
    end: Optional[datetime] = Query(None, description="End time"),
    aggregation: Optional[AggregationType] = Query(AggregationType.AVG, description="Aggregation function"),
    current_user: User = Depends(get_current_active_user),
    metrics_service: MetricsService = Depends(get_metrics_service)
):
    """Get historical VM metrics."""
    
    # Set default time range if not provided
    if not end:
        end = datetime.now()
    if not start:
        start = end - timedelta(hours=24)  # Last 24 hours by default
    
    query = HistoricalMetricsQuery(
        metric=metric,
        interval=interval,
        start=start,
        end=end,
        aggregation=aggregation
    )
    
    result = metrics_service.get_historical_metrics(EntityType.VM, vm_id, query)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VM not found"
        )
    
    return result


@router.post("/query", response_model=CustomMetricsResponse)
async def custom_metrics_query(
    query: CustomMetricsQuery,
    current_user: User = Depends(get_current_active_user),
    metrics_service: MetricsService = Depends(get_metrics_service)
):
    """Execute custom metrics query."""
    
    # Validate query parameters
    if query.end <= query.start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End time must be after start time"
        )
    
    # Limit query range to prevent abuse
    max_range = timedelta(days=30)
    if query.end - query.start > max_range:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query range cannot exceed 30 days"
        )
    
    try:
        result = metrics_service.custom_metrics_query(query)
        return result
    except Exception as e:
        logger.error(f"Error executing custom metrics query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error executing query"
        )


@router.get("/alerts", response_model=AlertsResponse)
async def get_alerts(
    current_user: User = Depends(get_current_active_user),
    alerts_service: AlertsService = Depends(get_alerts_service)
):
    """Get active alerts."""
    
    try:
        alerts = alerts_service.get_active_alerts()
        return alerts
    except Exception as e:
        logger.error(f"Error retrieving alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving alerts"
        )


@router.get("/status/{entity_type}/{entity_id}", response_model=MetricsCollectionStatus)
async def get_metrics_collection_status(
    entity_type: EntityType,
    entity_id: int,
    current_user: User = Depends(get_current_active_user),
    metrics_service: MetricsService = Depends(get_metrics_service)
):
    """Get metrics collection status for an entity."""
    
    status_info = metrics_service.get_collection_status(entity_type, entity_id)
    if not status_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{entity_type.value.capitalize()} not found"
        )
    
    return status_info


# Additional endpoints for recording metrics (typically called by agents)
@router.post("/servers/{server_id}/record")
async def record_server_metric(
    server_id: int,
    metric_name: str,
    value: float,
    unit: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    metrics_service: MetricsService = Depends(get_metrics_service)
):
    """Record a server metric (used by monitoring agents)."""
    
    try:
        metrics_service.record_server_metric(server_id, metric_name, value, unit)
        return {"message": "Metric recorded successfully"}
    except Exception as e:
        logger.error(f"Error recording server metric: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error recording metric"
        )


@router.post("/vms/{vm_id}/record")
async def record_vm_metric(
    vm_id: int,
    metric_name: str,
    value: float,
    unit: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    metrics_service: MetricsService = Depends(get_metrics_service)
):
    """Record a VM metric (used by monitoring agents)."""
    
    try:
        metrics_service.record_vm_metric(vm_id, metric_name, value, unit)
        return {"message": "Metric recorded successfully"}
    except Exception as e:
        logger.error(f"Error recording VM metric: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error recording metric"
        )