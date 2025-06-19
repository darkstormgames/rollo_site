"""Pydantic schemas for console API endpoints."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class ConsoleSessionRequest(BaseModel):
    """Request model for creating a console session."""
    
    user_id: Optional[int] = Field(None, description="User ID (will be extracted from JWT)")
    protocol: str = Field("vnc", description="Console protocol (vnc or spice)")
    expires_minutes: Optional[int] = Field(15, description="Session expiration in minutes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "protocol": "vnc",
                "expires_minutes": 15
            }
        }

class ConsoleSessionResponse(BaseModel):
    """Response model for console session creation."""
    
    session_token: str = Field(..., description="Unique session token for WebSocket connection")
    vm_id: int = Field(..., description="VM ID")
    protocol: str = Field(..., description="Console protocol (vnc or spice)")
    websocket_url: str = Field(..., description="WebSocket URL for console connection")
    expires_at: datetime = Field(..., description="Session expiration timestamp")
    vnc_port: Optional[int] = Field(None, description="VNC port if protocol is vnc")
    spice_port: Optional[int] = Field(None, description="SPICE port if protocol is spice")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_token": "abc123def456ghi789...",
                "vm_id": 1,
                "protocol": "vnc",
                "websocket_url": "ws://localhost:8000/ws/console/abc123def456ghi789...",
                "expires_at": "2024-01-15T10:30:00Z",
                "vnc_port": 5901,
                "spice_port": None
            }
        }

class ConsoleStatusResponse(BaseModel):
    """Response model for console status check."""
    
    vm_id: int = Field(..., description="VM ID")
    available: bool = Field(..., description="Whether console access is available")
    has_active_session: bool = Field(..., description="Whether user has an active session")
    session_token: Optional[str] = Field(None, description="Active session token if exists")
    expires_at: Optional[datetime] = Field(None, description="Session expiration if active")
    protocol: Optional[str] = Field(None, description="Active session protocol")
    
    class Config:
        json_schema_extra = {
            "example": {
                "vm_id": 1,
                "available": True,
                "has_active_session": True,
                "session_token": "abc123def456ghi789...",
                "expires_at": "2024-01-15T10:30:00Z",
                "protocol": "vnc"
            }
        }

class ConsoleConnectionInfo(BaseModel):
    """Model for WebSocket console connection information."""
    
    type: str = Field(..., description="Message type")
    session_token: str = Field(..., description="Session token")
    vm_id: int = Field(..., description="VM ID")
    protocol: str = Field(..., description="Console protocol")
    status: str = Field(..., description="Connection status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "console_connected",
                "session_token": "abc123def456ghi789...",
                "vm_id": 1,
                "protocol": "vnc",
                "status": "connected"
            }
        }

class VNCMessage(BaseModel):
    """Model for VNC protocol messages."""
    
    type: str = Field(..., description="VNC message type")
    data: dict = Field(..., description="VNC message data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "vnc_key",
                "data": {
                    "key": 65,
                    "down": True
                }
            }
        }