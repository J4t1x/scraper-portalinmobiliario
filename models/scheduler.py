"""
Scheduler models for APScheduler integration with PostgreSQL.

This module defines SQLAlchemy models for tracking scheduler state
and job executions.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, DateTime, Integer, Text, JSON
from database import Base


class SchedulerExecution(Base):
    """
    Model for tracking individual job executions.
    
    Attributes:
        id: Primary key (UUID string)
        job_id: APScheduler job ID
        job_name: Human-readable job name
        start_time: Timestamp when job started
        end_time: Timestamp when job ended
        status: Execution status (success, failed, running, missed)
        properties_scraped: Number of properties scraped
        pages_processed: Number of pages processed
        error_message: Error message if failed
        duration: Duration in seconds
        metadata: JSON with job parameters
    """
    
    __tablename__ = 'scheduler_executions'
    
    id = Column(String(36), primary_key=True)
    job_id = Column(String(200), nullable=False, index=True)
    job_name = Column(String(200), nullable=False)
    
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=True)
    
    status = Column(String(50), nullable=False, index=True)  # success, failed, running, missed
    
    properties_scraped = Column(Integer, default=0)
    pages_processed = Column(Integer, default=0)
    
    error_message = Column(Text, nullable=True)
    duration = Column(Integer, nullable=True)  # Duration in seconds
    
    metadata = Column(JSON, nullable=True)
    
    def __repr__(self) -> str:
        return f"<SchedulerExecution(id={self.id}, job_id='{self.job_id}', status='{self.status}')>"
    
    def to_dict(self) -> dict:
        """Convert execution to dictionary representation."""
        return {
            'id': self.id,
            'job_id': self.job_id,
            'job_name': self.job_name,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status,
            'properties_scraped': self.properties_scraped,
            'pages_processed': self.pages_processed,
            'error_message': self.error_message,
            'duration': self.duration,
            'metadata': self.metadata
        }


class SchedulerState(Base):
    """
    Model for tracking overall scheduler state.
    
    Attributes:
        id: Primary key (UUID string)
        scheduler_id: Unique identifier for this scheduler instance
        status: Scheduler status (running, paused, stopped)
        last_heartbeat: Timestamp of last heartbeat
        start_time: Timestamp when scheduler started
        total_jobs_executed: Counter for total job executions
    """
    
    __tablename__ = 'scheduler_state'
    
    id = Column(String(36), primary_key=True)
    scheduler_id = Column(String(200), nullable=False, unique=True, index=True)
    
    status = Column(String(50), nullable=False, default='stopped')  # running, paused, stopped
    
    last_heartbeat = Column(DateTime, nullable=True)
    start_time = Column(DateTime, nullable=True)
    
    total_jobs_executed = Column(Integer, default=0)
    
    def __repr__(self) -> str:
        return f"<SchedulerState(id={self.id}, scheduler_id='{self.scheduler_id}', status='{self.status}')>"
    
    def to_dict(self) -> dict:
        """Convert state to dictionary representation."""
        return {
            'id': self.id,
            'scheduler_id': self.scheduler_id,
            'status': self.status,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'total_jobs_executed': self.total_jobs_executed
        }
