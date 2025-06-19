"""Configuration management for VM Agent."""

import os
from typing import Optional, Dict, Any
from pydantic import BaseSettings, Field


class AgentConfig(BaseSettings):
    """Agent configuration settings."""
    
    # Agent identification
    agent_id: Optional[str] = Field(default=None, description="Unique agent identifier")
    agent_name: str = Field(default="vm-agent", description="Agent display name")
    
    # Backend communication
    backend_url: str = Field(default="https://localhost:8000", description="Main backend service URL")
    api_timeout: int = Field(default=30, description="API request timeout in seconds")
    
    # Security
    agent_token: Optional[str] = Field(default=None, description="Agent authentication token")
    ssl_verify: bool = Field(default=True, description="Verify SSL certificates")
    ssl_cert_path: Optional[str] = Field(default=None, description="Path to SSL certificate")
    ssl_key_path: Optional[str] = Field(default=None, description="Path to SSL private key")
    
    # Libvirt connection
    libvirt_uri: str = Field(default="qemu:///system", description="Libvirt connection URI")
    
    # Monitoring
    metrics_interval: int = Field(default=60, description="Metrics collection interval in seconds")
    heartbeat_interval: int = Field(default=30, description="Heartbeat interval in seconds")
    
    # Retry logic
    retry_attempts: int = Field(default=3, description="Number of retry attempts for failed operations")
    retry_backoff: float = Field(default=2.0, description="Exponential backoff multiplier")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Optional[str] = Field(default=None, description="Log file path")
    
    # Agent settings
    auto_register: bool = Field(default=True, description="Auto-register with backend on startup")
    update_check_interval: int = Field(default=3600, description="Update check interval in seconds")
    
    class Config:
        env_file = ".env"
        env_prefix = "AGENT_"
        case_sensitive = False


def load_config() -> AgentConfig:
    """Load agent configuration from environment variables and .env file."""
    return AgentConfig()


def get_agent_id() -> str:
    """Get or generate agent ID."""
    config = load_config()
    
    if config.agent_id:
        return config.agent_id
    
    # Generate agent ID from hostname and MAC address
    import socket
    import uuid
    
    hostname = socket.gethostname()
    mac = hex(uuid.getnode()).replace('0x', '').upper()
    agent_id = f"{hostname}-{mac}"
    
    return agent_id


def validate_config(config: AgentConfig) -> Dict[str, Any]:
    """Validate agent configuration and return validation results."""
    issues = []
    warnings = []
    
    # Check required settings
    if not config.backend_url:
        issues.append("Backend URL is required")
    
    if not config.libvirt_uri:
        issues.append("Libvirt URI is required")
    
    # Check optional settings
    if config.ssl_verify and not config.ssl_cert_path:
        warnings.append("SSL verification enabled but no certificate path provided")
    
    if config.metrics_interval < 10:
        warnings.append("Metrics interval is very short, may impact performance")
    
    if config.heartbeat_interval < 10:
        warnings.append("Heartbeat interval is very short, may impact performance")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings
    }