"""Tests for WebSocket manager functionality."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from websocket.manager import WebSocketManager, ConnectionInfo
from models.user import User


@pytest.fixture
def manager():
    """Create a WebSocketManager instance for testing."""
    return WebSocketManager()


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket for testing."""
    websocket = Mock()
    websocket.accept = AsyncMock()
    websocket.send_text = AsyncMock()
    websocket.close = AsyncMock()
    return websocket


@pytest.fixture
def mock_user():
    """Create a mock User for testing."""
    user = Mock(spec=User)
    user.id = 1
    user.username = "testuser"
    return user


class TestWebSocketManager:
    """Test WebSocket manager functionality."""
    
    async def test_connect_anonymous(self, manager, mock_websocket):
        """Test connecting an anonymous user."""
        connection_id = await manager.connect(mock_websocket)
        
        assert connection_id is not None
        assert connection_id in manager.connections
        assert manager.connections[connection_id].user is None
        assert connection_id in manager.rooms["global"]
        
        mock_websocket.accept.assert_called_once()
        mock_websocket.send_text.assert_called_once()
    
    async def test_connect_authenticated(self, manager, mock_websocket, mock_user):
        """Test connecting an authenticated user."""
        connection_id = await manager.connect(mock_websocket, mock_user)
        
        assert connection_id is not None
        assert connection_id in manager.connections
        assert manager.connections[connection_id].user == mock_user
        assert connection_id in manager.rooms["global"]
        
        mock_websocket.accept.assert_called_once()
    
    def test_disconnect(self, manager, mock_websocket):
        """Test disconnecting a user."""
        # First connect
        loop = asyncio.get_event_loop()
        connection_id = loop.run_until_complete(manager.connect(mock_websocket))
        
        # Subscribe to some rooms
        manager.subscribe_to_room(connection_id, "vm_status")
        manager.subscribe_to_vm(connection_id, 1)
        
        # Then disconnect
        manager.disconnect(connection_id)
        
        assert connection_id not in manager.connections
        assert connection_id not in manager.rooms["global"]
        assert connection_id not in manager.rooms["vm_status"]
        if 1 in manager.vm_rooms:
            assert connection_id not in manager.vm_rooms[1]
    
    async def test_send_to_connection(self, manager, mock_websocket):
        """Test sending message to specific connection."""
        connection_id = await manager.connect(mock_websocket)
        
        message = {"type": "test", "data": {"test": True}}
        result = await manager.send_to_connection(connection_id, message)
        
        assert result is True
        mock_websocket.send_text.assert_called()
        # Verify the message was JSON serialized
        call_args = mock_websocket.send_text.call_args[0][0]
        assert '"type": "test"' in call_args
    
    async def test_send_to_nonexistent_connection(self, manager):
        """Test sending message to non-existent connection."""
        message = {"type": "test", "data": {}}
        result = await manager.send_to_connection("invalid", message)
        
        assert result is False
    
    async def test_broadcast_to_room(self, manager, mock_websocket):
        """Test broadcasting to a room."""
        # Connect two clients
        connection_id1 = await manager.connect(mock_websocket)
        
        mock_websocket2 = Mock()
        mock_websocket2.accept = AsyncMock()
        mock_websocket2.send_text = AsyncMock()
        connection_id2 = await manager.connect(mock_websocket2)
        
        # Subscribe both to vm_status
        manager.subscribe_to_room(connection_id1, "vm_status")
        manager.subscribe_to_room(connection_id2, "vm_status")
        
        message = {"type": "vm_status", "data": {"vm_id": 1, "status": "running"}}
        await manager.broadcast_to_room("vm_status", message)
        
        # Both should have received the message
        assert mock_websocket.send_text.call_count >= 1
        assert mock_websocket2.send_text.call_count >= 1
    
    async def test_broadcast_to_vm(self, manager, mock_websocket):
        """Test broadcasting to VM-specific subscribers."""
        connection_id = await manager.connect(mock_websocket)
        manager.subscribe_to_vm(connection_id, 1)
        
        message = {"type": "vm_metrics", "data": {"vm_id": 1, "metrics": {}}}
        await manager.broadcast_to_vm(1, message)
        
        # Should have received the message
        assert mock_websocket.send_text.call_count >= 1
    
    async def test_broadcast_to_server(self, manager, mock_websocket):
        """Test broadcasting to server-specific subscribers."""
        connection_id = await manager.connect(mock_websocket)
        manager.subscribe_to_server(connection_id, 1)
        
        message = {"type": "server_metrics", "data": {"server_id": 1, "metrics": {}}}
        await manager.broadcast_to_server(1, message)
        
        # Should have received the message
        assert mock_websocket.send_text.call_count >= 1
    
    def test_subscribe_to_room(self, manager, mock_websocket):
        """Test subscribing to a room."""
        loop = asyncio.get_event_loop()
        connection_id = loop.run_until_complete(manager.connect(mock_websocket))
        
        result = manager.subscribe_to_room(connection_id, "test_room")
        
        assert result is True
        assert connection_id in manager.rooms["test_room"]
        assert "test_room" in manager.connections[connection_id].subscriptions
    
    def test_subscribe_to_vm(self, manager, mock_websocket):
        """Test subscribing to VM-specific updates."""
        loop = asyncio.get_event_loop()
        connection_id = loop.run_until_complete(manager.connect(mock_websocket))
        
        result = manager.subscribe_to_vm(connection_id, 1)
        
        assert result is True
        assert connection_id in manager.vm_rooms[1]
        assert 1 in manager.connections[connection_id].vm_subscriptions
    
    def test_subscribe_to_server(self, manager, mock_websocket):
        """Test subscribing to server-specific updates."""
        loop = asyncio.get_event_loop()
        connection_id = loop.run_until_complete(manager.connect(mock_websocket))
        
        result = manager.subscribe_to_server(connection_id, 1)
        
        assert result is True
        assert connection_id in manager.server_rooms[1]
        assert 1 in manager.connections[connection_id].server_subscriptions
    
    async def test_handle_subscribe_message(self, manager, mock_websocket):
        """Test handling subscription messages."""
        connection_id = await manager.connect(mock_websocket)
        
        message = {
            "type": "subscribe",
            "data": {
                "events": ["vm_status_changed", "vm_metrics_update"],
                "vm_ids": [1, 2],
                "server_ids": [1]
            }
        }
        
        await manager.handle_message(connection_id, message)
        
        # Should be subscribed to appropriate rooms
        assert connection_id in manager.rooms["vm_status"]
        assert connection_id in manager.rooms["vm_metrics"]
        assert connection_id in manager.vm_rooms[1]
        assert connection_id in manager.vm_rooms[2]
        assert connection_id in manager.server_rooms[1]
    
    async def test_handle_ping_message(self, manager, mock_websocket):
        """Test handling ping messages."""
        connection_id = await manager.connect(mock_websocket)
        
        message = {"type": "ping"}
        await manager.handle_message(connection_id, message)
        
        # Should have sent a pong response
        assert mock_websocket.send_text.call_count >= 2  # connect message + pong
    
    def test_get_connection_count(self, manager, mock_websocket):
        """Test getting connection count."""
        assert manager.get_connection_count() == 0
        
        loop = asyncio.get_event_loop()
        connection_id = loop.run_until_complete(manager.connect(mock_websocket))
        
        assert manager.get_connection_count() == 1
        
        manager.disconnect(connection_id)
        assert manager.get_connection_count() == 0
    
    def test_get_room_stats(self, manager, mock_websocket):
        """Test getting room statistics."""
        loop = asyncio.get_event_loop()
        connection_id = loop.run_until_complete(manager.connect(mock_websocket))
        
        manager.subscribe_to_room(connection_id, "vm_status")
        manager.subscribe_to_room(connection_id, "vm_metrics")
        
        stats = manager.get_room_stats()
        
        assert stats["global"] == 1
        assert stats["vm_status"] == 1
        assert stats["vm_metrics"] == 1