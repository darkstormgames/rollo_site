"""FastAPI application for VM management."""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from core.config import settings
from core.logging import setup_logging, get_logger
from core.rate_limit import RateLimitMiddleware
from models.base import DatabaseSession, create_tables
from api.health import create_health_router
from api.auth import router as auth_router
from api.example import router as example_router

# Setup logging
setup_logging()
logger = get_logger("app")

# Create FastAPI application
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    debug=settings.debug
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers
)

# Add rate limiting middleware
app.add_middleware(
    RateLimitMiddleware,
    calls_per_minute=settings.rate_limit_per_minute
)

# Add routers
health_router = create_health_router()
app.include_router(health_router, prefix="/api/v1", tags=["health"])
app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
app.include_router(example_router, prefix="/api/example", tags=["examples"])


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info(f"🚀 {settings.api_title} v{settings.api_version} starting...")
    logger.info(f"📊 Debug mode: {settings.debug}")
    logger.info(f"🔗 Database: {settings.database_dsn.split('@')[-1] if '@' in settings.database_dsn else settings.database_dsn}")
    
    # Create database tables
    try:
        create_tables()
        logger.info("✅ Database tables created/verified")
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("🛑 VM Management Service shutting down...")


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": settings.api_title,
        "version": settings.api_version,
        "docs": "/docs",
        "health": "/api/v1/health",
        "status": "running"
    }


# Dependency to get database session
def get_db() -> Session:
    """Database dependency for dependency injection."""
    return DatabaseSession.get_session()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload
    )