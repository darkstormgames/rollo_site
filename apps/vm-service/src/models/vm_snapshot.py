"""VMSnapshot model for snapshot management."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class VMSnapshot(Base):
    """VMSnapshot model for snapshot management."""
    
    __tablename__ = "vm_snapshots"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # VM reference
    vm_id = Column(Integer, ForeignKey("virtual_machines.id"), nullable=False)
    
    # Snapshot information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    snapshot_path = Column(String(500), nullable=False)  # Path to snapshot file
    
    # Snapshot metadata
    size_mb = Column(Float, nullable=True)  # Snapshot file size in MB
    is_active = Column(Boolean, default=True, nullable=False)  # Whether snapshot is valid/accessible
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    virtual_machine = relationship("VirtualMachine", back_populates="snapshots")
    
    def __repr__(self):
        return f"<VMSnapshot(id={self.id}, vm_id={self.vm_id}, name='{self.name}')>"
    
    @property
    def size_gb(self) -> float:
        """Get snapshot size in GB."""
        return self.size_mb / 1024.0 if self.size_mb else 0.0
    
    @property
    def formatted_size(self) -> str:
        """Get formatted snapshot size."""
        if not self.size_mb:
            return "Unknown"
        if self.size_mb < 1024:
            return f"{self.size_mb:.1f} MB"
        else:
            return f"{self.size_gb:.1f} GB"
    
    def mark_inactive(self):
        """Mark snapshot as inactive/deleted."""
        self.is_active = False