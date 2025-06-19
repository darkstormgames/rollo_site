"""Authentication and authorization middleware for FastAPI."""

from typing import Optional, List
from functools import wraps

from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from models.base import DatabaseSession
from models.user import User
from models.role import Role
from core.security import SecurityUtils, TokenData
from core.logging import get_logger

logger = get_logger("auth")
security = HTTPBearer()


class AuthenticationError(HTTPException):
    """Custom authentication error."""
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationError(HTTPException):
    """Custom authorization error."""
    def __init__(self, detail: str = "Not enough permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(DatabaseSession.get_session)
) -> User:
    """Get current authenticated user."""
    token = credentials.credentials
    token_data = SecurityUtils.verify_token(token, "access")
    
    if token_data is None:
        logger.warning(f"Invalid token provided")
        raise AuthenticationError("Invalid or expired token")
    
    # Get user from database
    user = db.query(User).filter(
        User.id == token_data.user_id,
        User.is_active == True
    ).first()
    
    if user is None:
        logger.warning(f"User {token_data.user_id} not found or inactive")
        raise AuthenticationError("User not found or inactive")
    
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise AuthenticationError("Inactive user")
    return current_user


def require_permissions(permissions: List[str]):
    """Decorator to require specific permissions."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user from kwargs (injected by FastAPI)
            current_user = None
            for key, value in kwargs.items():
                if isinstance(value, User):
                    current_user = value
                    break
            
            if current_user is None:
                raise AuthenticationError("Authentication required")
            
            # Check if user has required permissions
            user_permissions = set()
            for role in current_user.roles:
                if role.permissions:
                    for permission, granted in role.permissions.items():
                        if granted:
                            user_permissions.add(permission)
            
            missing_permissions = set(permissions) - user_permissions
            if missing_permissions:
                logger.warning(
                    f"User {current_user.username} missing permissions: {missing_permissions}"
                )
                raise AuthorizationError(
                    f"Missing required permissions: {', '.join(missing_permissions)}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_roles(roles: List[str]):
    """Decorator to require specific roles."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user from kwargs (injected by FastAPI)
            current_user = None
            for key, value in kwargs.items():
                if isinstance(value, User):
                    current_user = value
                    break
            
            if current_user is None:
                raise AuthenticationError("Authentication required")
            
            # Check if user has required roles
            user_roles = {role.name for role in current_user.roles}
            missing_roles = set(roles) - user_roles
            
            if missing_roles:
                logger.warning(
                    f"User {current_user.username} missing roles: {missing_roles}"
                )
                raise AuthorizationError(
                    f"Missing required roles: {', '.join(missing_roles)}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(DatabaseSession.get_session)
) -> Optional[User]:
    """Get optional user for endpoints that work with or without authentication."""
    if credentials is None:
        return None
    
    try:
        token_data = SecurityUtils.verify_token(credentials.credentials, "access")
        if token_data is None:
            return None
        
        user = db.query(User).filter(
            User.id == token_data.user_id,
            User.is_active == True
        ).first()
        
        return user
    except Exception:
        return None