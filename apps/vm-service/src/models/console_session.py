"""Console session model for VM console access management."""

from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# from models.base import BaseModel
from models.base import Base

class ConsoleSession(Base):
    """Console session model for tracking active VM console connections."""
    
    __tablename__ = "console_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    vm_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    vnc_port = Column(Integer, nullable=True)  # VNC port for this session
    spice_port = Column(Integer, nullable=True)  # SPICE port for this session
    protocol = Column(String(10), nullable=False, default="vnc")  # vnc or spice
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Add foreign key relationships if needed
    # vm = relationship("VM", back_populates="console_sessions")
    # user = relationship("User", back_populates="console_sessions")
    
    @classmethod
    def create_session(cls, vm_id: int, user_id: int, session_token: str, 
                       protocol: str = "vnc", expires_minutes: int = 15):
        """Create a new console session."""
        expires_at = datetime.utcnow() + timedelta(minutes=expires_minutes)
        
        return cls(
            vm_id=vm_id,
            user_id=user_id,
            session_token=session_token,
            protocol=protocol,
            expires_at=expires_at,
            is_active=True
        )
    
    def is_expired(self) -> bool:
        """Check if the session has expired."""
        return datetime.utcnow() > self.expires_at
    
    def extend_session(self, minutes: int = 15):
        """Extend the session expiration time."""
        self.expires_at = datetime.utcnow() + timedelta(minutes=minutes)
        self.updated_at = datetime.utcnow()
    
    def terminate(self):
        """Terminate the session."""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert session to dictionary."""
        return {
            "id": self.id,
            "vm_id": self.vm_id,
            "user_id": self.user_id,
            "session_token": self.session_token,
            "protocol": self.protocol,
            "vnc_port": self.vnc_port,
            "spice_port": self.spice_port,
            "is_active": self.is_active,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }