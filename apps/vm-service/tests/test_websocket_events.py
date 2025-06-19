"""Tests for WebSocket event broadcaster."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from websocket.events import EventBroadcaster, VMStatusEvent, ProgressEvent, AlertEvent
from websocket.manager import WebSocketManager


@pytest.fixture
def mock_manager():
    """Create a mock WebSocket manager for testing."""
    manager = Mock(spec=WebSocketManager)
    manager.broadcast_to_room = AsyncMock()
    manager.broadcast_to_vm = AsyncMock()
    manager.broadcast_to_server = AsyncMock()
    return manager


@pytest.fixture
def broadcaster(mock_manager):
    """Create an EventBroadcaster with mocked manager."""
    with patch('websocket.events.websocket_manager', mock_manager):
        return EventBroadcaster()


class TestEventBroadcaster:
    """Test event broadcasting functionality."""
    
    async def test_broadcast_vm_status_change(self, broadcaster, mock_manager):
        """Test broadcasting VM status change events."""
        await broadcaster.broadcast_vm_status_change(
            vm_id=1,
            vm_name="test-vm",
            old_status="stopped",
            new_status="running"
        )
        
        # Should broadcast to both vm_status room and VM-specific subscribers
        assert mock_manager.broadcast_to_room.call_count == 1
        assert mock_manager.broadcast_to_vm.call_count == 1
        
        # Check the room broadcast
        room_call = mock_manager.broadcast_to_room.call_args
        assert room_call[0][0] == "vm_status"
        message = room_call[0][1]
        assert message["type"] == "vm_status_changed"
        assert message["data"]["vm_id"] == 1
        assert message["data"]["vm_name"] == "test-vm"
        assert message["data"]["old_status"] == "stopped"
        assert message["data"]["new_status"] == "running"
        
        # Check the VM-specific broadcast
        vm_call = mock_manager.broadcast_to_vm.call_args
        assert vm_call[0][0] == 1
        assert vm_call[0][1]["type"] == "vm_status_changed"
    
    async def test_broadcast_vm_created(self, broadcaster, mock_manager):
        """Test broadcasting VM creation events."""
        vm_data = {
            "id": 1,
            "name": "new-vm",
            "uuid": "test-uuid",
            "status": "running",
            "server_id": 1
        }
        
        await broadcaster.broadcast_vm_created(vm_data)
        
        # Should broadcast only to vm_status room (not VM-specific since it's new)
        assert mock_manager.broadcast_to_room.call_count == 1
        assert mock_manager.broadcast_to_vm.call_count == 0
        
        room_call = mock_manager.broadcast_to_room.call_args
        assert room_call[0][0] == "vm_status"
        message = room_call[0][1]
        assert message["type"] == "vm_created"
        assert message["data"]["vm"] == vm_data
    
    async def test_broadcast_vm_deleted(self, broadcaster, mock_manager):
        """Test broadcasting VM deletion events."""
        await broadcaster.broadcast_vm_deleted(vm_id=1, vm_name="deleted-vm")
        
        # Should broadcast to both vm_status room and VM-specific subscribers
        assert mock_manager.broadcast_to_room.call_count == 1
        assert mock_manager.broadcast_to_vm.call_count == 1
        
        room_call = mock_manager.broadcast_to_room.call_args
        message = room_call[0][1]
        assert message["type"] == "vm_deleted"
        assert message["data"]["vm_id"] == 1
        assert message["data"]["vm_name"] == "deleted-vm"
    
    async def test_broadcast_vm_metrics(self, broadcaster, mock_manager):
        """Test broadcasting VM metrics updates."""
        metrics = {
            "cpu_usage_percent": 75.5,
            "memory_usage_percent": 60.2,
            "memory_used_mb": 1024
        }
        
        await broadcaster.broadcast_vm_metrics(
            vm_id=1,
            vm_name="test-vm",
            metrics=metrics
        )
        
        # Should broadcast to both vm_metrics room and VM-specific subscribers
        assert mock_manager.broadcast_to_room.call_count == 1
        assert mock_manager.broadcast_to_vm.call_count == 1
        
        room_call = mock_manager.broadcast_to_room.call_args
        assert room_call[0][0] == "vm_metrics"
        message = room_call[0][1]
        assert message["type"] == "vm_metrics_update"
        assert message["data"]["vm_id"] == 1
        assert message["data"]["vm_name"] == "test-vm"
        assert message["data"]["metrics"] == metrics
    
    async def test_broadcast_server_status_change(self, broadcaster, mock_manager):
        """Test broadcasting server status change events."""
        await broadcaster.broadcast_server_status_change(
            server_id=1,
            hostname="test-server",
            old_status="offline",
            new_status="online"
        )
        
        # Should broadcast to both server_status room and server-specific subscribers
        assert mock_manager.broadcast_to_room.call_count == 1
        assert mock_manager.broadcast_to_server.call_count == 1
        
        room_call = mock_manager.broadcast_to_room.call_args
        assert room_call[0][0] == "server_status"
        message = room_call[0][1]
        assert message["type"] == "server_status_changed"
        assert message["data"]["server_id"] == 1
        assert message["data"]["hostname"] == "test-server"
        assert message["data"]["old_status"] == "offline"
        assert message["data"]["new_status"] == "online"
    
    async def test_broadcast_server_metrics(self, broadcaster, mock_manager):
        """Test broadcasting server metrics updates."""
        metrics = {
            "cpu_usage_percent": 45.3,
            "memory_usage_percent": 70.1,
            "load_average": 2.5,
            "disk_usage_percent": 85.0
        }
        
        await broadcaster.broadcast_server_metrics(
            server_id=1,
            hostname="test-server",
            metrics=metrics
        )
        
        # Should broadcast to both server_metrics room and server-specific subscribers
        assert mock_manager.broadcast_to_room.call_count == 1
        assert mock_manager.broadcast_to_server.call_count == 1
        
        room_call = mock_manager.broadcast_to_room.call_args
        assert room_call[0][0] == "server_metrics"
        message = room_call[0][1]
        assert message["type"] == "server_metrics_update"
        assert message["data"]["server_id"] == 1
        assert message["data"]["hostname"] == "test-server"
        assert message["data"]["metrics"] == metrics
    
    async def test_broadcast_progress_update(self, broadcaster, mock_manager):
        """Test broadcasting progress updates."""
        await broadcaster.broadcast_progress_update(
            operation_id="op-123",
            operation_type="vm_creation",
            progress_percent=50,
            status="in_progress",
            message="Creating virtual machine..."
        )
        
        # Should broadcast to global room
        assert mock_manager.broadcast_to_room.call_count == 1
        
        room_call = mock_manager.broadcast_to_room.call_args
        assert room_call[0][0] == "global"
        message = room_call[0][1]
        assert message["type"] == "progress"
        assert message["data"]["operation_id"] == "op-123"
        assert message["data"]["operation_type"] == "vm_creation"
        assert message["data"]["progress_percent"] == 50
        assert message["data"]["status"] == "in_progress"
        assert message["data"]["message"] == "Creating virtual machine..."
    
    async def test_broadcast_alert(self, broadcaster, mock_manager):
        """Test broadcasting system alerts."""
        await broadcaster.broadcast_alert(
            alert_id="alert-456",
            alert_type="resource_warning",
            severity="warning",
            title="High CPU Usage",
            message="CPU usage is above 90%",
            entity_type="vm",
            entity_id=1
        )
        
        # Should broadcast to global room and VM-specific subscribers
        assert mock_manager.broadcast_to_room.call_count == 1
        assert mock_manager.broadcast_to_vm.call_count == 1
        
        # Check global broadcast
        room_call = mock_manager.broadcast_to_room.call_args
        assert room_call[0][0] == "global"
        message = room_call[0][1]
        assert message["type"] == "alert"
        assert message["data"]["alert_id"] == "alert-456"
        assert message["data"]["alert_type"] == "resource_warning"
        assert message["data"]["severity"] == "warning"
        assert message["data"]["title"] == "High CPU Usage"
        assert message["data"]["message"] == "CPU usage is above 90%"
        assert message["data"]["entity_type"] == "vm"
        assert message["data"]["entity_id"] == 1
        
        # Check VM-specific broadcast
        vm_call = mock_manager.broadcast_to_vm.call_args
        assert vm_call[0][0] == 1
        assert vm_call[0][1]["type"] == "alert"
    
    async def test_broadcast_alert_server_entity(self, broadcaster, mock_manager):
        """Test broadcasting alert for server entity."""
        await broadcaster.broadcast_alert(
            alert_id="alert-789",
            alert_type="connectivity",
            severity="error",
            title="Server Unreachable",
            message="Server is not responding",
            entity_type="server",
            entity_id=2
        )
        
        # Should broadcast to global room and server-specific subscribers
        assert mock_manager.broadcast_to_room.call_count == 1
        assert mock_manager.broadcast_to_server.call_count == 1
        assert mock_manager.broadcast_to_vm.call_count == 0
        
        # Check server-specific broadcast
        server_call = mock_manager.broadcast_to_server.call_args
        assert server_call[0][0] == 2
    
    async def test_broadcast_alert_no_entity(self, broadcaster, mock_manager):
        """Test broadcasting general system alert."""
        await broadcaster.broadcast_alert(
            alert_id="alert-general",
            alert_type="system",
            severity="info",
            title="System Update",
            message="System maintenance scheduled"
        )
        
        # Should only broadcast to global room
        assert mock_manager.broadcast_to_room.call_count == 1
        assert mock_manager.broadcast_to_vm.call_count == 0
        assert mock_manager.broadcast_to_server.call_count == 0
    
    def test_event_data_classes(self):
        """Test event data class functionality."""
        # Test VMStatusEvent
        vm_event = VMStatusEvent(
            vm_id=1,
            vm_name="test-vm",
            old_status="stopped",
            new_status="running",
            timestamp="2024-01-01T00:00:00Z"
        )
        
        vm_dict = vm_event.to_dict()
        assert vm_dict["vm_id"] == 1
        assert vm_dict["vm_name"] == "test-vm"
        assert vm_dict["old_status"] == "stopped"
        assert vm_dict["new_status"] == "running"
        assert vm_dict["timestamp"] == "2024-01-01T00:00:00Z"
        
        # Test ProgressEvent
        progress_event = ProgressEvent(
            operation_id="op-123",
            operation_type="vm_creation",
            progress_percent=75,
            status="in_progress",
            message="Almost done...",
            timestamp="2024-01-01T00:00:00Z"
        )
        
        progress_dict = progress_event.to_dict()
        assert progress_dict["operation_id"] == "op-123"
        assert progress_dict["progress_percent"] == 75
        assert progress_dict["message"] == "Almost done..."
        
        # Test AlertEvent
        alert_event = AlertEvent(
            alert_id="alert-123",
            alert_type="warning",
            severity="high",
            title="Test Alert",
            message="This is a test",
            entity_type="vm",
            entity_id=1,
            timestamp="2024-01-01T00:00:00Z"
        )
        
        alert_dict = alert_event.to_dict()
        assert alert_dict["alert_id"] == "alert-123"
        assert alert_dict["severity"] == "high"
        assert alert_dict["entity_type"] == "vm"
        assert alert_dict["entity_id"] == 1