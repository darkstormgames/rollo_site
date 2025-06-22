"""OS Image model for image management."""

from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .base import Base


class ImageStatus(enum.Enum):
    """Image status enumeration."""
    UPLOADING = "uploading"
    IMPORTING = "importing"
    AVAILABLE = "available"
    ERROR = "error"
    DELETED = "deleted"


class OSImage(Base):
    """OSImage model for managing OS images."""
    
    __tablename__ = "os_images"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Image information
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Operating system
    os_type = Column(String(50), nullable=False, index=True)
    os_version = Column(String(100), nullable=True)
    
    # Image properties
    format = Column(String(20), nullable=False, default="qcow2")  # qcow2, raw, vmdk, etc.
    file_path = Column(String(500), nullable=True)  # Local file path
    source_url = Column(String(1000), nullable=True)  # Source URL for import
    checksum = Column(String(64), nullable=True)  # SHA256 checksum
    size_gb = Column(Float, nullable=True)  # Image size in GB
    status = Column(Enum(ImageStatus), nullable=False, default=ImageStatus.UPLOADING, index=True)
    
    # Image metadata
    public = Column(Boolean, nullable=False, default=False)
    download_count = Column(Integer, nullable=False, default=0)
    
    # Error handling
    error_message = Column(Text, nullable=True)  # Error details if status is ERROR
    
    # Ownership and timestamps
    created_by = Column(Integer, nullable=False)  # SSO user ID, no ForeignKey
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    templates = relationship("VMTemplate", back_populates="os_image")
    
    def __repr__(self):
        return f"<OSImage(id={self.id}, name='{self.name}', os_type='{self.os_type}', status='{self.status}')>"
    
    @property
    def is_available(self) -> bool:
        """Check if image is available for use."""
        return self.status == ImageStatus.AVAILABLE
    
    @property
    def size_mb(self) -> float:
        """Get size in MB."""
        return self.size_gb * 1024.0 if self.size_gb else 0.0
    
    def to_dict(self) -> dict:
        """Convert image to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "os_type": self.os_type,
            "os_version": self.os_version,
            "format": self.format,
            "file_path": self.file_path,
            "source_url": self.source_url,
            "checksum": self.checksum,
            "size_gb": self.size_gb,
            "status": self.status.value if self.status else None,
            "public": self.public,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }