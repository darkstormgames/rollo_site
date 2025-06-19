"""Event broadcasting system for WebSocket real-time updates."""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass

from core.logging import get_logger
from websocket.manager import websocket_manager

logger = get_logger("websocket_events")


@dataclass
class EventData:
    """Base class for event data."""
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp
        }


@dataclass 
class VMStatusEvent(EventData):
    """VM status change event."""
    vm_id: int
    vm_name: str
    old_status: str
    new_status: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "vm_id": self.vm_id,
            "vm_name": self.vm_name,
            "old_status": self.old_status,
            "new_status": self.new_status
        }


@dataclass
class VMCreatedEvent(EventData):
    """VM creation event."""
    vm: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "vm": self.vm
        }


@dataclass
class VMDeletedEvent(EventData):
    """VM deletion event."""
    vm_id: int
    vm_name: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "vm_id": self.vm_id,
            "vm_name": self.vm_name
        }


@dataclass
class VMMetricsEvent(EventData):
    """VM metrics update event."""
    vm_id: int
    vm_name: str
    metrics: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "vm_id": self.vm_id,
            "vm_name": self.vm_name,
            "metrics": self.metrics
        }


@dataclass
class ServerStatusEvent(EventData):
    """Server status change event."""
    server_id: int
    hostname: str
    old_status: str
    new_status: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "server_id": self.server_id,
            "hostname": self.hostname,
            "old_status": self.old_status,
            "new_status": self.new_status
        }


@dataclass
class ServerRegisteredEvent(EventData):
    """Server registration event."""
    server: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "server": self.server
        }


@dataclass
class ServerRemovedEvent(EventData):
    """Server removal event."""
    server_id: int
    hostname: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "server_id": self.server_id,
            "hostname": self.hostname
        }


@dataclass
class ServerMetricsEvent(EventData):
    """Server metrics update event."""
    server_id: int
    hostname: str
    metrics: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "server_id": self.server_id,
            "hostname": self.hostname,
            "metrics": self.metrics
        }


@dataclass
class ProgressEvent(EventData):
    """Progress update event."""
    operation_id: str
    operation_type: str
    progress_percent: int
    status: str
    message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "operation_id": self.operation_id,
            "operation_type": self.operation_type,
            "progress_percent": self.progress_percent,
            "status": self.status,
            "message": self.message
        }


@dataclass
class AlertEvent(EventData):
    """System alert event."""
    alert_id: str
    alert_type: str
    severity: str
    title: str
    message: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "alert_id": self.alert_id,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "title": self.title,
            "message": self.message,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id
        }


