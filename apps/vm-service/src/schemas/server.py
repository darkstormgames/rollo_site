"""Server request and response schemas."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, IPvAnyAddress

from models.server import ServerStatus


class ServerSystemInfo(BaseModel):
    """Server system information schema."""
    os_version: str = Field(..., max_length=100, description="Operating system version")
    cpu_cores: int = Field(..., ge=1, le=256, description="Number of CPU cores")
    memory_gb: float = Field(..., ge=0.1, le=1024.0, description="Memory in GB")
    disk_gb: float = Field(..., ge=1.0, le=10000.0, description="Disk space in GB")


class ServerRegistrationRequest(BaseModel):
    """Server registration request schema."""
    hostname: str = Field(..., min_length=1, max_length=255, description="Server hostname")
    ip_address: str = Field(..., description="Server IP address")
    agent_version: str = Field(..., max_length=50, description="Agent version")
    system_info: ServerSystemInfo = Field(..., description="System specifications")
    auth_token: str = Field(..., description="Authentication token for registration")


class ServerUpdate(BaseModel):
    """Server update request schema."""
    hostname: Optional[str] = Field(None, min_length=1, max_length=255)
    ip_address: Optional[str] = Field(None)
    port: Optional[int] = Field(None, ge=1, le=65535)
    status: Optional[ServerStatus] = Field(None)
    os_version: Optional[str] = Field(None, max_length=100)
    cpu_cores: Optional[int] = Field(None, ge=1, le=256)
    memory_gb: Optional[float] = Field(None, ge=0.1, le=1024.0)
    disk_gb: Optional[float] = Field(None, ge=1.0, le=10000.0)
    agent_version: Optional[str] = Field(None, max_length=50)


class ServerResponse(BaseModel):
    """Server response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    hostname: str
    ip_address: str
    port: int
    status: ServerStatus
    os_version: Optional[str]
    cpu_cores: Optional[int]
    memory_gb: Optional[float]
    disk_gb: Optional[float]
    agent_version: Optional[str]
    last_heartbeat: Optional[datetime]
    vm_count: int
    created_at: datetime
    updated_at: datetime


class ServerListResponse(BaseModel):
    """Server list response schema."""
    servers: List[ServerResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class ServerDiscoverRequest(BaseModel):
    """Server discovery request schema."""
    subnet: str = Field(..., description="Subnet to scan (e.g., 192.168.1.0/24)")
    port: int = Field(default=22, ge=1, le=65535, description="Port to check")
    timeout: int = Field(default=5, ge=1, le=30, description="Connection timeout in seconds")


class ServerDiscoverResponse(BaseModel):
    """Server discovery response schema."""
    discovered_servers: List[str] = Field(..., description="List of discovered server IP addresses")
    scan_duration: float = Field(..., description="Scan duration in seconds")
    total_found: int = Field(..., description="Number of servers found")


class ServerStatusResponse(BaseModel):
    """Server status response schema."""
    id: int
    hostname: str
    ip_address: str
    status: ServerStatus
    last_heartbeat: Optional[datetime]
    agent_version: Optional[str]
    uptime_seconds: Optional[int]
    is_reachable: bool


class ServerMetricsResponse(BaseModel):
    """Server metrics response schema."""
    id: int
    hostname: str
    timestamp: datetime
    cpu_usage_percent: Optional[float]
    memory_usage_percent: Optional[float]
    memory_used_gb: Optional[float]
    memory_total_gb: Optional[float]
    disk_usage_percent: Optional[float]
    disk_used_gb: Optional[float]
    disk_total_gb: Optional[float]
    network_rx_bytes: Optional[int]
    network_tx_bytes: Optional[int]
    load_average: Optional[float]


class ServerHealthCheckResponse(BaseModel):
    """Server health check response schema."""
    id: int
    hostname: str
    status: ServerStatus
    timestamp: datetime
    checks: dict = Field(..., description="Health check results")
    overall_health: str = Field(..., description="Overall health status: healthy, warning, critical")


class ServerOperationResponse(BaseModel):
    """Server operation response schema."""
    id: int
    hostname: str
    operation: str
    status: str
    message: Optional[str] = None
    timestamp: datetime


# Query parameters for listing servers
class ServerListFilters(BaseModel):
    """Server list filtering parameters."""
    status: Optional[ServerStatus] = Field(None, description="Filter by server status")
    hostname: Optional[str] = Field(None, description="Filter by hostname (partial match)")
    agent_version: Optional[str] = Field(None, description="Filter by agent version")


class MessageResponse(BaseModel):
    """Simple message response schema."""
    message: str
    detail: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None