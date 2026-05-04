"""
Execution tracker for scraper runs.

This module provides utilities to track scraper executions and logs in the database.
"""

import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from contextlib import contextmanager
from database import session_scope
from models import ScraperExecutionModel, ScraperLog

logger = logging.getLogger(__name__)


class ExecutionTracker:
    """
    Tracker for scraper executions.
    
    This class manages the lifecycle of a scraper execution:
    - Creating execution records
    - Updating execution status and metrics
    - Logging execution events
    """
    
    def __init__(self, execution_id: Optional[str] = None):
        """
        Initialize execution tracker.
        
        Args:
            execution_id: Existing execution ID to resume tracking, or None to create new
        """
        self.execution_id = execution_id or str(uuid.uuid4())
        self.execution = None
    
    def start_execution(
        self,
        operacion: str,
        tipo: str,
        triggered_by: str = 'manual',
        user_id: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start a new scraper execution.
        
        Args:
            operacion: Operation type (venta, arriendo, etc.)
            tipo: Property type (departamento, casa, etc.)
            triggered_by: How was it triggered (manual, scheduled, api)
            user_id: User who triggered the execution
            parameters: Additional parameters
            
        Returns:
            Execution ID
        """
        try:
            with session_scope() as session:
                execution = ScraperExecutionModel(
                    execution_id=self.execution_id,
                    operacion=operacion,
                    tipo=tipo,
                    start_time=datetime.utcnow(),
                    status='running',
                    triggered_by=triggered_by,
                    user_id=user_id,
                    parameters=parameters or {}
                )
                session.add(execution)
                session.commit()
                
                self.execution = execution
                logger.info(f"Started execution {self.execution_id} for {operacion} {tipo}")
                
                return self.execution_id
        except Exception as e:
            logger.error(f"Error starting execution: {e}")
            raise
    
    def update_metrics(
        self,
        properties_scraped: Optional[int] = None,
        properties_new: Optional[int] = None,
        properties_updated: Optional[int] = None,
        pages_processed: Optional[int] = None
    ):
        """
        Update execution metrics.
        
        Args:
            properties_scraped: Total properties scraped
            properties_new: New properties added
            properties_updated: Properties updated
            pages_processed: Pages processed
        """
        try:
            with session_scope() as session:
                execution = session.query(ScraperExecutionModel).filter(
                    ScraperExecutionModel.execution_id == self.execution_id
                ).first()
                
                if not execution:
                    logger.warning(f"Execution {self.execution_id} not found for metrics update")
                    return
                
                if properties_scraped is not None:
                    execution.properties_scraped = properties_scraped
                if properties_new is not None:
                    execution.properties_new = properties_new
                if properties_updated is not None:
                    execution.properties_updated = properties_updated
                if pages_processed is not None:
                    execution.pages_processed = pages_processed
                
                session.commit()
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
    
    def complete_execution(self, status: str = 'completed', error_message: Optional[str] = None):
        """
        Mark execution as completed.
        
        Args:
            status: Final status (completed, failed, cancelled)
            error_message: Error message if failed
        """
        try:
            with session_scope() as session:
                execution = session.query(ScraperExecutionModel).filter(
                    ScraperExecutionModel.execution_id == self.execution_id
                ).first()
                
                if not execution:
                    logger.warning(f"Execution {self.execution_id} not found for completion")
                    return
                
                execution.end_time = datetime.utcnow()
                execution.status = status
                
                if execution.start_time:
                    duration = (execution.end_time - execution.start_time).total_seconds()
                    execution.duration = int(duration)
                
                if error_message:
                    execution.error_message = error_message
                
                session.commit()
                logger.info(f"Completed execution {self.execution_id} with status {status}")
        except Exception as e:
            logger.error(f"Error completing execution: {e}")
    
    def log(
        self,
        level: str,
        message: str,
        source: Optional[str] = None,
        log_metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add a log entry to the execution.
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Log message
            source: Source of the log (scraper, validator, etc.)
            log_metadata: Additional metadata
        """
        try:
            with session_scope() as session:
                log_entry = ScraperLog(
                    execution_id=self.execution_id,
                    timestamp=datetime.utcnow(),
                    level=level.upper(),
                    message=message,
                    source=source,
                    log_metadata=log_metadata
                )
                session.add(log_entry)
                session.commit()
        except Exception as e:
            logger.error(f"Error logging to execution: {e}")
    
    def log_info(self, message: str, source: Optional[str] = None, **kwargs):
        """Log INFO level message."""
        self.log('INFO', message, source, kwargs if kwargs else None)
    
    def log_warning(self, message: str, source: Optional[str] = None, **kwargs):
        """Log WARNING level message."""
        self.log('WARNING', message, source, kwargs if kwargs else None)
    
    def log_error(self, message: str, source: Optional[str] = None, **kwargs):
        """Log ERROR level message."""
        self.log('ERROR', message, source, kwargs if kwargs else None)
    
    def log_debug(self, message: str, source: Optional[str] = None, **kwargs):
        """Log DEBUG level message."""
        self.log('DEBUG', message, source, kwargs if kwargs else None)


@contextmanager
def track_execution(
    operacion: str,
    tipo: str,
    triggered_by: str = 'manual',
    user_id: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None
):
    """
    Context manager for tracking a scraper execution.
    
    Usage:
        with track_execution('venta', 'departamento') as tracker:
            # Scraping code
            tracker.log_info("Started scraping")
            tracker.update_metrics(properties_scraped=10)
    
    Args:
        operacion: Operation type
        tipo: Property type
        triggered_by: How was it triggered
        user_id: User who triggered
        parameters: Additional parameters
        
    Yields:
        ExecutionTracker instance
    """
    tracker = ExecutionTracker()
    execution_id = tracker.start_execution(
        operacion=operacion,
        tipo=tipo,
        triggered_by=triggered_by,
        user_id=user_id,
        parameters=parameters
    )
    
    try:
        yield tracker
        tracker.complete_execution(status='completed')
    except Exception as e:
        tracker.log_error(f"Execution failed: {str(e)}", source='tracker')
        tracker.complete_execution(status='failed', error_message=str(e))
        raise
