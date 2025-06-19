"""WebSocket connection manager for real-time VM monitoring."""

import json
import asyncio
from typing import Dict, List, Set, Optional, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from core.logging import get_logger
from models.user import User

logger = get_logger("websocket")


class ConnectionInfo:
    """Information about a WebSocket connection."""
    
    def __init__(self, websocket: WebSocket, user: Optional[User] = None):
        self.websocket = websocket
        self.user = user
        self.connected_at = datetime.utcnow()
        self.subscriptions: Set[str] = set()
        self.vm_subscriptions: Set[int] = set()
        self.server_subscriptions: Set[int] = set()


class WebSocketManager:
    """Manages WebSocket connections and message broadcasting."""
    
    def __init__(self):
        # Active connections
        self.connections: Dict[str, ConnectionInfo] = {}
        
        # Room-based subscriptions
        self.rooms: Dict[str, Set[str]] = {
            "global": set(),           # Global announcements
            "vm_status": set(),        # VM status changes
            "vm_metrics": set(),       # VM metrics updates
            "server_status": set(),    # Server status changes  
            "server_metrics": set(),   # Server metrics updates
        }
        
        # Entity-specific subscriptions
        self.vm_rooms: Dict[int, Set[str]] = {}      # VM ID -> connection IDs
        self.server_rooms: Dict[int, Set[str]] = {}  # Server ID -> connection IDs
        
        # Message queue for offline connections
        self.message_queue: Dict[str, List[Dict]] = {}
        
    def _generate_connection_id(self, websocket: WebSocket) -> str:
        """Generate a unique connection ID."""
        return f"conn_{id(websocket)}_{datetime.utcnow().timestamp()}"
    
    async def connect(self, websocket: WebSocket, user: Optional[User] = None) -> str:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        
        connection_id = self._generate_connection_id(websocket)
        connection_info = ConnectionInfo(websocket, user)
        
        self.connections[connection_id] = connection_info
        
        # Add to global room by default
        self.rooms["global"].add(connection_id)
        
        logger.info(f"WebSocket connected: {connection_id} (user: {user.username if user else 'anonymous'})")
        
        # Send welcome message
        await self.send_to_connection(connection_id, {
            "type": "connection_status",
            "data": {
                "status": "connected",
                "connection_id": connection_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
        # Send queued messages if any
        if connection_id in self.message_queue:
            for message in self.message_queue[connection_id]:
                await self.send_to_connection(connection_id, message)
            del self.message_queue[connection_id]
        
        return connection_id
    
    def disconnect(self, connection_id: str):
        """Disconnect a WebSocket connection."""
        if connection_id not in self.connections:
            return
        
        connection_info = self.connections[connection_id]
        
        # Remove from all rooms
        for room_connections in self.rooms.values():
            room_connections.discard(connection_id)
        
        # Remove from entity-specific rooms
        for vm_connections in self.vm_rooms.values():
            vm_connections.discard(connection_id)
        
        for server_connections in self.server_rooms.values():
            server_connections.discard(connection_id)
        
        # Remove connection
        del self.connections[connection_id]
        
        logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def send_to_connection(self, connection_id: str, message: Dict[str, Any]) -> bool:
        """Send a message to a specific connection."""
        if connection_id not in self.connections:
            return False
        
        connection_info = self.connections[connection_id]
        
        try:
            await connection_info.websocket.send_text(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Failed to send message to {connection_id}: {e}")
            self.disconnect(connection_id)
            return False
    
    async def broadcast_to_room(self, room: str, message: Dict[str, Any], exclude: Optional[Set[str]] = None):
        """Broadcast a message to all connections in a room."""
        if room not in self.rooms:
            logger.warning(f"Room {room} does not exist")
            return
        
        exclude = exclude or set()
        connection_ids = self.rooms[room] - exclude
        
        if not connection_ids:
            return
        
        logger.debug(f"Broadcasting to room {room}: {len(connection_ids)} connections")
        
        # Send to all connections concurrently
        tasks = [
            self.send_to_connection(conn_id, message)
            for conn_id in connection_ids
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast_to_vm(self, vm_id: int, message: Dict[str, Any], exclude: Optional[Set[str]] = None):
        """Broadcast a message to all connections subscribed to a specific VM."""
        if vm_id not in self.vm_rooms:
            return
        
        exclude = exclude or set()
        connection_ids = self.vm_rooms[vm_id] - exclude
        
        if not connection_ids:
            return
        
        logger.debug(f"Broadcasting to VM {vm_id}: {len(connection_ids)} connections")
        
        tasks = [
            self.send_to_connection(conn_id, message)
            for conn_id in connection_ids
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast_to_server(self, server_id: int, message: Dict[str, Any], exclude: Optional[Set[str]] = None):
        """Broadcast a message to all connections subscribed to a specific server."""
        if server_id not in self.server_rooms:
            return
        
        exclude = exclude or set()
        connection_ids = self.server_rooms[server_id] - exclude
        
        if not connection_ids:
            return
        
        logger.debug(f"Broadcasting to server {server_id}: {len(connection_ids)} connections")
        
        tasks = [
            self.send_to_connection(conn_id, message)
            for conn_id in connection_ids
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    def subscribe_to_room(self, connection_id: str, room: str):
        """Subscribe a connection to a room."""
        if connection_id not in self.connections:
            return False
        
        if room not in self.rooms:
            self.rooms[room] = set()
        
        self.rooms[room].add(connection_id)
        self.connections[connection_id].subscriptions.add(room)
        
        logger.debug(f"Connection {connection_id} subscribed to room {room}")
        return True
    
    def unsubscribe_from_room(self, connection_id: str, room: str):
        """Unsubscribe a connection from a room."""
        if connection_id not in self.connections:
            return False
        
        if room in self.rooms:
            self.rooms[room].discard(connection_id)
        
        self.connections[connection_id].subscriptions.discard(room)
        
        logger.debug(f"Connection {connection_id} unsubscribed from room {room}")
        return True
    
    def subscribe_to_vm(self, connection_id: str, vm_id: int):
        """Subscribe a connection to VM-specific updates."""
        if connection_id not in self.connections:
            return False
        
        if vm_id not in self.vm_rooms:
            self.vm_rooms[vm_id] = set()
        
        self.vm_rooms[vm_id].add(connection_id)
        self.connections[connection_id].vm_subscriptions.add(vm_id)
        
        logger.debug(f"Connection {connection_id} subscribed to VM {vm_id}")
        return True
    
    def unsubscribe_from_vm(self, connection_id: str, vm_id: int):
        """Unsubscribe a connection from VM-specific updates."""
        if connection_id not in self.connections:
            return False
        
        if vm_id in self.vm_rooms:
            self.vm_rooms[vm_id].discard(connection_id)
        
        self.connections[connection_id].vm_subscriptions.discard(vm_id)
        
        logger.debug(f"Connection {connection_id} unsubscribed from VM {vm_id}")
        return True
    
    def subscribe_to_server(self, connection_id: str, server_id: int):
        """Subscribe a connection to server-specific updates."""
        if connection_id not in self.connections:
            return False
        
        if server_id not in self.server_rooms:
            self.server_rooms[server_id] = set()
        
        self.server_rooms[server_id].add(connection_id)
        self.connections[connection_id].server_subscriptions.add(server_id)
        
        logger.debug(f"Connection {connection_id} subscribed to server {server_id}")
        return True
    
    def unsubscribe_from_server(self, connection_id: str, server_id: int):
        """Unsubscribe a connection from server-specific updates."""
        if connection_id not in self.connections:
            return False
        
        if server_id in self.server_rooms:
            self.server_rooms[server_id].discard(connection_id)
        
        self.connections[connection_id].server_subscriptions.discard(server_id)
        
        logger.debug(f"Connection {connection_id} unsubscribed from server {server_id}")
        return True
    
    async def handle_message(self, connection_id: str, message: Dict[str, Any]):
        """Handle incoming WebSocket message from client."""
        message_type = message.get("type")
        data = message.get("data", {})
        
        if message_type == "subscribe":
            await self._handle_subscribe(connection_id, data)
        elif message_type == "unsubscribe":
            await self._handle_unsubscribe(connection_id, data)
        elif message_type == "ping":
            await self._handle_ping(connection_id)
        else:
            logger.warning(f"Unknown message type: {message_type}")
    
    async def _handle_subscribe(self, connection_id: str, data: Dict[str, Any]):
        """Handle subscription requests."""
        events = data.get("events", [])
        vm_ids = data.get("vm_ids", [])
        server_ids = data.get("server_ids", [])
        
        # Subscribe to event types
        for event in events:
            room_map = {
                "vm_status_changed": "vm_status",
                "vm_created": "vm_status", 
                "vm_deleted": "vm_status",
                "vm_metrics_update": "vm_metrics",
                "server_status_changed": "server_status",
                "server_registered": "server_status",
                "server_removed": "server_status", 
                "server_metrics_update": "server_metrics"
            }
            
            if event in room_map:
                self.subscribe_to_room(connection_id, room_map[event])
        
        # Subscribe to specific VMs
        for vm_id in vm_ids:
            self.subscribe_to_vm(connection_id, vm_id)
        
        # Subscribe to specific servers  
        for server_id in server_ids:
            self.subscribe_to_server(connection_id, server_id)
        
        # Send confirmation
        await self.send_to_connection(connection_id, {
            "type": "subscription_confirmed",
            "data": {
                "events": events,
                "vm_ids": vm_ids,
                "server_ids": server_ids,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
    
    async def _handle_unsubscribe(self, connection_id: str, data: Dict[str, Any]):
        """Handle unsubscription requests."""
        events = data.get("events", [])
        vm_ids = data.get("vm_ids", [])
        server_ids = data.get("server_ids", [])
        
        # Unsubscribe from event types
        for event in events:
            room_map = {
                "vm_status_changed": "vm_status",
                "vm_created": "vm_status",
                "vm_deleted": "vm_status", 
                "vm_metrics_update": "vm_metrics",
                "server_status_changed": "server_status",
                "server_registered": "server_status",
                "server_removed": "server_status",
                "server_metrics_update": "server_metrics"
            }
            
            if event in room_map:
                self.unsubscribe_from_room(connection_id, room_map[event])
        
        # Unsubscribe from specific VMs
        for vm_id in vm_ids:
            self.unsubscribe_from_vm(connection_id, vm_id)
        
        # Unsubscribe from specific servers
        for server_id in server_ids:
            self.unsubscribe_from_server(connection_id, server_id)
    
    async def _handle_ping(self, connection_id: str):
        """Handle ping/heartbeat messages."""
        await self.send_to_connection(connection_id, {
            "type": "pong",
            "data": {
                "timestamp": datetime.utcnow().isoformat()
            }
        })
    
    def get_connection_count(self) -> int:
        """Get the total number of active connections."""
        return len(self.connections)
    
    def get_room_stats(self) -> Dict[str, int]:
        """Get statistics about room subscriptions."""
        return {
            room: len(connections)
            for room, connections in self.rooms.items()
        }


# Global WebSocket manager instance
websocket_manager = WebSocketManager()