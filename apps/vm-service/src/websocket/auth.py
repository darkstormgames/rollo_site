"""WebSocket authentication utilities."""

from typing import Optional
from fastapi import WebSocket, status
from sqlalchemy.orm import Session

from core.security import SecurityUtils, TokenData
from core.logging import get_logger
from models.base import DatabaseSession
from models.user import User

logger = get_logger("websocket_auth")


class WebSocketAuthError(Exception):
    """WebSocket authentication error."""
    pass


async def authenticate_websocket(websocket: WebSocket, token: Optional[str] = None) -> Optional[User]:
    """Authenticate WebSocket connection using token.
    
    Args:
        websocket: The WebSocket connection
        token: Optional JWT token for authentication
        
    Returns:
        User object if authenticated, None if anonymous access allowed
        
    Raises:
        WebSocketAuthError: If authentication fails
    """
    if token is None:
        # Allow anonymous connections for now
        logger.info("Anonymous WebSocket connection")
        return None
    
    try:
        # Verify the token
        token_data = SecurityUtils.verify_token(token, "access")
        if token_data is None:
            raise WebSocketAuthError("Invalid or expired token")
        
        # Get user from database
        db: Session = DatabaseSession.get_session()
        user = db.query(User).filter(
            User.id == token_data.user_id,
            User.is_active == True
        ).first()
        
        if user is None:
            raise WebSocketAuthError("User not found or inactive")
        
        logger.info(f"Authenticated WebSocket user: {user.username}")
        return user
        
    except Exception as e:
        logger.warning(f"WebSocket authentication failed: {e}")
        raise WebSocketAuthError(f"Authentication failed: {str(e)}")


async def get_websocket_user(websocket: WebSocket, token: Optional[str] = None) -> Optional[User]:
    """Get authenticated user for WebSocket connection with error handling.
    
    Args:
        websocket: The WebSocket connection
        token: Optional JWT token
        
    Returns:
        User object if authenticated, None otherwise
    """
    try:
        return await authenticate_websocket(websocket, token)
    except WebSocketAuthError as e:
        logger.info(f"WebSocket authentication failed, allowing anonymous: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during WebSocket auth: {e}")
        return None


def require_websocket_auth(func):
    """Decorator to require authentication for WebSocket endpoints."""
    async def wrapper(websocket: WebSocket, token: Optional[str] = None, *args, **kwargs):
        try:
            user = await authenticate_websocket(websocket, token)
            if user is None and token is not None:
                # If token was provided but authentication failed
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication required")
                return
            return await func(websocket, user, *args, **kwargs)
        except WebSocketAuthError:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication failed")
        except Exception as e:
            logger.error(f"Unexpected error in WebSocket auth decorator: {e}")
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Internal server error")
    
    return wrapper


async def check_websocket_permissions(user: Optional[User], action: str, resource_id: Optional[int] = None) -> bool:
    """Check if user has permissions for WebSocket actions.
    
    Args:
        user: The authenticated user (None for anonymous)
        action: The action being performed (e.g., "view_vm", "view_server")
        resource_id: Optional resource ID for resource-specific permissions
        
    Returns:
        True if permission granted, False otherwise
    """
    # For now, allow all authenticated users and anonymous users to view
    # In a production system, you would implement proper RBAC here
    
    if user is None:
        # Anonymous users can view public information
        return action in ["view_vm", "view_server", "view_metrics"]
    
    # Authenticated users can view everything
    # TODO: Implement proper role-based access control
    return True