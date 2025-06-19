"""VM template schemas for predefined configurations."""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, HttpUrl
from enum import Enum

from .resources import VMResources, CPUConfig, MemoryConfig, DiskConfig, NetworkConfig
from models.virtual_machine import OSType


class TemplateType(str, Enum):
    """Template type enumeration."""
    # Resource-based templates
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    CUSTOM = "custom"
    
    # OS templates
    UBUNTU_20_04 = "ubuntu-20-04"
    UBUNTU_22_04 = "ubuntu-22-04"
    UBUNTU_24_04 = "ubuntu-24-04"
    DEBIAN_11 = "debian-11"
    DEBIAN_12 = "debian-12"
    CENTOS_STREAM_8 = "centos-stream-8"
    CENTOS_STREAM_9 = "centos-stream-9"
    WINDOWS_SERVER_2012 = "windows-server-2012"
    WINDOWS_SERVER_2016 = "windows-server-2016"
    WINDOWS_7 = "windows-7"
    WINDOWS_8_1 = "windows-8-1"
    WINDOWS_10 = "windows-10"
    WINDOWS_11 = "windows-11"
    
    # Application templates  
    LAMP_STACK = "lamp-stack"
    DOCKER_HOST = "docker-host"
    KUBERNETES_NODE = "kubernetes-node"
    DATABASE_SERVER = "database-server"
    WEB_SERVER = "web-server"
    
    # Resource profile templates
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    HIGH_PERFORMANCE = "high-performance"


class TemplateCreate(BaseModel):
    """Create template request schema."""
    name: str = Field(..., min_length=1, max_length=255, description="Template name")
    description: Optional[str] = Field(None, max_length=1000, description="Template description")
    type: TemplateType = Field(..., description="Template type")
    os_type: OSType = Field(..., description="Operating system type")
    os_version: Optional[str] = Field(None, max_length=100, description="OS version")
    resources: VMResources = Field(..., description="Resource configuration")
    base_image_path: Optional[str] = Field(None, description="Base image path")
    tags: Optional[List[str]] = Field(default_factory=list, description="Template tags")
    public: bool = Field(False, description="Whether template is public")
    
    # New fields for enhanced template system
    packages: Optional[List[str]] = Field(default_factory=list, description="Pre-installed packages")
    cloud_init_config: Optional[str] = Field(None, description="Cloud-init user data configuration")
    image_source: Optional[str] = Field(None, description="Source URL or path for OS image")
    image_checksum: Optional[str] = Field(None, description="SHA256 checksum of the image")
    image_format: Optional[str] = Field("qcow2", description="Image format (qcow2, raw, vmdk)")
    startup_scripts: Optional[List[str]] = Field(default_factory=list, description="Startup script paths")
    network_config: Optional[Dict[str, Any]] = Field(None, description="Network configuration presets")
    security_hardening: Optional[Dict[str, Any]] = Field(None, description="Security hardening options")


