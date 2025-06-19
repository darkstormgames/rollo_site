"""WebSocket endpoints for real-time VM monitoring."""

import json
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from sqlalchemy.orm import Session

from core.logging import get_logger
from models.base import DatabaseSession
from websocket.manager import websocket_manager
from websocket.auth import get_websocket_user, check_websocket_permissions
from websocket.events import event_broadcaster

logger = get_logger("websocket_endpoints")

router = APIRouter()


@router.websocket("/ws/monitor")
async def monitor_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    db: Session = Depends(DatabaseSession.get_session)
):
    """Main monitoring WebSocket endpoint for general VM and server updates.
    
    Supports:
    - Global system announcements
    - VM status changes
    - Server status changes  
    - Metrics updates
    - System alerts
    - Progress notifications
    """
    connection_id = None
    
    try:
        # Authenticate user
        user = await get_websocket_user(websocket, token)
        
        # Connect to WebSocket manager
        connection_id = await websocket_manager.connect(websocket, user)
        
        logger.info(f"Monitor connection established: {connection_id}")
        
        # Main message loop
        while True:
            try:
                # Receive message from client
                message_text = await websocket.receive_text()
                message = json.loads(message_text)
                
                # Handle the message
                await websocket_manager.handle_message(connection_id, message)
                
            except WebSocketDisconnect:
                logger.info(f"Monitor connection disconnected: {connection_id}")
                break
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received from {connection_id}")
                await websocket_manager.send_to_connection(connection_id, {
                    "type": "error",
                    "data": {
                        "message": "Invalid JSON format",
                        "timestamp": "timestamp"
                    }
                })
            except Exception as e:
                logger.error(f"Error in monitor endpoint for {connection_id}: {e}")
                await websocket_manager.send_to_connection(connection_id, {
                    "type": "error", 
                    "data": {
                        "message": "Internal server error",
                        "timestamp": "timestamp"
                    }
                })
                
    except Exception as e:
        logger.error(f"Monitor endpoint error: {e}")
        
    finally:
        if connection_id:
            websocket_manager.disconnect(connection_id)


@router.websocket("/ws/vm/{vm_id}")
async def vm_endpoint(
    websocket: WebSocket,
    vm_id: int,
    token: Optional[str] = Query(None),
    db: Session = Depends(DatabaseSession.get_session)
):
    """VM-specific WebSocket endpoint for detailed VM monitoring.
    
    Provides:
    - VM-specific status updates
    - VM metrics in real-time
    - VM operation progress
    - VM alerts and notifications
    """
    connection_id = None
    
    try:
        # Authenticate user
        user = await get_websocket_user(websocket, token)
        
        # Check permissions for this VM
        if not await check_websocket_permissions(user, "view_vm", vm_id):
            await websocket.close(code=4003, reason="Permission denied")
            return
        
        # Connect to WebSocket manager
        connection_id = await websocket_manager.connect(websocket, user)
        
        # Auto-subscribe to this VM
        websocket_manager.subscribe_to_vm(connection_id, vm_id)
        websocket_manager.subscribe_to_room(connection_id, "vm_status")
        websocket_manager.subscribe_to_room(connection_id, "vm_metrics")
        
        logger.info(f"VM {vm_id} connection established: {connection_id}")
        
        # Send initial VM data if available
        # TODO: Fetch and send current VM status and metrics
        
        # Main message loop
        while True:
            try:
                message_text = await websocket.receive_text()
                message = json.loads(message_text)
                
                # Handle VM-specific messages
                await websocket_manager.handle_message(connection_id, message)
                
            except WebSocketDisconnect:
                logger.info(f"VM {vm_id} connection disconnected: {connection_id}")
                break
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from VM {vm_id} connection {connection_id}")
            except Exception as e:
                logger.error(f"Error in VM {vm_id} endpoint for {connection_id}: {e}")
                
    except Exception as e:
        logger.error(f"VM {vm_id} endpoint error: {e}")
        
    finally:
        if connection_id:
            websocket_manager.disconnect(connection_id)


