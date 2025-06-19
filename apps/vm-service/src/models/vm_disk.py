"""VM disk model for disk management."""

from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class VMDisk(Base):
    """VM disk model for individual disk management."""
    
    __tablename__ = "vm_disks"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # VM relationship
    vm_id = Column(Integer, ForeignKey("virtual_machines.id"), nullable=False)
    
    # Disk identification
    name = Column(String(255), nullable=False, index=True)
    device_name = Column(String(50), nullable=True)  # e.g., vda, vdb, sda
    
    # Disk configuration
    size_gb = Column(Float, nullable=False)
    format = Column(String(20), nullable=False, default="qcow2")  # qcow2, raw, vmdk
    pool = Column(String(255), nullable=False, default="default")
    path = Column(String(500), nullable=True)
    
    # Performance settings
    cache = Column(String(20), nullable=False, default="writeback")
    discard = Column(Boolean, nullable=False, default=False)
    readonly = Column(Boolean, nullable=False, default=False)
    
    # Boot settings
    bootable = Column(Boolean, nullable=False, default=False)
    boot_order = Column(Integer, nullable=True)
    
    # Status and metadata
    status = Column(String(20), nullable=False, default="created")  # created, attached, detached, error
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    virtual_machine = relationship("VirtualMachine", back_populates="disks")
    
    def __repr__(self):
        return f"<VMDisk(id={self.id}, vm_id={self.vm_id}, name='{self.name}', size_gb={self.size_gb})>"
    
    @property
    def full_path(self) -> str:
        """Get full disk path."""
        if self.path:
            return self.path
        return f"/var/lib/libvirt/images/{self.virtual_machine.name}_{self.name}.{self.format}"