class TemplateUpdate(BaseModel):
    """Update template request schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    resources: Optional[VMResources] = Field(None)
    base_image_path: Optional[str] = Field(None)
    tags: Optional[List[str]] = Field(None)
    public: Optional[bool] = Field(None)
    
    # New fields for enhanced template system
    packages: Optional[List[str]] = Field(None, description="Pre-installed packages")
    cloud_init_config: Optional[str] = Field(None, description="Cloud-init user data configuration")
    image_source: Optional[str] = Field(None, description="Source URL or path for OS image")
    image_checksum: Optional[str] = Field(None, description="SHA256 checksum of the image")
    image_format: Optional[str] = Field(None, description="Image format (qcow2, raw, vmdk)")
    startup_scripts: Optional[List[str]] = Field(None, description="Startup script paths")
    network_config: Optional[Dict[str, Any]] = Field(None, description="Network configuration presets")
    security_hardening: Optional[Dict[str, Any]] = Field(None, description="Security hardening options")


class TemplateResponse(BaseModel):
    """Template response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: Optional[str]
    type: TemplateType
    os_type: OSType
    os_version: Optional[str]
    resources: VMResources
    base_image_path: Optional[str]
    tags: List[str]
    public: bool
    created_by: int
    created_at: datetime
    version: int = Field(1, description="Template version")
    
    # New fields for enhanced template system
    packages: List[str] = Field(default_factory=list, description="Pre-installed packages")
    cloud_init_config: Optional[str] = Field(None, description="Cloud-init user data configuration")
    image_source: Optional[str] = Field(None, description="Source URL or path for OS image")
    image_checksum: Optional[str] = Field(None, description="SHA256 checksum of the image")
    image_format: str = Field("qcow2", description="Image format (qcow2, raw, vmdk)")
    startup_scripts: List[str] = Field(default_factory=list, description="Startup script paths")
    network_config: Optional[Dict[str, Any]] = Field(None, description="Network configuration presets")
    security_hardening: Optional[Dict[str, Any]] = Field(None, description="Security hardening options")


