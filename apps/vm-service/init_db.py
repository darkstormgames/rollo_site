"""Database initialization script."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from models.base import create_tables, drop_tables, DatabaseSession
from models import User, Role
from passlib.context import CryptContext
from core.logging import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger("db_init")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_default_roles():
    """Create default roles."""
    with DatabaseSession.get_db() as db:
        # Check if roles already exist
        existing_roles = db.query(Role).count()
        if existing_roles > 0:
            logger.info("Roles already exist, skipping creation")
            return
        
        # Create default roles
        roles = [
            Role(
                name="admin",
                permissions={
                    "servers.create": True,
                    "servers.read": True,
                    "servers.update": True,
                    "servers.delete": True,
                    "vms.create": True,
                    "vms.read": True,
                    "vms.update": True,
                    "vms.delete": True,
                    "users.manage": True,
                    "audit.read": True
                }
            ),
            Role(
                name="user",
                permissions={
                    "servers.read": True,
                    "vms.create": True,
                    "vms.read": True,
                    "vms.update": True,
                    "vms.delete": True
                }
            ),
            Role(
                name="viewer",
                permissions={
                    "servers.read": True,
                    "vms.read": True
                }
            )
        ]
        
        for role in roles:
            db.add(role)
        
        db.commit()
        logger.info(f"Created {len(roles)} default roles")


def create_admin_user():
    """Create default admin user."""
    with DatabaseSession.get_db() as db:
        # Check if admin user already exists
        admin_user = db.query(User).filter(User.username == "admin").first()
        if admin_user:
            logger.info("Admin user already exists")
            return
        
        # Get admin role
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if not admin_role:
            logger.error("Admin role not found. Create roles first.")
            return
        
        # Create admin user
        admin_user = User(
            username="admin",
            email="admin@vm-service.local",
            password_hash=pwd_context.hash("admin123"),
            is_active=True
        )
        admin_user.roles.append(admin_role)
        
        db.add(admin_user)
        db.commit()
        logger.info("Created admin user (username: admin, password: admin123)")


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