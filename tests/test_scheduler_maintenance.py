import pytest
from unittest.mock import MagicMock, patch
import os
import datetime

from scheduler_jobs import (
    create_data_cleanup_job,
    create_log_maintenance_job,
    create_backup_job,
    setup_maintenance_jobs
)
from scheduler import ScraperScheduler

@pytest.fixture
def mock_scheduler():
    scheduler = MagicMock(spec=ScraperScheduler)
    return scheduler

@patch("os.path.exists")
@patch("os.listdir")
@patch("os.path.isfile")
@patch("os.path.getmtime")
@patch("os.remove")
def test_create_data_cleanup_job(
    mock_remove, mock_getmtime, mock_isfile, mock_listdir, mock_exists, mock_scheduler
):
    # Setup the mocks
    mock_exists.return_value = True
    mock_listdir.return_value = ["file1.json", "file2.json"]
    mock_isfile.return_value = True
    # Make file1 old enough, file2 recent
    import time
    old_time = time.time() - (100 * 24 * 3600)  # 100 days old
    recent_time = time.time() - (10 * 24 * 3600)  # 10 days old
    mock_getmtime.side_effect = [old_time, recent_time]

    job_id = create_data_cleanup_job(mock_scheduler, days_to_keep=90)
    assert job_id == 'data_cleanup_job'
    
    mock_scheduler.add_job.assert_called_once()
    
    # Extract the wrapper to test its execution
    job_wrapper = mock_scheduler.add_job.call_args[0][0]
    result = job_wrapper()
    
    # Should delete only 1 file (the 100 days old one)
    assert result['deleted_files'] == 1
    mock_remove.assert_called_once()

@patch("scheduler_jobs.logger")
def test_create_log_maintenance_job(mock_logger, mock_scheduler):
    with patch("logger_config.setup_logging") as mock_setup_logging:
        mock_log_config = MagicMock()
        mock_setup_logging.return_value = mock_log_config
        
        job_id = create_log_maintenance_job(mock_scheduler)
        assert job_id == 'log_maintenance_job'
        
        mock_scheduler.add_job.assert_called_once()
        job_wrapper = mock_scheduler.add_job.call_args[0][0]
        result = job_wrapper()
        
        assert result['status'] == 'success'
        mock_log_config.clean_old_logs.assert_called_once()

@patch("os.path.exists")
@patch("os.makedirs")
@patch("subprocess.run")
def test_create_backup_job(mock_run, mock_makedirs, mock_exists, mock_scheduler):
    mock_exists.return_value = True
    
    job_id = create_backup_job(mock_scheduler)
    assert job_id == 'backup_job'
    
    mock_scheduler.add_job.assert_called_once()
    job_wrapper = mock_scheduler.add_job.call_args[0][0]
    result = job_wrapper()
    
    assert 'backup_file' in result
    mock_makedirs.assert_called_once_with('backups', exist_ok=True)
    mock_run.assert_called_once()

@patch("scheduler_jobs.create_cleanup_job")
@patch("scheduler_jobs.create_data_cleanup_job")
@patch("scheduler_jobs.create_log_maintenance_job")
@patch("scheduler_jobs.create_backup_job")
def test_setup_maintenance_jobs(
    mock_backup, mock_log, mock_data, mock_cleanup, mock_scheduler
):
    setup_maintenance_jobs(mock_scheduler)
    mock_cleanup.assert_called_once_with(mock_scheduler)
    mock_data.assert_called_once_with(mock_scheduler)
    mock_log.assert_called_once_with(mock_scheduler)
    mock_backup.assert_called_once_with(mock_scheduler)
