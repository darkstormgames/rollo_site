"""VM template schemas for predefined configurations."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

from .resources import VMResources, CPUConfig, MemoryConfig, DiskConfig, NetworkConfig
from models.virtual_machine import OSType


class TemplateType(str, Enum):
    """Template type enumeration."""
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    CUSTOM = "custom"


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


class TemplateUpdate(BaseModel):
    """Update template request schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    resources: Optional[VMResources] = Field(None)
    base_image_path: Optional[str] = Field(None)
    tags: Optional[List[str]] = Field(None)
    public: Optional[bool] = Field(None)


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


# Predefined template configurations
PREDEFINED_TEMPLATES = {
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
    )
}