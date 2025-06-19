"""VM request and response schemas."""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

from models.virtual_machine import VMStatus, OSType


class NetworkType(str, Enum):
    """Network configuration type."""
    BRIDGE = "bridge"
    NAT = "nat"


class NetworkConfig(BaseModel):
    """Network configuration schema."""
    type: NetworkType = Field(..., description="Network type (bridge or nat)")
    bridge_name: Optional[str] = Field(None, description="Bridge name for bridge type networks")


class VMCreate(BaseModel):
    """Create VM request schema."""
    name: str = Field(..., min_length=1, max_length=255, description="VM name")
    template_id: Optional[str] = Field(None, description="Template ID for VM creation")
    server_id: int = Field(..., description="Server ID where VM will be created")
    cpu_cores: int = Field(..., ge=1, le=32, description="Number of CPU cores")
    memory_mb: int = Field(..., ge=512, le=32768, description="Memory in MB")
    disk_gb: float = Field(..., ge=10.0, le=1000.0, description="Disk size in GB")
    os_type: OSType = Field(default=OSType.LINUX, description="Operating system type")
    os_version: Optional[str] = Field(None, max_length=100, description="OS version")
    network_config: NetworkConfig = Field(default_factory=lambda: NetworkConfig(type=NetworkType.NAT))


class VMUpdate(BaseModel):
    """Update VM request schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    cpu_cores: Optional[int] = Field(None, ge=1, le=32)
    memory_mb: Optional[int] = Field(None, ge=512, le=32768)
    disk_gb: Optional[float] = Field(None, ge=10.0, le=1000.0)
    os_version: Optional[str] = Field(None, max_length=100)


class VMResize(BaseModel):
    """VM resize request schema."""
    cpu_cores: Optional[int] = Field(None, ge=1, le=32, description="New CPU cores count")
    memory_mb: Optional[int] = Field(None, ge=512, le=32768, description="New memory in MB")
    disk_gb: Optional[float] = Field(None, ge=10.0, le=1000.0, description="New disk size in GB")


class VMConfigUpdate(BaseModel):
    """VM configuration update schema."""
    cpu_cores: Optional[int] = Field(None, ge=1, le=32)
    memory_mb: Optional[int] = Field(None, ge=512, le=32768)
    vnc_enabled: Optional[bool] = Field(None)
    network_config: Optional[NetworkConfig] = Field(None)


class ServerInfo(BaseModel):
    """Server information schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    hostname: str


class VMResources(BaseModel):
    """VM resources schema."""
    cpu_cores: int
    memory_mb: int
    disk_gb: float


class VMNetwork(BaseModel):
    """VM network information schema."""
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None


class VMResponse(BaseModel):
    """VM response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    uuid: str
    status: VMStatus
    server: ServerInfo
    resources: VMResources
    network: VMNetwork
    os_type: OSType
    os_version: Optional[str]
    vnc_port: Optional[int]
    created_at: datetime
    updated_at: datetime


class VMListResponse(BaseModel):
    """VM list response schema."""
    vms: List[VMResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class VMOperationResponse(BaseModel):
    """VM operation response schema."""
    id: int
    name: str
    operation: str
    status: str
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class VMConfig(BaseModel):
    """VM configuration response schema."""
    id: int
    name: str
    uuid: str
    cpu_cores: int
    memory_mb: int
    disk_gb: float
    os_type: OSType
    os_version: Optional[str]
    vnc_enabled: bool
    vnc_port: Optional[int]
    network_config: Dict[str, Any]
    xml_config: Optional[str] = None


class MessageResponse(BaseModel):
    """Simple message response schema."""
    message: str
    detail: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


# Query parameters for listing VMs
class VMListFilters(BaseModel):
    """VM list filtering parameters."""
    status: Optional[VMStatus] = Field(None, description="Filter by VM status")
    server_id: Optional[int] = Field(None, description="Filter by server ID")
    os_type: Optional[OSType] = Field(None, description="Filter by OS type")
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(None, description="Search in VM names")