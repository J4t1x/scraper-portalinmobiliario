"""
Scheduler module for automated scraping jobs using APScheduler.

This module provides a ScraperScheduler class that manages periodic
scraping jobs with PostgreSQL persistence, concurrency control, and
detailed execution logging.
"""

import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED
from apscheduler.jobstores.base import JobLookupError

from database import get_session, Session
from models import SchedulerExecution, SchedulerState
from config import Config
from logger_config import get_logger

logger = get_logger(__name__)


class ScraperScheduler:
    """
    Scheduler for automated scraping jobs with APScheduler.
    
    Features:
    - PostgreSQL job store for persistence
    - Concurrency control (max concurrent jobs)
    - Detailed execution logging
    - Automatic recovery on restart
    - Heartbeat monitoring
    """
    
    def __init__(self, database_url: Optional[str] = None, scheduler_id: Optional[str] = None):
        """
        Initialize the scheduler.
        
        Args:
            database_url: PostgreSQL connection URL. If None, uses Config.DATABASE_URL
            scheduler_id: Unique identifier for this scheduler instance
        """
        if database_url is None:
            database_url = Config.DATABASE_URL
        
        if not database_url:
            raise ValueError("DATABASE_URL is not configured")
        
        self.scheduler_id = scheduler_id or f"scraper-scheduler-{uuid.uuid4()}"
        
        # Configure job store with PostgreSQL
        jobstores = {
            'default': SQLAlchemyJobStore(url=database_url, tablename='apscheduler_jobs')
        }
        
        # Configure executors for concurrent job execution
        executors = {
            'default': ThreadPoolExecutor(max_workers=20),
            'processpool': ProcessPoolExecutor(max_workers=5)
        }
        
        # Configure job defaults
        job_defaults = {
            'coalesce': True,  # Combine missed executions into one
            'max_instances': 1,  # Prevent job overlap
            'misfire_grace_time': 300,  # 5 minutes grace for missed jobs
            'replace_existing': True  # Replace job if it already exists
        }
        
        # Create scheduler
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='America/Santiago'
        )
        
        # Add event listeners for execution tracking
        self.scheduler.add_listener(
            self._job_executed_listener,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_MISSED
        )
        
        logger.info(f"Scheduler initialized with ID: {self.scheduler_id}")
    
    def start(self) -> None:
        """Start the scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            self._update_scheduler_state('running')
            logger.info(f"Scheduler started: {self.scheduler_id}")
        else:
            logger.warning(f"Scheduler already running: {self.scheduler_id}")
    
    def shutdown(self, wait: bool = True) -> None:
        """
        Shutdown the scheduler.
        
        Args:
            wait: Wait for running jobs to complete
        """
        if self.scheduler.running:
            self.scheduler.shutdown(wait=wait)
            self._update_scheduler_state('stopped')
            logger.info(f"Scheduler stopped: {self.scheduler_id}")
    
    def pause(self) -> None:
        """Pause the scheduler (jobs won't execute but scheduler stays running)."""
        if self.scheduler.running:
            self.scheduler.pause()
            self._update_scheduler_state('paused')
            logger.info(f"Scheduler paused: {self.scheduler_id}")
    
    def resume(self) -> None:
        """Resume the scheduler."""
        if self.scheduler.state == 2:  # STATE_PAUSED
            self.scheduler.resume()
            self._update_scheduler_state('running')
            logger.info(f"Scheduler resumed: {self.scheduler_id}")
    
    def add_job(
        self,
        func,
        job_id: str,
        trigger: str = 'interval',
        **trigger_args
    ) -> None:
        """
        Add a job to the scheduler.
        
        Args:
            func: Function to execute
            job_id: Unique job identifier
            trigger: Type of trigger ('interval', 'cron', 'date')
            **trigger_args: Arguments for the trigger (e.g., hours=1 for interval)
        """
        try:
            self.scheduler.add_job(
                func,
                trigger=trigger,
                id=job_id,
                **trigger_args
            )
            logger.info(f"Job added: {job_id} with trigger {trigger}")
        except Exception as e:
            logger.error(f"Failed to add job {job_id}: {e}")
            raise
    
    def remove_job(self, job_id: str) -> bool:
        """
        Remove a job from the scheduler.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if job was removed, False if not found
        """
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Job removed: {job_id}")
            return True
        except JobLookupError:
            logger.warning(f"Job not found: {job_id}")
            return False
        except Exception as e:
            logger.error(f"Failed to remove job {job_id}: {e}")
            raise
    
    def pause_job(self, job_id: str) -> bool:
        """
        Pause a specific job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if job was paused, False if not found
        """
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"Job paused: {job_id}")
            return True
        except JobLookupError:
            logger.warning(f"Job not found: {job_id}")
            return False
    
    def resume_job(self, job_id: str) -> bool:
        """
        Resume a paused job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if job was resumed, False if not found
        """
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"Job resumed: {job_id}")
            return True
        except JobLookupError:
            logger.warning(f"Job not found: {job_id}")
            return False
    
    def get_jobs(self) -> List[Dict[str, Any]]:
        """
        Get all configured jobs.
        
        Returns:
            List of job dictionaries
        """
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger),
                'max_instances': job.max_instances
            })
        return jobs
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific job by ID.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job dictionary or None if not found
        """
        try:
            job = self.scheduler.get_job(job_id)
            return {
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger),
                'max_instances': job.max_instances
            }
        except JobLookupError:
            return None
    
    def get_executions(
        self,
        job_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get execution history from database.
        
        Args:
            job_id: Filter by job ID (optional)
            limit: Maximum number of executions to return
            
        Returns:
            List of execution dictionaries
        """
        with get_session() as session:
            query = session.query(SchedulerExecution)
            
            if job_id:
                query = query.filter(SchedulerExecution.job_id == job_id)
            
            executions = query.order_by(
                SchedulerExecution.start_time.desc()
            ).limit(limit).all()
            
            return [exec.to_dict() for exec in executions]
    
    def get_scheduler_state(self) -> Optional[Dict[str, Any]]:
        """
        Get the current scheduler state from database.
        
        Returns:
            State dictionary or None if not found
        """
        with get_session() as session:
            state = session.query(SchedulerState).filter(
                SchedulerState.scheduler_id == self.scheduler_id
            ).first()
            
            if state:
                return state.to_dict()
            return None
    
    def send_heartbeat(self) -> None:
        """Update the heartbeat timestamp in database."""
        self._update_scheduler_state(None, heartbeat_only=True)
    
    def _job_executed_listener(self, event) -> None:
        """
        Event listener for job execution events.
        
        Args:
            event: APScheduler event
        """
        if event.exception:
            self._log_execution(
                job_id=event.job_id,
                job_name=event.job_id,  # Fallback if name not available
                status='failed',
                error_message=str(event.exception)
            )
            logger.error(f"Job {event.job_id} failed: {event.exception}")
        else:
            self._log_execution(
                job_id=event.job_id,
                job_name=event.job_id,
                status='success',
                result=event.retval
            )
            logger.info(f"Job {event.job_id} executed successfully")
    
    def _log_execution(
        self,
        job_id: str,
        job_name: str,
        status: str,
        error_message: Optional[str] = None,
        result: Optional[Any] = None
    ) -> None:
        """
        Log job execution to database.
        
        Args:
            job_id: Job identifier
            job_name: Job name
            status: Execution status
            error_message: Error message if failed
            result: Result object if successful
        """
        execution_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        # Extract metrics from result if available
        properties_scraped = 0
        pages_processed = 0
        metadata = {}
        
        if result and isinstance(result, dict):
            properties_scraped = result.get('properties_scraped', 0)
            pages_processed = result.get('pages_processed', 0)
            metadata = result.get('metadata', {})
        
        execution = SchedulerExecution(
            id=execution_id,
            job_id=job_id,
            job_name=job_name,
            start_time=start_time,
            end_time=datetime.utcnow(),
            status=status,
            properties_scraped=properties_scraped,
            pages_processed=pages_processed,
            error_message=error_message,
            metadata=metadata
        )
        
        with get_session() as session:
            session.add(execution)
            
            # Update total jobs counter in scheduler state
            state = session.query(SchedulerState).filter(
                SchedulerState.scheduler_id == self.scheduler_id
            ).first()
            
            if state:
                state.total_jobs_executed += 1
                state.last_heartbeat = datetime.utcnow()
    
    def _update_scheduler_state(
        self,
        status: Optional[str] = None,
        heartbeat_only: bool = False
    ) -> None:
        """
        Update scheduler state in database.
        
        Args:
            status: New status (running, paused, stopped)
            heartbeat_only: Only update heartbeat timestamp
        """
        with get_session() as session:
            state = session.query(SchedulerState).filter(
                SchedulerState.scheduler_id == self.scheduler_id
            ).first()
            
            now = datetime.utcnow()
            
            if not state:
                # Create new state record
                state = SchedulerState(
                    id=str(uuid.uuid4()),
                    scheduler_id=self.scheduler_id,
                    status=status or 'running',
                    last_heartbeat=now,
                    start_time=now,
                    total_jobs_executed=0
                )
                session.add(state)
            else:
                # Update existing state
                if not heartbeat_only and status:
                    state.status = status
                state.last_heartbeat = now
                
                if status == 'running' and not state.start_time:
                    state.start_time = now


# Global scheduler instance
_global_scheduler: Optional[ScraperScheduler] = None


def get_scheduler() -> ScraperScheduler:
    """
    Get or create the global scheduler instance.
    
    Returns:
        ScraperScheduler instance
    """
    global _global_scheduler
    
    if _global_scheduler is None:
        _global_scheduler = ScraperScheduler()
    
    return _global_scheduler


def shutdown_global_scheduler() -> None:
    """Shutdown the global scheduler instance."""
    global _global_scheduler
    
    if _global_scheduler is not None:
        _global_scheduler.shutdown()
        _global_scheduler = None
