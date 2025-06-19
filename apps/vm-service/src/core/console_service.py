"""Console service for managing VM console connections and VNC proxy."""

import asyncio
import json
import secrets
import websockets
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from sqlalchemy.orm import Session

from core.logging import get_logger
from models.console_session import ConsoleSession
from models.base import DatabaseSession

logger = get_logger("console_service")

class ConsoleService:
    """Service for managing VM console sessions and VNC/SPICE proxy connections."""
    
    def __init__(self):
        self.active_connections: Dict[str, dict] = {}
        self.vnc_proxies: Dict[str, asyncio.Task] = {}
    
    async def create_console_session(self, vm_id: int, user_id: int, 
                                     protocol: str = "vnc", 
                                     expires_minutes: int = 15) -> Optional[ConsoleSession]:
        """Create a new console session for a VM."""
        try:
            # Generate secure session token
            session_token = secrets.token_urlsafe(32)
            
            # Check if user already has an active session for this VM
            db = DatabaseSession.get_session()
            existing_session = db.query(ConsoleSession).filter(
                ConsoleSession.vm_id == vm_id,
                ConsoleSession.user_id == user_id,
                ConsoleSession.is_active == True,
                ConsoleSession.expires_at > datetime.utcnow()
            ).first()
            
            # Terminate existing session if found
            if existing_session:
                existing_session.terminate()
                await self.cleanup_session(existing_session.session_token)
            
            # Create new session
            session = ConsoleSession.create_session(
                vm_id=vm_id,
                user_id=user_id,
                session_token=session_token,
                protocol=protocol,
                expires_minutes=expires_minutes
            )
            
            # Get VNC/SPICE port for the VM (this would integrate with libvirt)
            vnc_port = await self._get_vm_console_port(vm_id, protocol)
            if protocol == "vnc":
                session.vnc_port = vnc_port
            else:
                session.spice_port = vnc_port
            
            db.add(session)
            db.commit()
            db.refresh(session)
            
            logger.info(f"Created console session {session_token} for VM {vm_id}, user {user_id}")
            return session
            
        except Exception as e:
            logger.error(f"Failed to create console session for VM {vm_id}: {e}")
            return None
        finally:
            db.close()
    
    async def get_session_by_token(self, session_token: str) -> Optional[ConsoleSession]:
        """Get console session by token."""
        try:
            db = DatabaseSession.get_session()
            session = db.query(ConsoleSession).filter(
                ConsoleSession.session_token == session_token,
                ConsoleSession.is_active == True
            ).first()
            
            if session and session.is_expired():
                session.terminate()
                db.commit()
                await self.cleanup_session(session_token)
                return None
                
            return session
            
        except Exception as e:
            logger.error(f"Failed to get session by token {session_token}: {e}")
            return None
        finally:
            db.close()
    
    async def terminate_session(self, session_token: str) -> bool:
        """Terminate a console session."""
        try:
            db = DatabaseSession.get_session()
            session = db.query(ConsoleSession).filter(
                ConsoleSession.session_token == session_token
            ).first()
            
            if session:
                session.terminate()
                db.commit()
                await self.cleanup_session(session_token)
                logger.info(f"Terminated console session {session_token}")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Failed to terminate session {session_token}: {e}")
            return False
        finally:
            db.close()
    
    async def cleanup_session(self, session_token: str):
        """Clean up session resources."""
        try:
            # Remove from active connections
            if session_token in self.active_connections:
                del self.active_connections[session_token]
            
            # Stop VNC proxy if running
            if session_token in self.vnc_proxies:
                self.vnc_proxies[session_token].cancel()
                del self.vnc_proxies[session_token]
                
        except Exception as e:
            logger.error(f"Failed to cleanup session {session_token}: {e}")
    
    async def start_vnc_proxy(self, session_token: str, websocket) -> bool:
        """Start VNC proxy for a console session."""
        try:
            session = await self.get_session_by_token(session_token)
            if not session:
                return False
            
            # Get the appropriate port based on protocol
            if session.protocol == "vnc":
                target_port = session.vnc_port
            else:
                target_port = session.spice_port
                
            if not target_port:
                logger.error(f"No console port available for session {session_token}")
                return False
            
            # Store connection info
            self.active_connections[session_token] = {
                "websocket": websocket,
                "session": session,
                "target_port": target_port,
                "started_at": datetime.utcnow()
            }
            
            # Start the proxy task
            proxy_task = asyncio.create_task(
                self._proxy_vnc_data(session_token, websocket, target_port)
            )
            self.vnc_proxies[session_token] = proxy_task
            
            logger.info(f"Started VNC proxy for session {session_token} on port {target_port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start VNC proxy for session {session_token}: {e}")
            return False
    
    async def _proxy_vnc_data(self, session_token: str, client_ws, vnc_port: int):
        """Proxy data between WebSocket client and VNC server."""
        try:
            # Connect to VNC server (localhost for now - would be VM host in production)
            vnc_host = "localhost"
            vnc_uri = f"ws://{vnc_host}:{vnc_port}"
            
            logger.info(f"Connecting to VNC server at {vnc_uri} for session {session_token}")
            
            # For now, simulate VNC connection since we don't have actual VNC server
            await self._simulate_vnc_connection(client_ws, session_token)
            
            # In production, this would be:
            # async with websockets.connect(vnc_uri) as vnc_ws:
            #     await self._bidirectional_proxy(client_ws, vnc_ws, session_token)
            
        except Exception as e:
            logger.error(f"VNC proxy error for session {session_token}: {e}")
        finally:
            await self.cleanup_session(session_token)
    
    async def _simulate_vnc_connection(self, client_ws, session_token: str):
        """Simulate VNC connection for development."""
        try:
            # Send VNC protocol initialization
            await client_ws.send(json.dumps({
                "type": "vnc_init",
                "data": {
                    "width": 1024,
                    "height": 768,
                    "depth": 24,
                    "name": f"VM Console - Session {session_token[:8]}"
                }
            }))
            
            # Send initial frame (black screen)
            await client_ws.send(json.dumps({
                "type": "vnc_frame",
                "data": {
                    "x": 0,
                    "y": 0,
                    "width": 1024,
                    "height": 768,
                    "encoding": "raw",
                    "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
                }
            }))
            
            # Keep connection alive and handle messages
            async for message in client_ws:
                try:
                    data = json.loads(message)
                    await self._handle_vnc_message(client_ws, data, session_token)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from VNC client {session_token}")
                    
        except Exception as e:
            logger.error(f"Simulated VNC connection error for {session_token}: {e}")
    
    async def _handle_vnc_message(self, client_ws, data: dict, session_token: str):
        """Handle VNC protocol messages from client."""
        message_type = data.get("type")
        
        if message_type == "vnc_key":
            # Handle keyboard input
            key_data = data.get("data", {})
            logger.debug(f"VNC key event for {session_token}: {key_data}")
            
        elif message_type == "vnc_pointer":
            # Handle mouse input
            pointer_data = data.get("data", {})
            logger.debug(f"VNC pointer event for {session_token}: {pointer_data}")
            
        elif message_type == "vnc_resize":
            # Handle client resize
            resize_data = data.get("data", {})
            logger.debug(f"VNC resize event for {session_token}: {resize_data}")
            
            # Send resize response
            await client_ws.send(json.dumps({
                "type": "vnc_resize_response",
                "data": {
                    "width": resize_data.get("width", 1024),
                    "height": resize_data.get("height", 768)
                }
            }))
    
    async def _get_vm_console_port(self, vm_id: int, protocol: str) -> Optional[int]:
        """Get the console port for a VM (would integrate with libvirt)."""
        # In production, this would query libvirt to get the actual VNC/SPICE port
        # For now, return a simulated port based on VM ID
        if protocol == "vnc":
            return 5900 + vm_id  # Standard VNC port range
        else:
            return 5930 + vm_id  # SPICE port range
    
    async def cleanup_expired_sessions(self):
        """Clean up expired sessions (called periodically)."""
        try:
            db = DatabaseSession.get_session()
            expired_sessions = db.query(ConsoleSession).filter(
                ConsoleSession.is_active == True,
                ConsoleSession.expires_at < datetime.utcnow()
            ).all()
            
            for session in expired_sessions:
                session.terminate()
                await self.cleanup_session(session.session_token)
                logger.info(f"Cleaned up expired session {session.session_token}")
            
            if expired_sessions:
                db.commit()
                
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
        finally:
            db.close()

# Global console service instance
console_service = ConsoleService()