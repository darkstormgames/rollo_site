"""Configuration management for VM Service."""
import os
from typing import Optional


class Settings:
    """Application settings loaded from environment variables."""
    
    # API Configuration
    api_title: str = os.getenv("API_TITLE", "VM Management Service")
    api_description: str = os.getenv("API_DESCRIPTION", "FastAPI backend for VM management")
    api_version: str = os.getenv("API_VERSION", "1.0.0")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Server Configuration
    host: str = os.getenv("HOST", "127.0.0.1")
    port: int = int(os.getenv("PORT", "8000"))
    reload: bool = os.getenv("RELOAD", "false").lower() == "true"
    
    # Database Configuration
    database_url: Optional[str] = os.getenv("DATABASE_URL")
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_name: str = os.getenv("DB_NAME", "vm_service")
    db_user: str = os.getenv("DB_USER", "vm_user")
    db_password: str = os.getenv("DB_PASSWORD", "")
    
    # Security Configuration
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # VM Management Configuration
    libvirt_uri: str = os.getenv("LIBVIRT_URI", "qemu:///system")
    vm_storage_path: str = os.getenv("VM_STORAGE_PATH", "/var/lib/libvirt/images")
    
    # Logging Configuration
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_format: str = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # CORS Configuration
    cors_origins: list[str] = os.getenv("CORS_ORIGINS", "http://localhost:4200").split(",")
    cors_credentials: bool = os.getenv("CORS_CREDENTIALS", "true").lower() == "true"
    cors_methods: list[str] = os.getenv("CORS_METHODS", "GET,POST,PUT,DELETE").split(",")
    cors_headers: list[str] = ["*"]

    @property
    def database_dsn(self) -> str:
        """Build database DSN from components if DATABASE_URL not provided."""
        if self.database_url:
            return self.database_url
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


# Global settings instance
settings = Settings()