"""Authentication and authorization middleware for FastAPI."""

from typing import Optional, List
from functools import wraps

from fastapi import HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx

from core.logging import get_logger

logger = get_logger("auth")
security = HTTPBearer()

SSO_BASE_URL = "http://127.0.0.1:3000/api/auth"


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


async def fetch_user_from_sso(token: str) -> dict:
    """Fetch user info from SSO using the access token."""
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        try:
            print(f"{headers}")
            resp = await client.get(f"{SSO_BASE_URL}/me", headers=headers)
            resp.raise_for_status()
            data = resp.json()
            # The user info is in the 'user' property
            user = data.get("user")
            if not user:
                raise AuthenticationError("User info missing in SSO response")
            # Optionally map access_level to accessLevel for consistency
            if "access_level" in user:
                user["accessLevel"] = user["access_level"]
                # Map access_level to permissions
                level = user["access_level"]
                if level == "admin":
                    user["permissions"] = ["read", "write", "delete", "admin"]
                elif level == "premium":
                    user["permissions"] = ["read", "write"]
                elif level == "standard":
                    user["permissions"] = ["read"]
                else:
                    user["permissions"] = []
            return user
        except httpx.HTTPStatusError as e:
            logger.warning(f"SSO user fetch failed: {e.response.text}")
            raise AuthenticationError("Invalid or expired token")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Get current authenticated user from SSO."""
    token = credentials.credentials
    user = await fetch_user_from_sso(token)
    if not user or not user.get("id") or not user.get("username"):
        logger.warning("User not found or inactive in SSO")
        raise AuthenticationError("User not found or inactive")
    return user


async def get_current_active_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Get current active user."""
    if not current_user.get("is_active", True):
        raise AuthenticationError("Inactive user")
    return current_user


def require_roles(roles: List[str]):
    """Decorator to require specific roles."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not current_user:
                raise AuthenticationError("Authentication required")
            user_roles = set()
            # SSO returns 'accessLevel' or 'roles'
            if "roles" in current_user:
                user_roles = set(current_user["roles"])
            elif "accessLevel" in current_user:
                user_roles = {current_user["accessLevel"]}
            missing_roles = set(roles) - user_roles
            if missing_roles:
                logger.warning(
                    f"User {current_user.get('username')} missing roles: {missing_roles}"
                )
                raise AuthorizationError(
                    f"Missing required roles: {', '.join(missing_roles)}"
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# If you want to support permissions, adapt this function to your SSO user schema
def require_permissions(permissions: List[str]):
    """Decorator to require specific permissions."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not current_user:
                raise AuthenticationError("Authentication required")
            user_permissions = set(current_user.get("permissions", []))
            missing_permissions = set(permissions) - user_permissions
            if missing_permissions:
                logger.warning(
                    f"User {current_user.get('username')} missing permissions: {missing_permissions}"
                )
                raise AuthorizationError(
                    f"Missing required permissions: {', '.join(missing_permissions)}"
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
) -> Optional[dict]:
    """Get optional user for endpoints that work with or without authentication."""
    if credentials is None:
        return None
    try:
        return await fetch_user_from_sso(credentials.credentials)
    except Exception:
        return None