class EventBroadcaster:
    """Broadcasts events to WebSocket connections."""
    
    def __init__(self):
        self.manager = websocket_manager
    
    async def broadcast_vm_status_change(self, vm_id: int, vm_name: str, old_status: str, new_status: str):
        """Broadcast VM status change event."""
        event = VMStatusEvent(
            vm_id=vm_id,
            vm_name=vm_name,
            old_status=old_status,
            new_status=new_status,
            timestamp=datetime.utcnow().isoformat()
        )
        
        message = {
            "type": "vm_status_changed",
            "data": event.to_dict(),
            "timestamp": event.timestamp
        }
        
        # Broadcast to vm_status room and VM-specific subscribers
        await asyncio.gather(
            self.manager.broadcast_to_room("vm_status", message),
            self.manager.broadcast_to_vm(vm_id, message)
        )
        
        logger.info(f"Broadcasted VM status change: {vm_name} {old_status} -> {new_status}")
    
    async def broadcast_vm_created(self, vm_data: Dict[str, Any]):
        """Broadcast VM creation event."""
        event = VMCreatedEvent(
            vm=vm_data,
            timestamp=datetime.utcnow().isoformat()
        )
        
        message = {
            "type": "vm_created",
            "data": event.to_dict(),
            "timestamp": event.timestamp
        }
        
        await self.manager.broadcast_to_room("vm_status", message)
        logger.info(f"Broadcasted VM created: {vm_data.get('name', 'Unknown')}")
    
    async def broadcast_vm_deleted(self, vm_id: int, vm_name: str):
        """Broadcast VM deletion event."""
        event = VMDeletedEvent(
            vm_id=vm_id,
            vm_name=vm_name,
            timestamp=datetime.utcnow().isoformat()
        )
        
        message = {
            "type": "vm_deleted",
            "data": event.to_dict(),
            "timestamp": event.timestamp
        }
        
        # Broadcast to vm_status room and VM-specific subscribers
        await asyncio.gather(
            self.manager.broadcast_to_room("vm_status", message),
            self.manager.broadcast_to_vm(vm_id, message)
        )
        
        logger.info(f"Broadcasted VM deleted: {vm_name}")
    
    async def broadcast_vm_metrics(self, vm_id: int, vm_name: str, metrics: Dict[str, Any]):
        """Broadcast VM metrics update."""
        event = VMMetricsEvent(
            vm_id=vm_id,
            vm_name=vm_name,
            metrics=metrics,
            timestamp=datetime.utcnow().isoformat()
        )
        
        message = {
            "type": "vm_metrics_update",
            "data": event.to_dict(),
            "timestamp": event.timestamp
        }
        
        # Broadcast to vm_metrics room and VM-specific subscribers
        await asyncio.gather(
            self.manager.broadcast_to_room("vm_metrics", message),
            self.manager.broadcast_to_vm(vm_id, message)
        )
        
        logger.debug(f"Broadcasted VM metrics: {vm_name}")
    
    async def broadcast_server_status_change(self, server_id: int, hostname: str, old_status: str, new_status: str):
        """Broadcast server status change event."""
        event = ServerStatusEvent(
            server_id=server_id,
            hostname=hostname,
            old_status=old_status,
            new_status=new_status,
            timestamp=datetime.utcnow().isoformat()
        )
        
        message = {
            "type": "server_status_changed",
            "data": event.to_dict(),
            "timestamp": event.timestamp
        }
        
        # Broadcast to server_status room and server-specific subscribers
        await asyncio.gather(
            self.manager.broadcast_to_room("server_status", message),
            self.manager.broadcast_to_server(server_id, message)
        )
        
        logger.info(f"Broadcasted server status change: {hostname} {old_status} -> {new_status}")
    
    async def broadcast_server_registered(self, server_data: Dict[str, Any]):
        """Broadcast server registration event."""
        event = ServerRegisteredEvent(
            server=server_data,
            timestamp=datetime.utcnow().isoformat()
        )
        
        message = {
            "type": "server_registered",
            "data": event.to_dict(),
            "timestamp": event.timestamp
        }
        
        await self.manager.broadcast_to_room("server_status", message)
        logger.info(f"Broadcasted server registered: {server_data.get('hostname', 'Unknown')}")
    
    async def broadcast_server_removed(self, server_id: int, hostname: str):
        """Broadcast server removal event."""
        event = ServerRemovedEvent(
            server_id=server_id,
            hostname=hostname,
            timestamp=datetime.utcnow().isoformat()
        )
        
        message = {
            "type": "server_removed",
            "data": event.to_dict(),
            "timestamp": event.timestamp
        }
        
        # Broadcast to server_status room and server-specific subscribers
        await asyncio.gather(
            self.manager.broadcast_to_room("server_status", message),
            self.manager.broadcast_to_server(server_id, message)
        )
        
        logger.info(f"Broadcasted server removed: {hostname}")
    
    async def broadcast_server_metrics(self, server_id: int, hostname: str, metrics: Dict[str, Any]):
        """Broadcast server metrics update."""
        event = ServerMetricsEvent(
            server_id=server_id,
            hostname=hostname,
            metrics=metrics,
            timestamp=datetime.utcnow().isoformat()
        )
        
        message = {
            "type": "server_metrics_update",
            "data": event.to_dict(),
            "timestamp": event.timestamp
        }
        
        # Broadcast to server_metrics room and server-specific subscribers
        await asyncio.gather(
            self.manager.broadcast_to_room("server_metrics", message),
            self.manager.broadcast_to_server(server_id, message)
        )
        
        logger.debug(f"Broadcasted server metrics: {hostname}")
    
    async def broadcast_progress_update(self, operation_id: str, operation_type: str, 
                                      progress_percent: int, status: str, message: Optional[str] = None):
        """Broadcast operation progress update."""
        event = ProgressEvent(
            operation_id=operation_id,
            operation_type=operation_type,
            progress_percent=progress_percent,
            status=status,
            message=message,
            timestamp=datetime.utcnow().isoformat()
        )
        
        progress_message = {
            "type": "progress",
            "data": event.to_dict(),
            "timestamp": event.timestamp
        }
        
        # Broadcast to global room for progress updates
        await self.manager.broadcast_to_room("global", progress_message)
        logger.debug(f"Broadcasted progress: {operation_type} {progress_percent}%")
    
    async def broadcast_alert(self, alert_id: str, alert_type: str, severity: str, 
                            title: str, message: str, entity_type: Optional[str] = None, 
                            entity_id: Optional[int] = None):
        """Broadcast system alert."""
        event = AlertEvent(
            alert_id=alert_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            entity_type=entity_type,
            entity_id=entity_id,
            timestamp=datetime.utcnow().isoformat()
        )
        
        alert_message = {
            "type": "alert",
            "data": event.to_dict(),
            "timestamp": event.timestamp
        }
        
        # Broadcast to global room for alerts
        await self.manager.broadcast_to_room("global", alert_message)
        
        # Also broadcast to entity-specific rooms if applicable
        if entity_type == "vm" and entity_id:
            await self.manager.broadcast_to_vm(entity_id, alert_message)
        elif entity_type == "server" and entity_id:
            await self.manager.broadcast_to_server(entity_id, alert_message)
        
        logger.info(f"Broadcasted alert: {severity} - {title}")


# Global event broadcaster instance
event_broadcaster = EventBroadcaster()