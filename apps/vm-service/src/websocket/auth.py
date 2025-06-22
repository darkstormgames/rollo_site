"""WebSocket authentication utilities."""

from typing import Optional
from fastapi import WebSocket, status
from sqlalchemy.orm import Session

from core.security import SecurityUtils, TokenData
from core.logging import get_logger
from models.base import DatabaseSession

logger = get_logger("websocket_auth")


class WebSocketAuthError(Exception):
    """WebSocket authentication error."""
    pass


async def authenticate_websocket(websocket: WebSocket, token: Optional[str] = None) -> Optional[dict]:
    """Authenticate WebSocket connection using token.
    
    Args:
        websocket: The WebSocket connection
        token: Optional JWT token for authentication
        
    Returns:
        User dict if authenticated, None if anonymous access allowed
        
    Raises:
        WebSocketAuthError: If authentication fails
    """
    if token is None:
        # Optionally allow anonymous access or close connection
        return None
    try:
        # Validate token and fetch user info from SSO
        user = await SecurityUtils.fetch_user_from_sso(token)
        if not user:
            raise WebSocketAuthError("Invalid or expired token")
        return user
    except Exception as e:
        logger.error(f"WebSocket authentication failed: {e}")
        raise WebSocketAuthError("Authentication failed")


async def get_websocket_user(websocket: WebSocket, token: Optional[str] = None) -> Optional[dict]:
    """Get user dict for WebSocket connection."""
    return await authenticate_websocket(websocket, token)


def require_websocket_auth(func):
    """Decorator to require WebSocket authentication."""
    async def wrapper(*args, **kwargs):
        user = kwargs.get("user")
        if not user:
            raise WebSocketAuthError("Authentication required")
        return await func(*args, **kwargs)
    return wrapper


async def check_websocket_permissions(user: Optional[dict], action: str, resource_id: Optional[int] = None) -> bool:
    """Check if user dict has permission for action."""
    if not user:
        return False
    permissions = user.get("permissions", [])
    return action in permissions