"""VMTemplate model for predefined VM configurations."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
from .virtual_machine import OSType


class VMTemplate(Base):
    """VMTemplate model for predefined VM configurations."""
    
    __tablename__ = "vm_templates"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Template information
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    type = Column(String(20), nullable=False, default="custom")  # small, medium, large, custom, etc.
    version = Column(Integer, nullable=False, default=1)
    
    # Operating system
    os_type = Column(String(50), nullable=False, default="linux")  # Using String instead of Enum for flexibility
    os_version = Column(String(100), nullable=True)
    
    # Hardware specifications
    cpu_cores = Column(Integer, nullable=False, default=1)
    memory_mb = Column(Integer, nullable=False, default=1024)
    disk_gb = Column(Float, nullable=False, default=20.0)
    
    # Resource configuration (JSON)
    resource_config = Column(Text, nullable=True)  # JSON blob for advanced resource configuration
    
    # Base image
    base_image_path = Column(String(500), nullable=False)
    os_image_id = Column(Integer, ForeignKey("os_images.id"), nullable=True)  # Reference to OS image
    
    # Template metadata
    tags = Column(Text, nullable=True)  # JSON array of tags
    public = Column(Boolean, nullable=False, default=False)
    
    # New fields for enhanced template system
    packages = Column(Text, nullable=True)  # JSON array of package names
    cloud_init_config = Column(Text, nullable=True)  # Cloud-init user data
    image_source = Column(String(1000), nullable=True)  # Source URL or path for OS image
    image_checksum = Column(String(64), nullable=True)  # SHA256 checksum
    image_format = Column(String(20), nullable=False, default="qcow2")  # Image format
    startup_scripts = Column(Text, nullable=True)  # JSON array of startup script paths
    network_config = Column(Text, nullable=True)  # JSON network configuration presets
    security_hardening = Column(Text, nullable=True)  # JSON security hardening options
    
    # Version history
    version_history = Column(Text, nullable=True)  # JSON array of version changes
    
    # Ownership and timestamps
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    created_by_user = relationship("User", back_populates="created_templates")
    os_image = relationship("OSImage", back_populates="templates")
    
    def __repr__(self):
        return f"<VMTemplate(id={self.id}, name='{self.name}', os_type='{self.os_type}')>"
    
    @property
    def memory_gb(self) -> float:
        """Get memory in GB."""
        return self.memory_mb / 1024.0 if self.memory_mb else 0.0
    
    def to_vm_dict(self) -> dict:
        """Convert template to VM creation parameters."""
        return {
            "cpu_cores": self.cpu_cores,
            "memory_mb": self.memory_mb,
            "disk_gb": self.disk_gb,
            "os_type": self.os_type,
            "os_version": self.os_version,
            "base_image_path": self.base_image_path
        }
    
    def get_packages_list(self) -> list:
        """Get packages as a list."""
        if not self.packages:
            return []
        try:
            import json
            return json.loads(self.packages)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_packages_list(self, packages: list):
        """Set packages from a list."""
        import json
        self.packages = json.dumps(packages) if packages else None
    
    def get_startup_scripts_list(self) -> list:
        """Get startup scripts as a list."""
        if not self.startup_scripts:
            return []
        try:
            import json
            return json.loads(self.startup_scripts)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_startup_scripts_list(self, scripts: list):
        """Set startup scripts from a list."""
        import json
        self.startup_scripts = json.dumps(scripts) if scripts else None
    
    def get_network_config_dict(self) -> dict:
        """Get network config as a dict."""
        if not self.network_config:
            return {}
        try:
            import json
            return json.loads(self.network_config)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_network_config_dict(self, config: dict):
        """Set network config from a dict."""
        import json
        self.network_config = json.dumps(config) if config else None
    
    def get_security_hardening_dict(self) -> dict:
        """Get security hardening as a dict."""
        if not self.security_hardening:
            return {}
        try:
            import json
            return json.loads(self.security_hardening)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_security_hardening_dict(self, config: dict):
        """Set security hardening from a dict."""
        import json
        self.security_hardening = json.dumps(config) if config else None