"""Resource configuration schemas for VM management."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class DiskFormat(str, Enum):
    """Disk format enumeration."""
    QCOW2 = "qcow2"
    RAW = "raw"
    VMDK = "vmdk"


class NetworkType(str, Enum):
    """Network type enumeration."""
    BRIDGE = "bridge"
    NAT = "nat"
    VLAN = "vlan"


class CPUConfig(BaseModel):
    """CPU configuration schema."""
    cores: int = Field(..., ge=1, le=32, description="Number of CPU cores")
    sockets: int = Field(1, ge=1, le=4, description="Number of CPU sockets")
    threads: int = Field(1, ge=1, le=2, description="Threads per core")
    model: Optional[str] = Field(None, description="CPU model (e.g., host-passthrough)")
    pinning: Optional[List[int]] = Field(None, description="CPU pinning to physical cores")
    shares: Optional[int] = Field(None, ge=1, le=2048, description="CPU shares (relative weight)")
    limit: Optional[int] = Field(None, ge=1, le=100, description="CPU limit percentage")
    numa_nodes: Optional[List[int]] = Field(None, description="NUMA node assignment")


class MemoryConfig(BaseModel):
    """Memory configuration schema."""
    size_mb: int = Field(..., ge=512, le=65536, description="Memory size in MB")
    hugepages: bool = Field(False, description="Enable huge pages")
    balloon: bool = Field(True, description="Enable memory ballooning")
    shares: Optional[int] = Field(None, ge=1, le=2048, description="Memory shares")
    numa_nodes: Optional[List[int]] = Field(None, description="NUMA memory binding")
    overcommit_ratio: Optional[float] = Field(None, ge=0.5, le=2.0, description="Memory overcommit ratio")


class DiskConfig(BaseModel):
    """Disk configuration schema."""
    name: str = Field(..., description="Disk name/identifier")
    size_gb: float = Field(..., ge=1.0, le=2000.0, description="Disk size in GB")
    format: DiskFormat = Field(DiskFormat.QCOW2, description="Disk format")
    pool: Optional[str] = Field("default", description="Storage pool name")
    path: Optional[str] = Field(None, description="Custom disk path")
    cache: str = Field("writeback", description="Cache mode")
    discard: bool = Field(False, description="Enable discard/TRIM")
    readonly: bool = Field(False, description="Read-only disk")
    bootable: bool = Field(False, description="Bootable disk")


class NetworkConfig(BaseModel):
    """Network configuration schema."""
    name: str = Field(..., description="Network interface name")
    type: NetworkType = Field(NetworkType.NAT, description="Network type")
    bridge: Optional[str] = Field(None, description="Bridge name for bridge networks")
    vlan_id: Optional[int] = Field(None, ge=1, le=4094, description="VLAN ID")
    ip_address: Optional[str] = Field(None, description="Static IP address")
    netmask: Optional[str] = Field(None, description="Network mask")
    gateway: Optional[str] = Field(None, description="Gateway address")
    mac_address: Optional[str] = Field(None, description="MAC address")
    bandwidth_limit: Optional[int] = Field(None, ge=1, description="Bandwidth limit in Mbps")


class VMResources(BaseModel):
    """Complete VM resource configuration."""
    cpu: CPUConfig
    memory: MemoryConfig
    disks: List[DiskConfig]
    network: List[NetworkConfig]


class ResourceLimits(BaseModel):
    """System resource limits."""
    max_cpu_cores: int = Field(..., description="Maximum CPU cores per VM")
    max_memory_mb: int = Field(..., description="Maximum memory per VM in MB")
    max_disk_gb: float = Field(..., description="Maximum disk size per VM in GB")
    max_disks: int = Field(..., description="Maximum number of disks per VM")
    max_networks: int = Field(..., description="Maximum number of network interfaces per VM")
    available_cpu_cores: int = Field(..., description="Available CPU cores on host")
    available_memory_mb: int = Field(..., description="Available memory on host in MB")
    available_disk_gb: float = Field(..., description="Available disk space on host in GB")


class ResourceAllocation(BaseModel):
    """Current resource allocation tracking."""
    allocated_cpu_cores: int = Field(..., description="Currently allocated CPU cores")
    allocated_memory_mb: int = Field(..., description="Currently allocated memory in MB")
    allocated_disk_gb: float = Field(..., description="Currently allocated disk space in GB")
    vm_count: int = Field(..., description="Number of VMs")


class ResourceValidationResult(BaseModel):
    """Resource validation result."""
    valid: bool = Field(..., description="Whether resources are valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")


class HotAddRequest(BaseModel):
    """Hot-add resource request."""
    resource_type: str = Field(..., description="Type of resource (cpu, memory, disk, network)")
    config: Dict[str, Any] = Field(..., description="Resource configuration")


class ResizeRequest(BaseModel):
    """VM resize request with validation."""
    cpu: Optional[CPUConfig] = Field(None, description="New CPU configuration")
    memory: Optional[MemoryConfig] = Field(None, description="New memory configuration")
    disks: Optional[List[DiskConfig]] = Field(None, description="New disk configuration")
    network: Optional[List[NetworkConfig]] = Field(None, description="New network configuration")
    validate_only: bool = Field(False, description="Only validate, don't apply changes")