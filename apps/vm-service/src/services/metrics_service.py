"""Metrics service for handling metrics operations."""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc

from models.server_metrics import ServerMetrics
from models.vm_metrics import VMMetrics
from models.server import Server
from models.virtual_machine import VirtualMachine
from schemas.metrics import (
    EntityType, MetricType, AggregationType, IntervalType,
    MetricData, MetricValue, HistoricalMetricsQuery, HistoricalMetricsResponse,
    CustomMetricsQuery, CustomMetricsResponse, VMMetricsResponse,
    MetricsCollectionStatus
)
from core.logging import get_logger

logger = get_logger("metrics_service")


class MetricsService:
    """Service class for metrics operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_server_metrics(self, server_id: int) -> Optional[Dict[str, Any]]:
        """Get current server metrics."""
        server = self.db.query(Server).filter(Server.id == server_id).first()
        if not server:
            return None
        
        # Get latest metrics for each metric type
        latest_metrics = {}
        for metric_type in ["cpu_usage", "memory_usage", "disk_usage", "network_rx", "network_tx", "load_average"]:
            metric = self.db.query(ServerMetrics).filter(
                and_(
                    ServerMetrics.server_id == server_id,
                    ServerMetrics.metric_name == metric_type
                )
            ).order_by(desc(ServerMetrics.timestamp)).first()
            
            if metric:
                latest_metrics[metric_type] = {
                    "value": metric.metric_value,
                    "unit": metric.metric_unit,
                    "timestamp": metric.timestamp
                }
        
        return {
            "id": server.id,
            "hostname": server.hostname,
            "timestamp": datetime.now(),
            "metrics": latest_metrics
        }
    
    def get_vm_metrics(self, vm_id: int) -> Optional[VMMetricsResponse]:
        """Get current VM metrics."""
        vm = self.db.query(VirtualMachine).filter(VirtualMachine.id == vm_id).first()
        if not vm:
            return None
        
        # Get latest metrics for each metric type
        latest_metrics = {}
        vm_metric_types = [
            "cpu_usage", "cpu_steal_time", "cpu_wait_time",
            "memory_usage", "memory_active", "memory_inactive", "memory_balloon",
            "disk_read_ops", "disk_write_ops", "disk_read_bytes", "disk_write_bytes",
            "network_rx_bytes", "network_tx_bytes", "network_rx_packets", "network_tx_packets",
            "response_time", "iops"
        ]
        
        for metric_type in vm_metric_types:
            metric = self.db.query(VMMetrics).filter(
                and_(
                    VMMetrics.vm_id == vm_id,
                    VMMetrics.metric_name == metric_type
                )
            ).order_by(desc(VMMetrics.timestamp)).first()
            
            if metric:
                latest_metrics[metric_type] = metric.metric_value
        
        return VMMetricsResponse(
            id=vm.id,
            name=vm.name,
            uuid=vm.uuid,
            timestamp=datetime.now(),
            cpu_usage_percent=latest_metrics.get("cpu_usage"),
            cpu_steal_time=latest_metrics.get("cpu_steal_time"),
            cpu_wait_time=latest_metrics.get("cpu_wait_time"),
            memory_usage_percent=latest_metrics.get("memory_usage"),
            memory_active_mb=latest_metrics.get("memory_active"),
            memory_inactive_mb=latest_metrics.get("memory_inactive"),
            memory_balloon_mb=latest_metrics.get("memory_balloon"),
            disk_read_ops=latest_metrics.get("disk_read_ops"),
            disk_write_ops=latest_metrics.get("disk_write_ops"),
            disk_read_bytes=latest_metrics.get("disk_read_bytes"),
            disk_write_bytes=latest_metrics.get("disk_write_bytes"),
            network_rx_bytes=latest_metrics.get("network_rx_bytes"),
            network_tx_bytes=latest_metrics.get("network_tx_bytes"),
            network_rx_packets=latest_metrics.get("network_rx_packets"),
            network_tx_packets=latest_metrics.get("network_tx_packets"),
            response_time_ms=latest_metrics.get("response_time"),
            iops=latest_metrics.get("iops")
        )
    
    def get_historical_metrics(
        self, 
        entity_type: EntityType, 
        entity_id: int, 
        query: HistoricalMetricsQuery
    ) -> Optional[HistoricalMetricsResponse]:
        """Get historical metrics for an entity."""
        
        # Get entity info
        if entity_type == EntityType.SERVER:
            entity = self.db.query(Server).filter(Server.id == entity_id).first()
            metrics_table = ServerMetrics
            entity_id_field = ServerMetrics.server_id
        else:  # VM
            entity = self.db.query(VirtualMachine).filter(VirtualMachine.id == entity_id).first()
            metrics_table = VMMetrics
            entity_id_field = VMMetrics.vm_id
        
        if not entity:
            return None
        
        # Build query conditions
        conditions = [entity_id_field == entity_id]
        
        if query.start:
            conditions.append(metrics_table.timestamp >= query.start)
        if query.end:
            conditions.append(metrics_table.timestamp <= query.end)
        
        # Get metrics
        metrics_data = []
        metric_types = query.metric or [MetricType.CPU, MetricType.MEMORY, MetricType.DISK, MetricType.NETWORK]
        
        for metric_type in metric_types:
            # Map metric type to actual metric names
            metric_names = self._get_metric_names_for_type(metric_type, entity_type)
            
            for metric_name in metric_names:
                metric_conditions = conditions + [metrics_table.metric_name == metric_name]
                
                metrics_query = self.db.query(metrics_table).filter(and_(*metric_conditions))
                
                if query.interval and query.interval != IntervalType.FIVE_SECONDS:
                    # Apply aggregation for larger intervals
                    metrics_query = self._apply_aggregation(metrics_query, query.interval, query.aggregation)
                
                metrics = metrics_query.order_by(metrics_table.timestamp).all()
                
                if metrics:
                    values = [
                        MetricValue(
                            timestamp=metric.timestamp,
                            value=metric.metric_value,
                            unit=metric.metric_unit
                        ) for metric in metrics
                    ]
                    
                    metrics_data.append(MetricData(
                        name=metric_name,
                        entity_type=entity_type,
                        entity_id=entity_id,
                        values=values
                    ))
        
        total_points = sum(len(metric.values) for metric in metrics_data)
        
        return HistoricalMetricsResponse(
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity.hostname if entity_type == EntityType.SERVER else entity.name,
            query=query,
            metrics=metrics_data,
            total_points=total_points
        )
    
    def custom_metrics_query(self, query: CustomMetricsQuery) -> CustomMetricsResponse:
        """Execute custom metrics query."""
        start_time = datetime.now()
        results = []
        
        entity_ids = query.entity_ids
        if not entity_ids:
            # Get all entities of the specified type
            if query.entity_type == EntityType.SERVER:
                entities = self.db.query(Server).all()
            else:
                entities = self.db.query(VirtualMachine).all()
            entity_ids = [entity.id for entity in entities]
        
        for entity_id in entity_ids:
            historical_query = HistoricalMetricsQuery(
                metric=query.metrics,
                interval=query.interval,
                start=query.start,
                end=query.end,
                aggregation=query.aggregation
            )
            
            result = self.get_historical_metrics(query.entity_type, entity_id, historical_query)
            if result:
                results.append(result)
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return CustomMetricsResponse(
            query=query,
            results=results,
            execution_time_ms=execution_time
        )
    
    def record_server_metric(self, server_id: int, metric_name: str, value: float, unit: str = None):
        """Record a server metric."""
        metric = ServerMetrics.record_metric(server_id, metric_name, value, unit)
        self.db.add(metric)
        self.db.commit()
    
    def record_vm_metric(self, vm_id: int, metric_name: str, value: float, unit: str = None):
        """Record a VM metric."""
        metric = VMMetrics.record_metric(vm_id, metric_name, value, unit)
        self.db.add(metric)
        self.db.commit()
    
    def get_collection_status(self, entity_type: EntityType, entity_id: int) -> Optional[MetricsCollectionStatus]:
        """Get metrics collection status for an entity."""
        if entity_type == EntityType.SERVER:
            entity = self.db.query(Server).filter(Server.id == entity_id).first()
            latest_metric = self.db.query(ServerMetrics).filter(
                ServerMetrics.server_id == entity_id
            ).order_by(desc(ServerMetrics.timestamp)).first()
        else:
            entity = self.db.query(VirtualMachine).filter(VirtualMachine.id == entity_id).first()
            latest_metric = self.db.query(VMMetrics).filter(
                VMMetrics.vm_id == entity_id
            ).order_by(desc(VMMetrics.timestamp)).first()
        
        if not entity:
            return None
        
        return MetricsCollectionStatus(
            entity_type=entity_type,
            entity_id=entity_id,
            last_collection=latest_metric.timestamp if latest_metric else None,
            collection_interval_seconds=5,
            is_collecting=True,  # Would be determined by actual collection status
            error_count=0,
            last_error=None
        )
    
    def _get_metric_names_for_type(self, metric_type: MetricType, entity_type: EntityType) -> List[str]:
        """Get actual metric names for a metric type."""
        if entity_type == EntityType.SERVER:
            mapping = {
                MetricType.CPU: ["cpu_usage", "load_average"],
                MetricType.MEMORY: ["memory_usage", "memory_free", "memory_cached"],
                MetricType.DISK: ["disk_usage", "disk_read_bytes", "disk_write_bytes"],
                MetricType.NETWORK: ["network_rx_bytes", "network_tx_bytes"],
                MetricType.SYSTEM: ["uptime", "processes"]
            }
        else:  # VM
            mapping = {
                MetricType.CPU: ["cpu_usage", "cpu_steal_time", "cpu_wait_time"],
                MetricType.MEMORY: ["memory_usage", "memory_active", "memory_inactive", "memory_balloon"],
                MetricType.DISK: ["disk_read_ops", "disk_write_ops", "disk_read_bytes", "disk_write_bytes"],
                MetricType.NETWORK: ["network_rx_bytes", "network_tx_bytes", "network_rx_packets", "network_tx_packets"],
                MetricType.PERFORMANCE: ["response_time", "iops"]
            }
        
        return mapping.get(metric_type, [])
    
    def _apply_aggregation(self, query, interval: IntervalType, aggregation: AggregationType):
        """Apply time-based aggregation to metrics query."""
        # This is a simplified implementation
        # In a real system, you'd use proper time-series aggregation functions
        
        if aggregation == AggregationType.AVG:
            return query
        elif aggregation == AggregationType.MAX:
            return query
        elif aggregation == AggregationType.MIN:
            return query
        elif aggregation == AggregationType.SUM:
            return query
        else:
            return query