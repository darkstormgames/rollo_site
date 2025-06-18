"""Health check API endpoints."""
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from core.config import settings
from core.logging import get_logger
from models.base import DatabaseSession

logger = get_logger("health")


class HealthResponse:
    """Health check response model."""
    def __init__(self, status: str, timestamp: datetime, version: str, service: str, checks: Dict[str, Any] = None):
        self.status = status
        self.timestamp = timestamp
        self.version = version
        self.service = service
        self.checks = checks or {}
    
    def dict(self):
        return {
            "status": self.status,
            "timestamp": self.timestamp.isoformat(),
            "version": self.version,
            "service": self.service,
            "checks": self.checks
        }


def create_health_router():
    """Create health check FastAPI router."""
    router = APIRouter()
    
    def check_database() -> str:
        """Check database connectivity."""
        try:
            with DatabaseSession.get_db() as db:
                result = db.execute(text("SELECT 1")).scalar()
                return "healthy" if result == 1 else "unhealthy"
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return "unhealthy"
    
    @router.get("/health")
    def health_check():
        """
        Perform a basic health check.
        
        Returns:
            dict: Service health status and metadata
        """
        logger.info("Health check requested")
        
        # Perform health checks
        checks = {
            "api": "healthy",
            "database": check_database(),
            "libvirt": "not_implemented",   # TODO: Add libvirt connection check
        }
        
        # Determine overall status
        overall_status = "healthy" if all(c in ["healthy", "not_implemented"] for c in checks.values()) else "unhealthy"
        
        response = HealthResponse(
            status=overall_status,
            timestamp=datetime.utcnow(),
            version=settings.api_version,
            service=settings.api_title,
            checks=checks
        )
        return response.dict()

    @router.get("/health/ready")
    def readiness_check():
        """
        Check if the service is ready to serve requests.
        
        Returns:
            dict: Readiness status
        """
        logger.info("Readiness check requested")
        db_status = check_database()
        status = "ready" if db_status == "healthy" else "not_ready"
        return {"status": status, "database": db_status}

    @router.get("/health/live")
    def liveness_check():
        """
        Check if the service is alive.
        
        Returns:
            dict: Liveness status
        """
        logger.info("Liveness check requested")
        return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}
    
    return router