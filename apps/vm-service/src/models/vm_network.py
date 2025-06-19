"""VM network model for network interface management."""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class VMNetwork(Base):
    """VM network interface model."""
    
    __tablename__ = "vm_networks"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # VM relationship
    vm_id = Column(Integer, ForeignKey("virtual_machines.id"), nullable=False)
    
    # Interface identification
    name = Column(String(255), nullable=False, index=True)
    device_name = Column(String(50), nullable=True)  # e.g., eth0, ens3
    
    # Network configuration
    type = Column(String(20), nullable=False, default="nat")  # nat, bridge, vlan
    bridge = Column(String(255), nullable=True)
    vlan_id = Column(Integer, nullable=True)
    
    # IP configuration
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    netmask = Column(String(45), nullable=True)
    gateway = Column(String(45), nullable=True)
    mac_address = Column(String(17), nullable=True, unique=True)  # MAC address format: XX:XX:XX:XX:XX:XX
    
    # Performance settings
    bandwidth_limit = Column(Integer, nullable=True)  # Mbps
    
    # Status and metadata
    status = Column(String(20), nullable=False, default="configured")  # configured, active, inactive, error
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    virtual_machine = relationship("VirtualMachine", back_populates="networks")
    
    def __repr__(self):
        return f"<VMNetwork(id={self.id}, vm_id={self.vm_id}, name='{self.name}', type='{self.type}')>"
    
    @property
    def is_static_ip(self) -> bool:
        """Check if network interface uses static IP."""
        return self.ip_address is not None