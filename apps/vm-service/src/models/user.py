"""User model for authentication and authorization."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Table, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

# Association table for many-to-many relationship between users and roles
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)


class User(Base):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic user information
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # User status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    servers = relationship("Server", back_populates="owner")
    created_vms = relationship("VirtualMachine", back_populates="created_by_user")
    created_templates = relationship("VMTemplate", back_populates="created_by_user")
    created_images = relationship("OSImage", back_populates="created_by_user")
    audit_logs = relationship("AuditLog", back_populates="user")
    refresh_tokens = relationship("RefreshToken", back_populates="user")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission through their roles."""
        for role in self.roles:
            if role.has_permission(permission):
                return True
        return False
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role."""
        return any(role.name == role_name for role in self.roles)
    
    def get_permissions(self) -> set[str]:
        """Get all permissions for the user."""
        permissions = set()
        for role in self.roles:
            if role.permissions:
                for permission, granted in role.permissions.items():
                    if granted:
                        permissions.add(permission)
        return permissions