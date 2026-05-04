"""
Scraper Execution model for tracking scraper runs and logs.

This module defines SQLAlchemy models for tracking scraper executions,
their status, metrics, and logs.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, DateTime, Integer, Text, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class ScraperExecution(Base):
    """
    Model for tracking individual scraper executions.
    
    Attributes:
        id: Primary key (UUID string)
        execution_id: Unique identifier for this execution
        operacion: Operation type (venta, arriendo, etc.)
        tipo: Property type (departamento, casa, etc.)
        start_time: Timestamp when scraping started
        end_time: Timestamp when scraping ended
        status: Execution status (running, completed, failed, cancelled)
        properties_scraped: Number of properties scraped
        properties_new: Number of new properties
        properties_updated: Number of updated properties
        pages_processed: Number of pages processed
        error_message: Error message if failed
        duration: Duration in seconds
        parameters: JSON with scraper parameters
        triggered_by: How was it triggered (manual, scheduled, api)
        user_id: User who triggered (for manual executions)
    """
    
    __tablename__ = 'scraper_executions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    execution_id = Column(String(36), unique=True, nullable=False, index=True)
    
    # Scraper parameters
    operacion = Column(String(50), nullable=False, index=True)
    tipo = Column(String(50), nullable=False, index=True)
    
    # Timing
    start_time = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    end_time = Column(DateTime, nullable=True)
    duration = Column(Integer, nullable=True)  # Duration in seconds
    
    # Status
    status = Column(String(50), nullable=False, default='running', index=True)
    # Possible values: running, completed, failed, cancelled
    
    # Metrics
    properties_scraped = Column(Integer, default=0)
    properties_new = Column(Integer, default=0)
    properties_updated = Column(Integer, default=0)
    pages_processed = Column(Integer, default=0)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    
    # Metadata
    parameters = Column(JSON, nullable=True)
    triggered_by = Column(String(50), nullable=True)  # manual, scheduled, api
    user_id = Column(String(100), nullable=True)
    
    # Relationships
    logs = relationship(
        "ScraperLog",
        back_populates="execution",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="ScraperLog.timestamp"
    )
    
    def __repr__(self) -> str:
        return f"<ScraperExecution(id={self.id}, execution_id='{self.execution_id}', status='{self.status}')>"
    
    def to_dict(self) -> dict:
        """Convert execution to dictionary representation."""
        return {
            'id': self.id,
            'execution_id': self.execution_id,
            'operacion': self.operacion,
            'tipo': self.tipo,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'status': self.status,
            'properties_scraped': self.properties_scraped,
            'properties_new': self.properties_new,
            'properties_updated': self.properties_updated,
            'pages_processed': self.pages_processed,
            'error_message': self.error_message,
            'parameters': self.parameters,
            'triggered_by': self.triggered_by,
            'user_id': self.user_id
        }


class ScraperLog(Base):
    """
    Model for storing individual log entries from scraper executions.
    
    Attributes:
        id: Primary key
        execution_id: Foreign key to ScraperExecution
        timestamp: When the log was created
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        message: Log message
        source: Source of the log (scraper, validator, exporter, etc.)
        metadata: Additional JSON metadata
    """
    
    __tablename__ = 'scraper_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    execution_id = Column(String(36), ForeignKey('scraper_executions.execution_id'), nullable=False, index=True)
    
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    level = Column(String(20), nullable=False, index=True)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    message = Column(Text, nullable=False)
    source = Column(String(100), nullable=True)  # scraper, validator, exporter, etc.
    log_metadata = Column(JSON, nullable=True)
    
    # Relationships
    execution = relationship("ScraperExecution", back_populates="logs")
    
    def __repr__(self) -> str:
        return f"<ScraperLog(id={self.id}, level='{self.level}', message='{self.message[:50]}...')>"
    
    def to_dict(self) -> dict:
        """Convert log to dictionary representation."""
        return {
            'id': self.id,
            'execution_id': self.execution_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'level': self.level,
            'message': self.message,
            'source': self.source,
            'log_metadata': self.log_metadata
        }
