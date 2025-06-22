"""Server model for physical/remote servers."""

from sqlalchemy import Column, Integer, String, Enum, DateTime, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .base import Base


class ServerStatus(enum.Enum):
    """Server status enumeration."""
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    ERROR = "error"


class Server(Base):
    """Server model for physical/remote servers."""
    
    __tablename__ = "servers"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Server identification
    hostname = Column(String(255), unique=True, nullable=False, index=True)
    ip_address = Column(String(45), nullable=False)  # IPv6 support
    port = Column(Integer, nullable=False, default=22)
    
    # Server status and OS
    status = Column(Enum(ServerStatus), nullable=False, default=ServerStatus.OFFLINE, index=True)
    os_version = Column(String(100), nullable=True)
    
    # Hardware specifications
    cpu_cores = Column(Integer, nullable=True)
    memory_gb = Column(Float, nullable=True)
    disk_gb = Column(Float, nullable=True)
    
    # Agent information
    agent_version = Column(String(50), nullable=True)
    last_heartbeat = Column(DateTime(timezone=True), nullable=True)
    
    # Ownership and timestamps
    user_id = Column(Integer, nullable=False)  # SSO user ID, no ForeignKey
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    virtual_machines = relationship("VirtualMachine", back_populates="server", cascade="all, delete-orphan")
    metrics = relationship("ServerMetrics", back_populates="server", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Server(id={self.id}, hostname='{self.hostname}', status='{self.status.value}')>"
    
    @property
    def is_online(self) -> bool:
        """Check if server is online."""
        return self.status == ServerStatus.ONLINE
    
    @property
    def vm_count(self) -> int:
        """Get count of VMs on this server."""
        return len(self.virtual_machines) if self.virtual_machines else 0