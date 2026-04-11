"""
Analytics cache model for storing computed metrics.
"""

from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from database import Base


class AnalyticsCache(Base):
    """Cache for analytics metrics."""
    
    __tablename__ = 'analytics_cache'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_name = Column(String(100), unique=True, nullable=False)
    metric_value = Column(JSONB, nullable=False)
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<AnalyticsCache(metric_name={self.metric_name})>"
