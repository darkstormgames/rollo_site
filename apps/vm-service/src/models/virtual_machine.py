"""VirtualMachine model for VM instances."""

from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, Float, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .base import Base


class VMStatus(enum.Enum):
    """Virtual machine status enumeration."""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    SUSPENDED = "suspended"
    STARTING = "starting"
    STOPPING = "stopping"
    ERROR = "error"


class OSType(enum.Enum):
    """Operating system type enumeration."""
    LINUX = "linux"
    WINDOWS = "windows"
    BSD = "bsd"
    OTHER = "other"


class VirtualMachine(Base):
    """VirtualMachine model for VM instances."""
    
    __tablename__ = "virtual_machines"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # VM identification
    name = Column(String(255), nullable=False, index=True)
    uuid = Column(String(36), unique=True, nullable=False, index=True)  # UUID4 format
    
    # VM status and configuration
    status = Column(Enum(VMStatus), nullable=False, default=VMStatus.STOPPED, index=True)
    server_id = Column(Integer, ForeignKey("servers.id"), nullable=False)
    
    # Hardware specifications
    cpu_cores = Column(Integer, nullable=False, default=1)
    cpu_sockets = Column(Integer, nullable=False, default=1)
    cpu_threads = Column(Integer, nullable=False, default=1)
    cpu_model = Column(String(100), nullable=True)
    cpu_pinning = Column(Text, nullable=True)  # JSON array of pinned cores
    cpu_shares = Column(Integer, nullable=True)
    cpu_limit = Column(Integer, nullable=True)  # CPU limit percentage
    numa_nodes = Column(Text, nullable=True)  # JSON array of NUMA nodes
    
    memory_mb = Column(Integer, nullable=False, default=1024)
    memory_hugepages = Column(Boolean, nullable=False, default=False)
    memory_balloon = Column(Boolean, nullable=False, default=True)
    memory_shares = Column(Integer, nullable=True)
    memory_numa_nodes = Column(Text, nullable=True)  # JSON array of NUMA nodes
    
    disk_gb = Column(Float, nullable=False, default=20.0)  # Primary disk size (for backwards compatibility)
    
    # Operating system
    os_type = Column(Enum(OSType), nullable=False, default=OSType.LINUX)
    os_version = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    
    # VNC access
    vnc_port = Column(Integer, nullable=True)
    
    # Ownership and timestamps
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    server = relationship("Server", back_populates="virtual_machines")
    created_by_user = relationship("User", back_populates="created_vms")
    snapshots = relationship("VMSnapshot", back_populates="virtual_machine", cascade="all, delete-orphan")
    disks = relationship("VMDisk", back_populates="virtual_machine", cascade="all, delete-orphan")
    networks = relationship("VMNetwork", back_populates="virtual_machine", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<VirtualMachine(id={self.id}, name='{self.name}', uuid='{self.uuid}', status='{self.status.value}')>"
    
    @property
    def is_running(self) -> bool:
        """Check if VM is running."""
        return self.status == VMStatus.RUNNING
    
    @property
    def memory_gb(self) -> float:
        """Get memory in GB."""
        return self.memory_mb / 1024.0 if self.memory_mb else 0.0