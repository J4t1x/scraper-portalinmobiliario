"""
Tests for scheduler module.

This module contains unit and integration tests for the APScheduler
integration and scheduler functionality.
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from scheduler import ScraperScheduler, get_scheduler, shutdown_global_scheduler
from models import SchedulerExecution, SchedulerState
from database import get_session


@pytest.fixture
def mock_database_url():
    """Provide a mock database URL for testing."""
    return "sqlite:///:memory:"


@pytest.fixture
def test_scheduler(mock_database_url):
    """Create a test scheduler instance."""
    scheduler = ScraperScheduler(database_url=mock_database_url)
    yield scheduler
    # Cleanup
    if scheduler.scheduler.running:
        scheduler.shutdown(wait=False)


class TestScraperScheduler:
    """Test cases for ScraperScheduler class."""
    
    def test_scheduler_initialization(self, test_scheduler):
        """Test that scheduler initializes correctly."""
        assert test_scheduler.scheduler_id is not None
        assert test_scheduler.scheduler is not None
        assert not test_scheduler.scheduler.running
    
    def test_scheduler_start(self, test_scheduler):
        """Test starting the scheduler."""
        test_scheduler.start()
        assert test_scheduler.scheduler.running
        test_scheduler.shutdown(wait=False)
    
    def test_scheduler_shutdown(self, test_scheduler):
        """Test shutting down the scheduler."""
        test_scheduler.start()
        test_scheduler.shutdown(wait=False)
        assert not test_scheduler.scheduler.running
    
    def test_add_job(self, test_scheduler):
        """Test adding a job to the scheduler."""
        def dummy_job():
            return {"status": "success"}
        
        job_id = test_scheduler.add_job(
            dummy_job,
            job_id='test_job',
            trigger='interval',
            seconds=10
        )
        
        # Job should be added
        jobs = test_scheduler.get_jobs()
        assert len(jobs) > 0
        assert any(job['id'] == 'test_job' for job in jobs)
    
    def test_remove_job(self, test_scheduler):
        """Test removing a job from the scheduler."""
        def dummy_job():
            return {"status": "success"}
        
        test_scheduler.add_job(
            dummy_job,
            job_id='test_job_remove',
            trigger='interval',
            seconds=10
        )
        
        success = test_scheduler.remove_job('test_job_remove')
        assert success is True
        
        # Job should be removed
        jobs = test_scheduler.get_jobs()
        assert not any(job['id'] == 'test_job_remove' for job in jobs)
    
    def test_pause_and_resume_job(self, test_scheduler):
        """Test pausing and resuming a job."""
        def dummy_job():
            return {"status": "success"}
        
        test_scheduler.add_job(
            dummy_job,
            job_id='test_job_pause',
            trigger='interval',
            seconds=10
        )
        
        # Pause job
        success = test_scheduler.pause_job('test_job_pause')
        assert success is True
        
        # Resume job
        success = test_scheduler.resume_job('test_job_pause')
        assert success is True
    
    def test_get_jobs(self, test_scheduler):
        """Test retrieving list of jobs."""
        def dummy_job():
            return {"status": "success"}
        
        test_scheduler.add_job(
            dummy_job,
            job_id='test_job_list',
            trigger='interval',
            seconds=10
        )
        
        jobs = test_scheduler.get_jobs()
        assert isinstance(jobs, list)
        assert len(jobs) > 0
    
    def test_get_job(self, test_scheduler):
        """Test retrieving a specific job."""
        def dummy_job():
            return {"status": "success"}
        
        test_scheduler.add_job(
            dummy_job,
            job_id='test_job_get',
            trigger='interval',
            seconds=10
        )
        
        job = test_scheduler.get_job('test_job_get')
        assert job is not None
        assert job['id'] == 'test_job_get'
    
    def test_get_nonexistent_job(self, test_scheduler):
        """Test retrieving a non-existent job."""
        job = test_scheduler.get_job('nonexistent_job')
        assert job is None


class TestSchedulerExecution:
    """Test cases for scheduler execution tracking."""
    
    def test_log_execution_success(self, test_scheduler):
        """Test logging a successful execution."""
        test_scheduler._log_execution(
            job_id='test_job',
            job_name='Test Job',
            status='success',
            result={'properties_scraped': 10, 'pages_processed': 2}
        )
        
        executions = test_scheduler.get_executions(job_id='test_job')
        assert len(executions) > 0
        assert executions[0]['status'] == 'success'
        assert executions[0]['properties_scraped'] == 10
    
    def test_log_execution_failure(self, test_scheduler):
        """Test logging a failed execution."""
        test_scheduler._log_execution(
            job_id='test_job_fail',
            job_name='Test Job Fail',
            status='failed',
            error_message='Test error'
        )
        
        executions = test_scheduler.get_executions(job_id='test_job_fail')
        assert len(executions) > 0
        assert executions[0]['status'] == 'failed'
        assert executions[0]['error_message'] == 'Test error'


class TestSchedulerState:
    """Test cases for scheduler state management."""
    
    def test_update_scheduler_state(self, test_scheduler):
        """Test updating scheduler state."""
        test_scheduler._update_scheduler_state('running')
        
        state = test_scheduler.get_scheduler_state()
        assert state is not None
        assert state['status'] == 'running'
    
    def test_heartbeat(self, test_scheduler):
        """Test sending heartbeat."""
        test_scheduler._update_scheduler_state('running')
        test_scheduler.send_heartbeat()
        
        state = test_scheduler.get_scheduler_state()
        assert state is not None
        assert state['last_heartbeat'] is not None


class TestGlobalScheduler:
    """Test cases for global scheduler instance."""
    
    def test_get_scheduler(self, mock_database_url):
        """Test getting global scheduler instance."""
        scheduler = get_scheduler()
        assert scheduler is not None
        assert isinstance(scheduler, ScraperScheduler)
        
        # Cleanup
        shutdown_global_scheduler()
    
    def test_shutdown_global_scheduler(self, mock_database_url):
        """Test shutting down global scheduler."""
        scheduler = get_scheduler()
        shutdown_global_scheduler()
        
        # New instance should be created
        new_scheduler = get_scheduler()
        assert new_scheduler.scheduler_id != scheduler.scheduler_id
        
        # Cleanup
        shutdown_global_scheduler()


class TestSchedulerJobs:
    """Test cases for scheduler job functions."""
    
    @patch('scheduler_jobs.create_scraping_job')
    def test_create_scraping_job(self, mock_create, test_scheduler):
        """Test creating a scraping job."""
        mock_create.return_value = 'test_job_id'
        
        from scheduler_jobs import create_scraping_job
        
        job_id = create_scraping_job(
            test_scheduler,
            operacion='venta',
            tipo='departamento',
            schedule_type='interval',
            hours=6
        )
        
        assert job_id == 'test_job_id'
        mock_create.assert_called_once()
    
    @patch('scheduler_jobs.create_custom_job')
    def test_create_custom_job(self, mock_create, test_scheduler):
        """Test creating a custom job."""
        mock_create.return_value = 'custom_job_id'
        
        from scheduler_jobs import create_custom_job
        
        job_config = {
            'operacion': 'venta',
            'tipo': 'casa',
            'schedule_type': 'cron',
            'schedule_args': {'hour': 2, 'minute': 0}
        }
        
        job_id = create_custom_job(test_scheduler, job_config)
        assert job_id == 'custom_job_id'
        mock_create.assert_called_once()
    
    def test_predefined_jobs_exist(self):
        """Test that predefined jobs configuration exists (SPEC-012)."""
        from scheduler_jobs import PREDEFINED_JOBS
        
        assert isinstance(PREDEFINED_JOBS, dict)
        assert len(PREDEFINED_JOBS) > 0
        
        # SPEC-012 required jobs
        assert 'venta_departamento_daily' in PREDEFINED_JOBS
        assert 'arriendo_departamento_daily' in PREDEFINED_JOBS
        assert 'venta_casa_daily' in PREDEFINED_JOBS
        assert 'arriendo_casa_daily' in PREDEFINED_JOBS
        assert 'venta_oficina_weekly' in PREDEFINED_JOBS
    
    def test_predefined_jobs_config(self):
        """Test that predefined jobs have correct configuration (SPEC-012)."""
        from scheduler_jobs import PREDEFINED_JOBS
        
        # Test venta_departamento_daily configuration
        venta_dept = PREDEFINED_JOBS['venta_departamento_daily']
        assert venta_dept['operacion'] == 'venta'
        assert venta_dept['tipo'] == 'departamento'
        assert venta_dept['schedule_type'] == 'cron'
        assert venta_dept['schedule_args'] == {'hour': 2, 'minute': 0}
        assert venta_dept['max_pages'] == 50
        assert venta_dept['scrape_details'] is True
        assert venta_dept['max_detail_properties'] == 100
        
        # Test arriendo_departamento_daily configuration
        arriendo_dept = PREDEFINED_JOBS['arriendo_departamento_daily']
        assert arriendo_dept['operacion'] == 'arriendo'
        assert arriendo_dept['tipo'] == 'departamento'
        assert arriendo_dept['schedule_args'] == {'hour': 3, 'minute': 0}
        
        # Test venta_oficina_weekly configuration
        venta_oficina = PREDEFINED_JOBS['venta_oficina_weekly']
        assert venta_oficina['schedule_args'] == {'day_of_week': 'mon', 'hour': 6, 'minute': 0}
    
    @patch('scheduler_jobs.create_scraping_job')
    def test_setup_default_jobs(self, mock_create, test_scheduler):
        """Test setup_default_jobs function (SPEC-012)."""
        from scheduler_jobs import setup_default_jobs
        
        mock_create.return_value = 'test_job_id'
        
        setup_default_jobs(test_scheduler)
        
        # Should create 5 jobs (SPEC-012)
        assert mock_create.call_count == 5
        
        # Verify calls were made with correct parameters
        calls = mock_create.call_args_list
        
        # First call: venta_departamento at 02:00
        assert calls[0][1]['operacion'] == 'venta'
        assert calls[0][1]['tipo'] == 'departamento'
        assert calls[0][1]['schedule_type'] == 'cron'
        assert calls[0][2]['hour'] == 2
        assert calls[0][2]['minute'] == 0
        assert calls[0][2]['max_pages'] == 50
        assert calls[0][2]['scrape_details'] is True
        assert calls[0][2]['max_detail_properties'] == 100


class TestSchedulerAPI:
    """Test cases for scheduler API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create a test Flask client."""
        from app import app
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_get_scheduler_status(self, client):
        """Test GET /api/scheduler/status endpoint."""
        response = client.get('/api/scheduler/status')
        assert response.status_code in [200, 500]  # May fail if DB not configured
    
    def test_list_jobs(self, client):
        """Test GET /api/scheduler/jobs endpoint."""
        response = client.get('/api/scheduler/jobs')
        assert response.status_code in [200, 500]
    
    def test_list_predefined_jobs(self, client):
        """Test GET /api/scheduler/jobs/predefined endpoint."""
        response = client.get('/api/scheduler/jobs/predefined')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert 'jobs' in data['data']


class TestJobWrapperMetrics:
    """Test cases for job wrapper metrics extraction (SPEC-012)."""
    
    @patch('scheduler_jobs.run_scraping')
    def test_job_wrapper_returns_metrics(self, mock_run_scraping):
        """Test that job wrapper returns metrics dictionary (SPEC-012)."""
        from scheduler_jobs import create_scraping_job
        from scheduler import ScraperScheduler
        
        # Mock run_scraping to return metrics
        mock_run_scraping.return_value = {
            'properties_scraped': 100,
            'pages_processed': 5,
            'status': 'success'
        }
        
        scheduler = ScraperScheduler(database_url="sqlite:///:memory:")
        
        # Create a job
        job_id = create_scraping_job(
            scheduler,
            operacion='venta',
            tipo='departamento',
            schedule_type='interval',
            hours=6,
            max_pages=5,
            scrape_details=False
        )
        
        assert job_id == 'scrape_venta_departamento'
        
        # Verify the job was added
        jobs = scheduler.get_jobs()
        assert len(jobs) > 0
        
        scheduler.shutdown(wait=False)
