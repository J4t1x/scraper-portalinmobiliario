"""
Scheduler job definitions for automated scraping.

This module provides job functions and helpers for creating
scheduled scraping jobs with different configurations.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from scheduler import ScraperScheduler
from logger_config import get_logger

logger = get_logger(__name__)


def create_scraping_job(
    scheduler: ScraperScheduler,
    operacion: str,
    tipo: str,
    schedule_type: str = 'interval',
    **schedule_args
) -> str:
    """
    Create a scraping job with specified schedule.
    
    Args:
        scheduler: ScraperScheduler instance
        operacion: Operation type (venta, arriendo, arriendo-de-temporada)
        tipo: Property type (departamento, casa, oficina, etc.)
        schedule_type: Type of schedule (interval, cron, date)
        **schedule_args: Schedule arguments (e.g., hours=1 for interval)
        
    Returns:
        Job ID
    """
    job_id = f'scrape_{operacion}_{tipo}'
    job_name = f'Scrape {operacion} {tipo}'
    
    # Import run_scraping function to avoid circular imports
    from main import run_scraping
    
    def job_wrapper():
        """Wrapper function for scraping job with error handling and metrics."""
        try:
            logger.info(f"Starting scheduled job: {job_name}")
            
            result = run_scraping(
                operacion=operacion,
                tipo=tipo,
                max_pages=schedule_args.get('max_pages'),
                scrape_details=schedule_args.get('scrape_details', False),
                max_detail_properties=schedule_args.get('max_detail_properties'),
                formato=schedule_args.get('formato', 'txt'),
                verbose=True
            )
            
            # TASK-015-04: Cautiously trigger cache invalidation
            try:
                import requests
                import os
                api_key = os.getenv('API_KEY', 'default-secret-key')
                requests.delete(
                    "http://localhost:5000/api/v2/cache/invalidate",
                    headers={"X-API-KEY": api_key},
                    timeout=2
                )
                logger.debug("Cache de la API invalidado automáticamente tras finalizado el scraper")
            except Exception as e:
                logger.debug(f"No fue posible auto-invalidar caché: {e}")
            
            # Extract metrics from result for scheduler logging
            metrics = {
                'properties_scraped': result.get('properties_scraped', 0) if isinstance(result, dict) else 0,
                'pages_processed': result.get('pages_processed', 0) if isinstance(result, dict) else 0,
                'metadata': {
                    'operacion': operacion,
                    'tipo': tipo,
                    'schedule_type': schedule_type,
                    'schedule_args': schedule_args
                }
            }
            
            logger.info(f"Job completed: {job_name} - {metrics['properties_scraped']} properties, {metrics['pages_processed']} pages")
            return metrics
            
        except Exception as e:
            logger.error(f"Job failed: {job_name} - {e}")
            raise
    
    scheduler.add_job(
        job_wrapper,
        job_id=job_id,
        trigger=schedule_type,
        **schedule_args
    )
    
    logger.info(f"Created job: {job_id} with schedule {schedule_type}")
    return job_id


def setup_default_jobs(scheduler: ScraperScheduler) -> None:
    """
    Setup default scraping jobs as specified in SPEC-012.
    
    Jobs configured:
    - scrape_venta_departamento: Daily at 02:00 AM
    - scrape_arriendo_departamento: Daily at 03:00 AM
    - scrape_venta_casa: Daily at 04:00 AM
    - scrape_arriendo_casa: Daily at 05:00 AM
    - scrape_venta_oficina: Weekly (Monday at 06:00 AM)
    
    Args:
        scheduler: ScraperScheduler instance
    """
    # Job: scrape_venta_departamento - Daily at 02:00 AM
    create_scraping_job(
        scheduler,
        operacion='venta',
        tipo='departamento',
        schedule_type='cron',
        hour=2,
        minute=0,
        max_pages=50,
        scrape_details=True,
        max_detail_properties=100
    )
    
    # Job: scrape_arriendo_departamento - Daily at 03:00 AM
    create_scraping_job(
        scheduler,
        operacion='arriendo',
        tipo='departamento',
        schedule_type='cron',
        hour=3,
        minute=0,
        max_pages=50,
        scrape_details=True,
        max_detail_properties=100
    )
    
    # Job: scrape_venta_casa - Daily at 04:00 AM
    create_scraping_job(
        scheduler,
        operacion='venta',
        tipo='casa',
        schedule_type='cron',
        hour=4,
        minute=0,
        max_pages=30,
        scrape_details=True,
        max_detail_properties=50
    )
    
    # Job: scrape_arriendo_casa - Daily at 05:00 AM
    create_scraping_job(
        scheduler,
        operacion='arriendo',
        tipo='casa',
        schedule_type='cron',
        hour=5,
        minute=0,
        max_pages=30,
        scrape_details=True,
        max_detail_properties=50
    )
    
    # Job: scrape_venta_oficina - Weekly (Monday at 06:00 AM)
    create_scraping_job(
        scheduler,
        operacion='venta',
        tipo='oficina',
        schedule_type='cron',
        day_of_week='mon',
        hour=6,
        minute=0,
        max_pages=20,
        scrape_details=True,
        max_detail_properties=30
    )
    
    logger.info("Default jobs setup completed (SPEC-012)")


def create_custom_job(
    scheduler: ScraperScheduler,
    job_config: Dict[str, Any]
) -> str:
    """
    Create a custom job from configuration dictionary.
    
    Args:
        scheduler: ScraperScheduler instance
        job_config: Job configuration with keys:
            - operacion: Operation type
            - tipo: Property type
            - schedule_type: interval, cron, or date
            - schedule_args: Schedule-specific arguments
            - max_pages: Optional max pages
            - scrape_details: Optional scrape details flag
            - max_detail_properties: Optional max detail properties
            - formato: Export format (default: txt)
            
    Returns:
        Job ID
    """
    job_id = job_config.get('job_id') or f"scrape_{job_config['operacion']}_{job_config['tipo']}"
    
    # Extract schedule arguments
    schedule_type = job_config['schedule_type']
    schedule_args = job_config.get('schedule_args', {})
    
    # Extract scraping parameters
    scraping_params = {
        'max_pages': job_config.get('max_pages'),
        'scrape_details': job_config.get('scrape_details', False),
        'max_detail_properties': job_config.get('max_detail_properties'),
        'formato': job_config.get('formato', 'txt')
    }
    
    # Merge schedule args with scraping params
    schedule_args.update(scraping_params)
    
    return create_scraping_job(
        scheduler,
        operacion=job_config['operacion'],
        tipo=job_config['tipo'],
        schedule_type=schedule_type,
        **schedule_args
    )


def create_cleanup_job(scheduler: ScraperScheduler, days_to_keep: int = 30) -> str:
    """
    Create a job to clean up old execution logs.
    
    Args:
        scheduler: ScraperScheduler instance
        days_to_keep: Number of days to keep execution logs
        
    Returns:
        Job ID
    """
    job_id = 'cleanup_old_executions'
    
    def cleanup_wrapper():
        """Wrapper function for cleanup job."""
        from database import get_session
        from models import SchedulerExecution
        from datetime import timedelta
        
        try:
            logger.info("Starting cleanup of old executions")
            
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            with get_session() as session:
                deleted = session.query(SchedulerExecution).filter(
                    SchedulerExecution.start_time < cutoff_date
                ).delete()
                
                session.commit()
            
            logger.info(f"Cleanup completed: {deleted} executions deleted")
            return {'deleted': deleted}
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            raise
    
    scheduler.add_job(
        cleanup_wrapper,
        job_id=job_id,
        trigger='cron',
        day=1,  # First day of month
        hour=3,  # 3 AM
        minute=0
    )
    
    logger.info(f"Created cleanup job: {job_id} (keep {days_to_keep} days)")
    return job_id


def create_data_cleanup_job(scheduler: ScraperScheduler, days_to_keep: int = 90) -> str:
    """
    Create a job to clean up old output data files and obsolete entries.
    SPEC-013-01
    """
    job_id = 'data_cleanup_job'
    
    def data_cleanup_wrapper():
        import os
        from datetime import datetime, timedelta
        from config import Config
        try:
            logger.info(f"Starting cleanup of old data files (>{days_to_keep} days)")
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            deleted_files = 0
            
            output_dir = getattr(Config, 'OUTPUT_DIR', 'output')
            if os.path.exists(output_dir):
                for filename in os.listdir(output_dir):
                    filepath = os.path.join(output_dir, filename)
                    if os.path.isfile(filepath):
                        mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                        if mtime < cutoff_date:
                            os.remove(filepath)
                            deleted_files += 1
                            
            logger.info(f"Data cleanup completed: {deleted_files} files deleted")
            return {'deleted_files': deleted_files}
        except Exception as e:
            logger.error(f"Data cleanup failed: {e}")
            raise

    scheduler.add_job(
        data_cleanup_wrapper,
        job_id=job_id,
        trigger='cron',
        day_of_week='sun',
        hour=2,
        minute=0
    )
    logger.info(f"Created data cleanup job: {job_id}")
    return job_id


def create_log_maintenance_job(scheduler: ScraperScheduler) -> str:
    """
    Create a job to manually trigger log rotation or old log cleanup.
    SPEC-013-02
    """
    job_id = 'log_maintenance_job'
    
    def log_maintenance_wrapper():
        try:
            logger.info("Starting log maintenance")
            from logger_config import setup_logging
            # Setup logging also calls clean_old_logs internally
            log_config = setup_logging()
            log_config.clean_old_logs()
            logger.info("Log maintenance completed")
            return {'status': 'success'}
        except Exception as e:
            logger.error(f"Log maintenance failed: {e}")
            raise

    scheduler.add_job(
        log_maintenance_wrapper,
        job_id=job_id,
        trigger='cron',
        hour=0,
        minute=0
    )
    logger.info(f"Created log maintenance job: {job_id}")
    return job_id


def create_backup_job(scheduler: ScraperScheduler) -> str:
    """
    Create a job to backup outputs and db instances.
    SPEC-013-03
    """
    job_id = 'backup_job'
    
    def backup_wrapper():
        import os
        import subprocess
        from datetime import datetime
        try:
            logger.info("Starting backup job")
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = 'backups'
            os.makedirs(backup_dir, exist_ok=True)
            
            # Backup output directory into a tarball
            backup_filename = f"{backup_dir}/output_backup_{timestamp}.tar.gz"
            if os.path.exists('output'):
                subprocess.run(['tar', '-czf', backup_filename, 'output'], check=True)
            
            logger.info(f"Backup completed: {backup_filename}")
            return {'backup_file': backup_filename}
        except Exception as e:
            logger.error(f"Backup job failed: {e}")
            raise

    scheduler.add_job(
        backup_wrapper,
        job_id=job_id,
        trigger='cron',
        day_of_week='sun',
        hour=4,
        minute=0
    )
    logger.info(f"Created backup job: {job_id}")
    return job_id


def setup_maintenance_jobs(scheduler: ScraperScheduler) -> None:
    """Register all maintenance jobs onto the scheduler."""
    create_cleanup_job(scheduler)
    create_data_cleanup_job(scheduler)
    create_log_maintenance_job(scheduler)
    create_backup_job(scheduler)
    logger.info("Maintenance jobs setup completed")


# Predefined job configurations (SPEC-012)
PREDEFINED_JOBS = {
    'venta_departamento_daily': {
        'operacion': 'venta',
        'tipo': 'departamento',
        'schedule_type': 'cron',
        'schedule_args': {'hour': 2, 'minute': 0},
        'max_pages': 50,
        'scrape_details': True,
        'max_detail_properties': 100
    },
    'arriendo_departamento_daily': {
        'operacion': 'arriendo',
        'tipo': 'departamento',
        'schedule_type': 'cron',
        'schedule_args': {'hour': 3, 'minute': 0},
        'max_pages': 50,
        'scrape_details': True,
        'max_detail_properties': 100
    },
    'venta_casa_daily': {
        'operacion': 'venta',
        'tipo': 'casa',
        'schedule_type': 'cron',
        'schedule_args': {'hour': 4, 'minute': 0},
        'max_pages': 30,
        'scrape_details': True,
        'max_detail_properties': 50
    },
    'arriendo_casa_daily': {
        'operacion': 'arriendo',
        'tipo': 'casa',
        'schedule_type': 'cron',
        'schedule_args': {'hour': 5, 'minute': 0},
        'max_pages': 30,
        'scrape_details': True,
        'max_detail_properties': 50
    },
    'venta_oficina_weekly': {
        'operacion': 'venta',
        'tipo': 'oficina',
        'schedule_type': 'cron',
        'schedule_args': {'day_of_week': 'mon', 'hour': 6, 'minute': 0},
        'max_pages': 20,
        'scrape_details': True,
        'max_detail_properties': 30
    }
}


def setup_predefined_job(scheduler: ScraperScheduler, job_name: str) -> str:
    """
    Setup a predefined job by name.
    
    Args:
        scheduler: ScraperScheduler instance
        job_name: Name from PREDEFINED_JOBS
        
    Returns:
        Job ID
    """
    if job_name not in PREDEFINED_JOBS:
        raise ValueError(f"Unknown predefined job: {job_name}")
    
    return create_custom_job(scheduler, PREDEFINED_JOBS[job_name])
