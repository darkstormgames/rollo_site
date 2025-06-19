"""Test User model methods."""

import pytest
from sqlalchemy.orm import Session

from models.user import User
from models.role import Role


def test_user_has_permission(db_session: Session):
    """Test user permission checking."""
    # Create roles
    admin_role = Role(name="admin", permissions={"read": True, "write": True, "delete": True})
    user_role = Role(name="user", permissions={"read": True})
    
    # Create user with roles
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password"
    )
    user.roles = [admin_role, user_role]
    
    db_session.add_all([admin_role, user_role, user])
    db_session.commit()
    
    # Test permissions
    assert user.has_permission("read") is True
    assert user.has_permission("write") is True
    assert user.has_permission("delete") is True
    assert user.has_permission("super_admin") is False


def test_user_has_role(db_session: Session):
    """Test user role checking."""
    # Create roles
    admin_role = Role(name="admin", permissions={"read": True})
    user_role = Role(name="user", permissions={"read": True})
    
    # Create user with roles
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password"
    )
    user.roles = [user_role]
    
    db_session.add_all([admin_role, user_role, user])
    db_session.commit()
    
    # Test roles
    assert user.has_role("user") is True
    assert user.has_role("admin") is False


def test_user_get_permissions(db_session: Session):
    """Test getting all user permissions."""
    # Create roles
    admin_role = Role(name="admin", permissions={"write": True, "delete": True})
    user_role = Role(name="user", permissions={"read": True, "write": False})
    
    # Create user with roles
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password"
    )
    user.roles = [admin_role, user_role]
    
    db_session.add_all([admin_role, user_role, user])
    db_session.commit()
    
    # Test permissions
    permissions = user.get_permissions()
    assert permissions == {"read", "write", "delete"}


def test_user_no_permissions(db_session: Session):
    """Test user with no roles/permissions."""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password"
    )
    
    db_session.add(user)
    db_session.commit()
    
    # Test permissions
    assert user.has_permission("read") is False
    assert user.has_role("user") is False
    assert user.get_permissions() == set()


def test_role_permission_methods(db_session: Session):
    """Test role permission management methods."""
    role = Role(name="test_role", permissions={})
    
    # Test adding permissions
    role.add_permission("read")
    assert role.has_permission("read") is True
    assert role.permissions["read"] is True
    
    # Test removing permissions
    role.remove_permission("read")
    assert role.has_permission("read") is False
    assert "read" not in role.permissions
    
    # Test removing non-existent permission
    role.remove_permission("nonexistent")  # Should not raise error