class TemplateListResponse(BaseModel):
    """Template list response schema."""
    templates: List[TemplateResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class TemplateListFilters(BaseModel):
    """Template list filtering parameters."""
    type: Optional[TemplateType] = Field(None, description="Filter by template type")
    os_type: Optional[OSType] = Field(None, description="Filter by OS type")
    public: Optional[bool] = Field(None, description="Filter by public templates")
    created_by: Optional[int] = Field(None, description="Filter by creator")
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(None, description="Search in template names")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")


class PredefinedTemplate(BaseModel):
    """Predefined template configuration."""
    name: str
    description: str
    type: TemplateType
    os_type: OSType
    resources: VMResources


# Image Management Schemas
class ImageStatus(str, Enum):
    """Image status enumeration."""
    UPLOADING = "uploading"
    IMPORTING = "importing"
    AVAILABLE = "available"
    ERROR = "error"
    DELETED = "deleted"


class ImageCreate(BaseModel):
    """Create image request schema."""
    name: str = Field(..., min_length=1, max_length=255, description="Image name")
    description: Optional[str] = Field(None, max_length=1000, description="Image description")
    os_type: OSType = Field(..., description="Operating system type")
    os_version: Optional[str] = Field(None, max_length=100, description="OS version")
    format: str = Field("qcow2", description="Image format")
    source_url: Optional[HttpUrl] = Field(None, description="Source URL for import")
    checksum: Optional[str] = Field(None, description="SHA256 checksum")
    size_gb: Optional[float] = Field(None, description="Image size in GB")
    public: bool = Field(False, description="Whether image is public")


class ImageResponse(BaseModel):
    """Image response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: Optional[str]
    os_type: OSType
    os_version: Optional[str]
    format: str
    file_path: Optional[str]
    source_url: Optional[str]
    checksum: Optional[str]
    size_gb: Optional[float]
    status: ImageStatus
    public: bool
    created_by: int
    created_at: datetime
    updated_at: datetime


class ImageListResponse(BaseModel):
    """Image list response schema."""
    images: List[ImageResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


# Template Deployment Schemas
class TemplateDeployRequest(BaseModel):
    """Deploy VM from template request schema."""
    template_id: int = Field(..., description="Template ID to deploy from")
    vm_name: str = Field(..., min_length=1, max_length=255, description="VM name")
    hostname: Optional[str] = Field(None, description="VM hostname")
    
    # Resource customization (optional overrides)
    custom_resources: Optional[VMResources] = Field(None, description="Custom resource configuration")
    
    # Network customization
    network_interfaces: Optional[List[Dict[str, Any]]] = Field(None, description="Network interface configuration")
    
    # Cloud-init customization
    custom_cloud_init: Optional[str] = Field(None, description="Custom cloud-init configuration")
    
    # User credentials
    root_password: Optional[str] = Field(None, description="Root password")
    ssh_keys: Optional[List[str]] = Field(None, description="SSH public keys")
    
    # Additional customization
    custom_packages: Optional[List[str]] = Field(None, description="Additional packages to install")
    environment_variables: Optional[Dict[str, str]] = Field(None, description="Environment variables")


class TemplateDeployResponse(BaseModel):
    """Deploy VM from template response schema."""
    vm_id: int = Field(..., description="Created VM ID")
    vm_name: str = Field(..., description="VM name")
    vm_uuid: str = Field(..., description="VM UUID")
    status: str = Field(..., description="Deployment status")
    message: str = Field(..., description="Deployment message")
    template_used: TemplateResponse = Field(..., description="Template that was used")


# Template Versioning Schemas
class TemplateVersion(BaseModel):
    """Template version information."""
    version: int
    created_at: datetime
    created_by: int
    changes: Optional[str] = Field(None, description="Description of changes")
    template_data: Dict[str, Any] = Field(..., description="Template configuration at this version")


class TemplateVersionResponse(BaseModel):
    """Template version response schema."""
    template_id: int
    versions: List[TemplateVersion]
    current_version: int


# Predefined template configurations
PREDEFINED_TEMPLATES = {
    # Resource-based templates
    TemplateType.SMALL: PredefinedTemplate(
        name="Small VM",
        description="Small VM with 1 CPU, 2GB RAM, 20GB disk",
        type=TemplateType.SMALL,
        os_type=OSType.LINUX,
        resources=VMResources(
            cpu=CPUConfig(cores=1, sockets=1, threads=1),
            memory=MemoryConfig(size_mb=2048, hugepages=False, balloon=True),
            disks=[DiskConfig(
                name="main",
                size_gb=20.0,
                format="qcow2",
                bootable=True
            )],
            network=[NetworkConfig(
                name="default",
                type="nat"
            )]
        )
    ),
    TemplateType.MEDIUM: PredefinedTemplate(
        name="Medium VM",
        description="Medium VM with 2 CPUs, 4GB RAM, 40GB disk",
        type=TemplateType.MEDIUM,
        os_type=OSType.LINUX,
        resources=VMResources(
            cpu=CPUConfig(cores=2, sockets=1, threads=1),
            memory=MemoryConfig(size_mb=4096, hugepages=False, balloon=True),
            disks=[DiskConfig(
                name="main",
                size_gb=40.0,
                format="qcow2",
                bootable=True
            )],
            network=[NetworkConfig(
                name="default",
                type="nat"
            )]
        )
    ),
    TemplateType.LARGE: PredefinedTemplate(
        name="Large VM",
        description="Large VM with 4 CPUs, 8GB RAM, 80GB disk",
        type=TemplateType.LARGE,
        os_type=OSType.LINUX,
        resources=VMResources(
            cpu=CPUConfig(cores=4, sockets=1, threads=1),
            memory=MemoryConfig(size_mb=8192, hugepages=False, balloon=True),
            disks=[DiskConfig(
                name="main",
                size_gb=80.0,
                format="qcow2",
                bootable=True
            )],
            network=[NetworkConfig(
                name="default",
                type="nat"
            )]
        )
    ),
    
    # OS Templates
    TemplateType.UBUNTU_22_04: PredefinedTemplate(
        name="Ubuntu 22.04 LTS",
        description="Ubuntu 22.04 LTS with 2 CPUs, 4GB RAM, 40GB disk",
        type=TemplateType.UBUNTU_22_04,
        os_type=OSType.LINUX,
        resources=VMResources(
            cpu=CPUConfig(cores=2, sockets=1, threads=1),
            memory=MemoryConfig(size_mb=4096, hugepages=False, balloon=True),
            disks=[DiskConfig(
                name="main",
                size_gb=40.0,
                format="qcow2",
                bootable=True
            )],
            network=[NetworkConfig(
                name="default",
                type="nat"
            )]
        )
    ),
    
    TemplateType.DEBIAN_12: PredefinedTemplate(
        name="Debian 12",
        description="Debian 12 with 2 CPUs, 4GB RAM, 40GB disk",
        type=TemplateType.DEBIAN_12,
        os_type=OSType.LINUX,
        resources=VMResources(
            cpu=CPUConfig(cores=2, sockets=1, threads=1),
            memory=MemoryConfig(size_mb=4096, hugepages=False, balloon=True),
            disks=[DiskConfig(
                name="main",
                size_gb=40.0,
                format="qcow2",
                bootable=True
            )],
            network=[NetworkConfig(
                name="default",
                type="nat"
            )]
        )
    ),
    
    # Application Templates
    TemplateType.LAMP_STACK: PredefinedTemplate(
        name="LAMP Stack",
        description="LAMP stack with Apache, MySQL, PHP on Ubuntu 22.04",
        type=TemplateType.LAMP_STACK,
        os_type=OSType.LINUX,
        resources=VMResources(
            cpu=CPUConfig(cores=2, sockets=1, threads=1),
            memory=MemoryConfig(size_mb=4096, hugepages=False, balloon=True),
            disks=[DiskConfig(
                name="main",
                size_gb=60.0,
                format="qcow2",
                bootable=True
            )],
            network=[NetworkConfig(
                name="default",
                type="nat"
            )]
        )
    ),
    
    TemplateType.DOCKER_HOST: PredefinedTemplate(
        name="Docker Host",
        description="Docker host with Docker CE on Ubuntu 22.04",
        type=TemplateType.DOCKER_HOST,
        os_type=OSType.LINUX,
        resources=VMResources(
            cpu=CPUConfig(cores=2, sockets=1, threads=1),
            memory=MemoryConfig(size_mb=4096, hugepages=False, balloon=True),
            disks=[DiskConfig(
                name="main",
                size_gb=80.0,
                format="qcow2",
                bootable=True
            )],
            network=[NetworkConfig(
                name="default",
                type="nat"
            )]
        )
    ),
    
    # Resource Profile Templates
    TemplateType.DEVELOPMENT: PredefinedTemplate(
        name="Development VM",
        description="Development environment with minimal resources",
        type=TemplateType.DEVELOPMENT,
        os_type=OSType.LINUX,
        resources=VMResources(
            cpu=CPUConfig(cores=1, sockets=1, threads=1),
            memory=MemoryConfig(size_mb=2048, hugepages=False, balloon=True),
            disks=[DiskConfig(
                name="main",
                size_gb=30.0,
                format="qcow2",
                bootable=True
            )],
            network=[NetworkConfig(
                name="default",
                type="nat"
            )]
        )
    ),
    
    TemplateType.PRODUCTION: PredefinedTemplate(
        name="Production VM",
        description="Production environment with balanced resources",
        type=TemplateType.PRODUCTION,
        os_type=OSType.LINUX,
        resources=VMResources(
            cpu=CPUConfig(cores=4, sockets=1, threads=1),
            memory=MemoryConfig(size_mb=8192, hugepages=False, balloon=True),
            disks=[DiskConfig(
                name="main",
                size_gb=100.0,
                format="qcow2",
                bootable=True
            )],
            network=[NetworkConfig(
                name="default",
                type="nat"
            )]
        )
    ),
    
    TemplateType.HIGH_PERFORMANCE: PredefinedTemplate(
        name="High Performance VM",
        description="High performance environment with maximum resources",
        type=TemplateType.HIGH_PERFORMANCE,
        os_type=OSType.LINUX,
        resources=VMResources(
            cpu=CPUConfig(cores=8, sockets=1, threads=1),
            memory=MemoryConfig(size_mb=16384, hugepages=False, balloon=True),
            disks=[DiskConfig(
                name="main",
                size_gb=200.0,
                format="qcow2",
                bootable=True
            )],
            network=[NetworkConfig(
                name="default",
                type="nat"
            )]
        )
    )
}