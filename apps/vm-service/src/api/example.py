"""Example router demonstrating authorization decorators."""

from fastapi import APIRouter, Depends

from core.auth import get_current_active_user, require_permissions, require_roles
from models.user import User

router = APIRouter()


@router.get("/public")
async def public_endpoint():
    """Public endpoint that doesn't require authentication."""
    return {"message": "This is a public endpoint"}


@router.get("/protected")
async def protected_endpoint(current_user: User = Depends(get_current_active_user)):
    """Protected endpoint requiring authentication."""
    return {
        "message": f"Hello {current_user.username}!",
        "user_id": current_user.id,
        "roles": [role.name for role in current_user.roles]
    }


@router.get("/read-access")
@require_permissions(["read"])
async def read_access_endpoint(current_user: User = Depends(get_current_active_user)):
    """Endpoint requiring read permission."""
    return {
        "message": "You have read access",
        "user": current_user.username,
        "permissions": list(current_user.get_permissions())
    }


@router.get("/write-access")
@require_permissions(["write"])
async def write_access_endpoint(current_user: User = Depends(get_current_active_user)):
    """Endpoint requiring write permission."""
    return {
        "message": "You have write access",
        "user": current_user.username
    }


@router.get("/admin-access")
@require_permissions(["admin"])
async def admin_access_endpoint(current_user: User = Depends(get_current_active_user)):
    """Endpoint requiring admin permission."""
    return {
        "message": "You have admin access",
        "user": current_user.username
    }


@router.get("/admin-role")
@require_roles(["admin"])
async def admin_role_endpoint(current_user: User = Depends(get_current_active_user)):
    """Endpoint requiring admin role."""
    return {
        "message": "You have admin role",
        "user": current_user.username,
        "roles": [role.name for role in current_user.roles]
    }


@router.get("/multiple-permissions")
@require_permissions(["read", "write"])
async def multiple_permissions_endpoint(current_user: User = Depends(get_current_active_user)):
    """Endpoint requiring multiple permissions."""
    return {
        "message": "You have both read and write permissions",
        "user": current_user.username,
        "permissions": list(current_user.get_permissions())
    }