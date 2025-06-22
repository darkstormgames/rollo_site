"""Database initialization script."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# from models.base import create_tables, drop_tables, DatabaseSession
from models.base import create_tables, drop_tables, DatabaseSession
from passlib.context import CryptContext
from core.logging import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger("db_init")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# All user and role creation logic below is now obsolete due to SSO-based user/role management.
def create_default_roles():
    """Create default roles."""
    # SSO handles roles, no local DB roles needed
    pass


def create_admin_user():
    """Create default admin user."""
    # SSO handles admin user, no local DB admin needed
    pass


def init_database():
    """Initialize database with tables and default data."""
    logger.info("Initializing database...")

    # Create tables
    create_tables()
    logger.info("Database tables created")

    # Create default roles
    create_default_roles()

    # Create admin user
    create_admin_user()

    logger.info("Database initialization completed")


def reset_database():
    """Reset database by dropping and recreating all tables."""
    logger.info("Resetting database...")

    drop_tables()
    logger.info("Dropped all tables")

    init_database()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Database initialization script")
    parser.add_argument("--reset", action="store_true", help="Reset database by dropping all tables")

    args = parser.parse_args()

    if args.reset:
        reset_database()
    else:
        init_database()