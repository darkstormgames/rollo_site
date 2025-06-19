"""ServerMetrics model for time-series metrics data."""

from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class ServerMetrics(Base):
    """ServerMetrics model for time-series metrics data."""
    
    __tablename__ = "server_metrics"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Server reference
    server_id = Column(Integer, ForeignKey("servers.id"), nullable=False)
    
    # Metric details
    metric_name = Column(String(100), nullable=False, index=True)  # e.g., 'cpu_usage', 'memory_usage', 'disk_usage'
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20), nullable=True)  # e.g., 'percent', 'bytes', 'count'
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    server = relationship("Server", back_populates="metrics")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_server_metrics_timestamp', 'server_id', 'metric_name', 'timestamp'),
        Index('idx_server_metrics_lookup', 'server_id', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<ServerMetrics(id={self.id}, server_id={self.server_id}, metric='{self.metric_name}', value={self.metric_value})>"
    
    @classmethod
    def record_metric(cls, server_id: int, metric_name: str, metric_value: float, 
                     metric_unit: str = None):
        """Create a new metric record."""
        return cls(
            server_id=server_id,
            metric_name=metric_name,
            metric_value=metric_value,
            metric_unit=metric_unit
        )
    
    @property
    def formatted_value(self) -> str:
        """Get formatted metric value with unit."""
        if self.metric_unit:
            return f"{self.metric_value} {self.metric_unit}"
        return str(self.metric_value)