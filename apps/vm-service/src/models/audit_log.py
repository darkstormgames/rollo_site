"""AuditLog model for tracking all actions."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class AuditLog(Base):
    """AuditLog model for tracking all actions."""
    
    __tablename__ = "audit_logs"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # User who performed the action
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for system actions
    
    # Action details
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False, index=True)  # e.g., 'vm', 'server', 'user'
    resource_id = Column(Integer, nullable=True)  # ID of the affected resource
    
    # Additional details
    description = Column(Text, nullable=True)
    extra_data = Column(JSON, nullable=True)  # Additional structured data (renamed from metadata)
    
    # Context information
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(String(500), nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', resource_type='{self.resource_type}', user_id={self.user_id})>"
    
    @classmethod
    def log_action(cls, action: str, resource_type: str, user_id: int = None, 
                   resource_id: int = None, description: str = None, 
                   extra_data: dict = None, ip_address: str = None, 
                   user_agent: str = None):
        """Create a new audit log entry."""
        return cls(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            extra_data=extra_data,
            ip_address=ip_address,
            user_agent=user_agent
        )