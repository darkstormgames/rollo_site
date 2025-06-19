"""Database base configuration and session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator

from core.config import settings

# Create declarative base
Base = declarative_base()

# Configure engine based on database type
if settings.database_dsn.startswith("sqlite"):
    # SQLite configuration for testing
    engine = create_engine(
        settings.database_dsn,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=settings.debug
    )
else:
    # PostgreSQL/MySQL configuration for production
    engine = create_engine(
        settings.database_dsn,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=settings.debug
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class DatabaseSession:
    """Database session management."""
    
    @staticmethod
    @contextmanager
    def get_db() -> Generator:
        """Get database session with automatic cleanup."""
        db = SessionLocal()
        try:
            yield db
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    @staticmethod
    def get_session():
        """Get a database session (for dependency injection)."""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()


def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """Drop all database tables."""
    Base.metadata.drop_all(bind=engine)