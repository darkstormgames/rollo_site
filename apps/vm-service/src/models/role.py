"""Role model for RBAC implementation."""

from sqlalchemy import Column, Integer, String, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
from .user import user_roles


class Role(Base):
    """Role model for RBAC implementation."""
    
    __tablename__ = "roles"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Role information
    name = Column(String(50), unique=True, nullable=False, index=True)
    permissions = Column(JSON, nullable=False, default=lambda: {})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    users = relationship("User", secondary=user_roles, back_populates="roles")
    
    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}')>"
    
    def has_permission(self, permission: str) -> bool:
        """Check if role has a specific permission."""
        return self.permissions.get(permission, False) if self.permissions else False
    
    def add_permission(self, permission: str):
        """Add a permission to the role."""
        if self.permissions is None:
            self.permissions = {}
        self.permissions[permission] = True
    
    def remove_permission(self, permission: str):
        """Remove a permission from the role."""
        if self.permissions and permission in self.permissions:
            del self.permissions[permission]