@router.websocket("/ws/console/{vm_id}")
async def console_endpoint(
    websocket: WebSocket,
    vm_id: int,
    token: Optional[str] = Query(None),
    db: Session = Depends(DatabaseSession.get_session)
):
    """VM console WebSocket endpoint for console streaming.
    
    Provides:
    - Real-time console output
    - Console input handling
    - Console session management
    """
    connection_id = None
    
    try:
        # Authenticate user
        user = await get_websocket_user(websocket, token)
        
        # Check permissions for console access
        if not await check_websocket_permissions(user, "console_vm", vm_id):
            await websocket.close(code=4003, reason="Console permission denied")
            return
        
        # Connect to WebSocket manager
        connection_id = await websocket_manager.connect(websocket, user)
        
        logger.info(f"Console {vm_id} connection established: {connection_id}")
        
        # TODO: Initialize console connection to VM
        # This would integrate with libvirt or other virtualization APIs
        
        # Send console connection status
        await websocket_manager.send_to_connection(connection_id, {
            "type": "console_status",
            "data": {
                "vm_id": vm_id,
                "status": "connected",
                "message": "Console session started"
            }
        })
        
        # Main console loop
        while True:
            try:
                message_text = await websocket.receive_text()
                message = json.loads(message_text)
                
                message_type = message.get("type")
                
                if message_type == "console_input":
                    # Handle console input
                    console_data = message.get("data", "")
                    logger.debug(f"Console input for VM {vm_id}: {console_data}")
                    
                    # TODO: Send input to VM console
                    # For now, echo back as a demo
                    await websocket_manager.send_to_connection(connection_id, {
                        "type": "console_output",
                        "data": {
                            "vm_id": vm_id,
                            "output": f"Echo: {console_data}"
                        }
                    })
                    
                elif message_type == "console_resize":
                    # Handle console resize
                    rows = message.get("data", {}).get("rows", 24)
                    cols = message.get("data", {}).get("cols", 80)
                    logger.debug(f"Console resize for VM {vm_id}: {cols}x{rows}")
                    
                    # TODO: Resize VM console
                    
                else:
                    await websocket_manager.handle_message(connection_id, message)
                
            except WebSocketDisconnect:
                logger.info(f"Console {vm_id} disconnected: {connection_id}")
                break
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from console {vm_id} connection {connection_id}")
            except Exception as e:
                logger.error(f"Error in console {vm_id} endpoint for {connection_id}: {e}")
                
    except Exception as e:
        logger.error(f"Console {vm_id} endpoint error: {e}")
        
    finally:
        if connection_id:
            websocket_manager.disconnect(connection_id)


@router.websocket("/ws/server/{server_id}")
async def server_endpoint(
    websocket: WebSocket,
    server_id: int,
    token: Optional[str] = Query(None),
    db: Session = Depends(DatabaseSession.get_session)
):
    """Server-specific WebSocket endpoint for detailed server monitoring.
    
    Provides:
    - Server-specific status updates
    - Server metrics in real-time
    - Server alerts and notifications
    - VMs hosted on this server
    """
    connection_id = None
    
    try:
        # Authenticate user
        user = await get_websocket_user(websocket, token)
        
        # Check permissions for this server
        if not await check_websocket_permissions(user, "view_server", server_id):
            await websocket.close(code=4003, reason="Permission denied")
            return
        
        # Connect to WebSocket manager
        connection_id = await websocket_manager.connect(websocket, user)
        
        # Auto-subscribe to this server
        websocket_manager.subscribe_to_server(connection_id, server_id)
        websocket_manager.subscribe_to_room(connection_id, "server_status")
        websocket_manager.subscribe_to_room(connection_id, "server_metrics")
        
        logger.info(f"Server {server_id} connection established: {connection_id}")
        
        # Main message loop
        while True:
            try:
                message_text = await websocket.receive_text()
                message = json.loads(message_text)
                
                await websocket_manager.handle_message(connection_id, message)
                
            except WebSocketDisconnect:
                logger.info(f"Server {server_id} connection disconnected: {connection_id}")
                break
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from server {server_id} connection {connection_id}")
            except Exception as e:
                logger.error(f"Error in server {server_id} endpoint for {connection_id}: {e}")
                
    except Exception as e:
        logger.error(f"Server {server_id} endpoint error: {e}")
        
    finally:
        if connection_id:
            websocket_manager.disconnect(connection_id)


# WebSocket stats endpoint for monitoring the WebSocket system itself
@router.websocket("/ws/stats")
async def stats_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """WebSocket statistics endpoint for system monitoring.
    
    Provides real-time statistics about:
    - Active connections
    - Room subscription counts
    - Message throughput
    - System health
    """
    connection_id = None
    
    try:
        # Authenticate user (admin only for stats)
        user = await get_websocket_user(websocket, token)
        
        # TODO: Check if user has admin permissions
        # For now, allow authenticated users
        if user is None:
            await websocket.close(code=4003, reason="Authentication required for stats")
            return
        
        connection_id = await websocket_manager.connect(websocket, user)
        
        logger.info(f"Stats connection established: {connection_id}")
        
        # Send periodic stats updates
        import asyncio
        
        while True:
            try:
                # Send current stats
                stats = {
                    "type": "websocket_stats",
                    "data": {
                        "active_connections": websocket_manager.get_connection_count(),
                        "room_stats": websocket_manager.get_room_stats(),
                        "timestamp": "timestamp"
                    }
                }
                
                await websocket_manager.send_to_connection(connection_id, stats)
                
                # Wait 5 seconds before next update
                await asyncio.sleep(5)
                
            except WebSocketDisconnect:
                logger.info(f"Stats connection disconnected: {connection_id}")
                break
            except Exception as e:
                logger.error(f"Error in stats endpoint for {connection_id}: {e}")
                break
                
    except Exception as e:
        logger.error(f"Stats endpoint error: {e}")
        
    finally:
        if connection_id:
            websocket_manager.disconnect(connection_id)