"""VMTemplate model for predefined VM configurations."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
from .virtual_machine import OSType


class VMTemplate(Base):
    """VMTemplate model for predefined VM configurations."""
    
    __tablename__ = "vm_templates"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Template information
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Operating system
    os_type = Column(String(50), nullable=False, default="linux")  # Using String instead of Enum for flexibility
    os_version = Column(String(100), nullable=True)
    
    # Hardware specifications
    cpu_cores = Column(Integer, nullable=False, default=1)
    memory_mb = Column(Integer, nullable=False, default=1024)
    disk_gb = Column(Float, nullable=False, default=20.0)
    
    # Base image
    base_image_path = Column(String(500), nullable=False)
    
    # Ownership and timestamps
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    created_by_user = relationship("User", back_populates="created_templates")
    
    def __repr__(self):
        return f"<VMTemplate(id={self.id}, name='{self.name}', os_type='{self.os_type}')>"
    
    @property
    def memory_gb(self) -> float:
        """Get memory in GB."""
        return self.memory_mb / 1024.0 if self.memory_mb else 0.0
    
    def to_vm_dict(self) -> dict:
        """Convert template to VM creation parameters."""
        return {
            "cpu_cores": self.cpu_cores,
            "memory_mb": self.memory_mb,
            "disk_gb": self.disk_gb,
            "os_type": self.os_type,
            "os_version": self.os_version,
            "base_image_path": self.base_image_path
        }