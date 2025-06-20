"""Alerts service for handling alert operations."""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc

from models.server_metrics import ServerMetrics
from models.vm_metrics import VMMetrics
from models.server import Server
from models.virtual_machine import VirtualMachine
from schemas.metrics import (
    EntityType, MetricType, AlertRule, Alert, AlertStatus, AlertsResponse
)
from core.logging import get_logger

logger = get_logger("alerts_service")


class AlertsService:
    """Service class for alerts operations."""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Default alert rules (in a real system, these would be stored in DB)
        self.default_rules = [
            AlertRule(
                name="high_cpu_usage",
                entity_type=EntityType.SERVER,
                metric_type=MetricType.CPU,
                condition="> 90",
                threshold=90.0,
                duration_minutes=5,
                severity="warning"
            ),
            AlertRule(
                name="critical_cpu_usage",
                entity_type=EntityType.SERVER,
                metric_type=MetricType.CPU,
                condition="> 95",
                threshold=95.0,
                duration_minutes=2,
                severity="critical"
            ),
            AlertRule(
                name="low_memory",
                entity_type=EntityType.SERVER,
                metric_type=MetricType.MEMORY,
                condition="< 10",
                threshold=10.0,
                duration_minutes=2,
                severity="critical"
            ),
            AlertRule(
                name="vm_high_cpu",
                entity_type=EntityType.VM,
                metric_type=MetricType.CPU,
                condition="> 85",
                threshold=85.0,
                duration_minutes=10,
                severity="warning"
            ),
            AlertRule(
                name="vm_memory_pressure",
                entity_type=EntityType.VM,
                metric_type=MetricType.MEMORY,
                condition="> 90",
                threshold=90.0,
                duration_minutes=5,
                severity="warning"
            )
        ]
    
    def get_active_alerts(self) -> AlertsResponse:
        """Get all active alerts."""
        alerts = []
        
        # Check each rule against current metrics
        for rule in self.default_rules:
            if not rule.enabled:
                continue
                
            entities = self._get_entities_for_rule(rule)
            
            for entity in entities:
                alert = self._check_rule_for_entity(rule, entity)
                if alert:
                    alerts.append(alert)
        
        # Count alerts by severity
        active_count = len(alerts)
        critical_count = len([a for a in alerts if a.severity == "critical"])
        warning_count = len([a for a in alerts if a.severity == "warning"])
        
        return AlertsResponse(
            alerts=alerts,
            total=active_count,
            active_count=active_count,
            critical_count=critical_count,
            warning_count=warning_count
        )
    
    def get_alerts_for_entity(self, entity_type: EntityType, entity_id: int) -> List[Alert]:
        """Get alerts for a specific entity."""
        alerts = []
        
        for rule in self.default_rules:
            if not rule.enabled or rule.entity_type != entity_type:
                continue
            
            if entity_type == EntityType.SERVER:
                entity = self.db.query(Server).filter(Server.id == entity_id).first()
            else:
                entity = self.db.query(VirtualMachine).filter(VirtualMachine.id == entity_id).first()
            
            if entity:
                alert = self._check_rule_for_entity(rule, entity)
                if alert:
                    alerts.append(alert)
        
        return alerts
    
    def check_threshold_alerts(self) -> List[Alert]:
        """Check all threshold-based alerts and return triggered ones."""
        triggered_alerts = []
        
        for rule in self.default_rules:
            if not rule.enabled:
                continue
                
            entities = self._get_entities_for_rule(rule)
            
            for entity in entities:
                alert = self._check_rule_for_entity(rule, entity)
                if alert:
                    triggered_alerts.append(alert)
                    logger.info(f"Alert triggered: {alert.rule_name} for {alert.entity_type.value} {alert.entity_id}")
        
        return triggered_alerts
    
    def _get_entities_for_rule(self, rule: AlertRule):
        """Get all entities that should be checked for a rule."""
        if rule.entity_type == EntityType.SERVER:
            return self.db.query(Server).all()
        else:
            return self.db.query(VirtualMachine).all()
    
    def _check_rule_for_entity(self, rule: AlertRule, entity) -> Optional[Alert]:
        """Check if a rule is triggered for a specific entity."""
        # Get the appropriate metric name for the rule
        metric_name = self._get_metric_name_for_rule(rule)
        
        # Get recent metrics for the entity
        if rule.entity_type == EntityType.SERVER:
            metrics_table = ServerMetrics
            entity_id_field = ServerMetrics.server_id
            entity_name = entity.hostname
        else:
            metrics_table = VMMetrics
            entity_id_field = VMMetrics.vm_id
            entity_name = entity.name
        
        # Look for metrics in the last duration_minutes + 1 minute
        time_threshold = datetime.now() - timedelta(minutes=rule.duration_minutes + 1)
        
        recent_metrics = self.db.query(metrics_table).filter(
            and_(
                entity_id_field == entity.id,
                metrics_table.metric_name == metric_name,
                metrics_table.timestamp >= time_threshold
            )
        ).order_by(desc(metrics_table.timestamp)).all()
        
        if not recent_metrics:
            return None
        
        # Check if the condition has been met for the required duration
        current_value = recent_metrics[0].metric_value
        
        # Simple threshold check (in a real system, this would be more sophisticated)
        if self._evaluate_condition(current_value, rule.condition, rule.threshold):
            # Check if this condition has persisted for the required duration
            violation_start = self._find_violation_start(recent_metrics, rule)
            
            if violation_start and (datetime.now() - violation_start).total_seconds() >= rule.duration_minutes * 60:
                return Alert(
                    id=hash(f"{rule.name}_{entity.id}") % 10000,  # Simple ID generation
                    rule_name=rule.name,
                    entity_type=rule.entity_type,
                    entity_id=entity.id,
                    entity_name=entity_name,
                    metric_type=rule.metric_type,
                    current_value=current_value,
                    threshold=rule.threshold,
                    condition=rule.condition,
                    severity=rule.severity,
                    status=AlertStatus.ACTIVE,
                    triggered_at=violation_start,
                    last_updated=datetime.now(),
                    duration_minutes=int((datetime.now() - violation_start).total_seconds() / 60)
                )
        
        return None
    
    def _get_metric_name_for_rule(self, rule: AlertRule) -> str:
        """Get the actual metric name for a rule."""
        if rule.entity_type == EntityType.SERVER:
            mapping = {
                MetricType.CPU: "cpu_usage",
                MetricType.MEMORY: "memory_usage",
                MetricType.DISK: "disk_usage",
                MetricType.NETWORK: "network_rx_bytes"
            }
        else:  # VM
            mapping = {
                MetricType.CPU: "cpu_usage",
                MetricType.MEMORY: "memory_usage",
                MetricType.DISK: "disk_read_ops",
                MetricType.NETWORK: "network_rx_bytes"
            }
        
        return mapping.get(rule.metric_type, "cpu_usage")
    
    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        """Evaluate if a condition is met."""
        if condition.startswith(">"):
            return value > threshold
        elif condition.startswith("<"):
            return value < threshold
        elif condition.startswith(">="):
            return value >= threshold
        elif condition.startswith("<="):
            return value <= threshold
        elif condition.startswith("=="):
            return value == threshold
        else:
            # Default to greater than
            return value > threshold
    
    def _find_violation_start(self, metrics: List, rule: AlertRule) -> Optional[datetime]:
        """Find when a violation started based on recent metrics."""
        if not metrics:
            return None
        
        # Check metrics from most recent to oldest
        violation_start = None
        
        for metric in metrics:
            if self._evaluate_condition(metric.metric_value, rule.condition, rule.threshold):
                violation_start = metric.timestamp
            else:
                # Found a metric that doesn't violate the rule, so violation started after this
                break
        
        return violation_start
    
    def create_alert_rule(self, rule: AlertRule) -> AlertRule:
        """Create a new alert rule."""
        # In a real implementation, this would save to database
        self.default_rules.append(rule)
        logger.info(f"Created alert rule: {rule.name}")
        return rule
    
    def update_alert_rule(self, rule_name: str, updates: Dict[str, Any]) -> Optional[AlertRule]:
        """Update an existing alert rule."""
        for rule in self.default_rules:
            if rule.name == rule_name:
                for key, value in updates.items():
                    if hasattr(rule, key):
                        setattr(rule, key, value)
                logger.info(f"Updated alert rule: {rule_name}")
                return rule
        return None
    
    def delete_alert_rule(self, rule_name: str) -> bool:
        """Delete an alert rule."""
        for i, rule in enumerate(self.default_rules):
            if rule.name == rule_name:
                del self.default_rules[i]
                logger.info(f"Deleted alert rule: {rule_name}")
                return True
        return False
    
    def get_alert_rules(self) -> List[AlertRule]:
        """Get all alert rules."""
        return self.default_rules