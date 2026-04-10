"""
Flask API endpoints for scheduler management.

This module provides REST API endpoints for controlling the scheduler,
managing jobs, and viewing execution history.
"""

from flask import Blueprint, request, jsonify
from typing import Dict, Any
import logging

from scheduler import get_scheduler
from scheduler_jobs import (
    create_custom_job,
    setup_default_jobs,
    PREDEFINED_JOBS,
    setup_predefined_job
)
from logger_config import get_logger

logger = get_logger(__name__)

# Create Blueprint
scheduler_bp = Blueprint('scheduler', __name__, url_prefix='/api/scheduler')


@scheduler_bp.route('/status', methods=['GET'])
def get_scheduler_status():
    """Get current scheduler status."""
    try:
        scheduler = get_scheduler()
        state = scheduler.get_scheduler_state()
        jobs = scheduler.get_jobs()
        
        return jsonify({
            'status': 'success',
            'data': {
                'state': state,
                'jobs': jobs,
                'is_running': scheduler.scheduler.running
            }
        })
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@scheduler_bp.route('/start', methods=['POST'])
def start_scheduler():
    """Start the scheduler."""
    try:
        scheduler = get_scheduler()
        scheduler.start()
        
        return jsonify({
            'status': 'success',
            'message': 'Scheduler started successfully'
        })
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@scheduler_bp.route('/stop', methods=['POST'])
def stop_scheduler():
    """Stop the scheduler."""
    try:
        scheduler = get_scheduler()
        scheduler.shutdown(wait=True)
        
        return jsonify({
            'status': 'success',
            'message': 'Scheduler stopped successfully'
        })
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@scheduler_bp.route('/pause', methods=['POST'])
def pause_scheduler():
    """Pause the scheduler."""
    try:
        scheduler = get_scheduler()
        scheduler.pause()
        
        return jsonify({
            'status': 'success',
            'message': 'Scheduler paused successfully'
        })
    except Exception as e:
        logger.error(f"Error pausing scheduler: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@scheduler_bp.route('/resume', methods=['POST'])
def resume_scheduler():
    """Resume the scheduler."""
    try:
        scheduler = get_scheduler()
        scheduler.resume()
        
        return jsonify({
            'status': 'success',
            'message': 'Scheduler resumed successfully'
        })
    except Exception as e:
        logger.error(f"Error resuming scheduler: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@scheduler_bp.route('/jobs', methods=['GET'])
def list_jobs():
    """List all configured jobs."""
    try:
        scheduler = get_scheduler()
        jobs = scheduler.get_jobs()
        
        return jsonify({
            'status': 'success',
            'data': jobs
        })
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@scheduler_bp.route('/jobs/<job_id>', methods=['GET'])
def get_job(job_id: str):
    """Get a specific job by ID."""
    try:
        scheduler = get_scheduler()
        job = scheduler.get_job(job_id)
        
        if job:
            return jsonify({
                'status': 'success',
                'data': job
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Job not found'
            }), 404
    except Exception as e:
        logger.error(f"Error getting job {job_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@scheduler_bp.route('/jobs', methods=['POST'])
def add_job():
    """Add a new job."""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['operacion', 'tipo', 'schedule_type']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}'
                }), 400
        
        scheduler = get_scheduler()
        job_id = create_custom_job(scheduler, data)
        
        return jsonify({
            'status': 'success',
            'data': {
                'job_id': job_id
            },
            'message': 'Job added successfully'
        }), 201
    except Exception as e:
        logger.error(f"Error adding job: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@scheduler_bp.route('/jobs/<job_id>', methods=['DELETE'])
def remove_job(job_id: str):
    """Remove a job."""
    try:
        scheduler = get_scheduler()
        success = scheduler.remove_job(job_id)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Job removed successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Job not found'
            }), 404
    except Exception as e:
        logger.error(f"Error removing job {job_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@scheduler_bp.route('/jobs/<job_id>/pause', methods=['POST'])
def pause_job(job_id: str):
    """Pause a specific job."""
    try:
        scheduler = get_scheduler()
        success = scheduler.pause_job(job_id)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Job paused successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Job not found'
            }), 404
    except Exception as e:
        logger.error(f"Error pausing job {job_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@scheduler_bp.route('/jobs/<job_id>/resume', methods=['POST'])
def resume_job(job_id: str):
    """Resume a paused job."""
    try:
        scheduler = get_scheduler()
        success = scheduler.resume_job(job_id)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Job resumed successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Job not found'
            }), 404
    except Exception as e:
        logger.error(f"Error resuming job {job_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@scheduler_bp.route('/executions', methods=['GET'])
def list_executions():
    """List execution history."""
    try:
        job_id = request.args.get('job_id')
        limit = request.args.get('limit', 100, type=int)
        
        scheduler = get_scheduler()
        executions = scheduler.get_executions(job_id=job_id, limit=limit)
        
        return jsonify({
            'status': 'success',
            'data': executions
        })
    except Exception as e:
        logger.error(f"Error listing executions: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@scheduler_bp.route('/jobs/predefined', methods=['GET'])
def list_predefined_jobs():
    """List available predefined job configurations."""
    return jsonify({
        'status': 'success',
        'data': {
            'jobs': list(PREDEFINED_JOBS.keys()),
            'configurations': PREDEFINED_JOBS
        }
    })


@scheduler_bp.route('/jobs/predefined/<job_name>', methods=['POST'])
def add_predefined_job(job_name: str):
    """Add a predefined job by name."""
    try:
        scheduler = get_scheduler()
        job_id = setup_predefined_job(scheduler, job_name)
        
        return jsonify({
            'status': 'success',
            'data': {
                'job_id': job_id
            },
            'message': f'Predefined job {job_name} added successfully'
        }), 201
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 404
    except Exception as e:
        logger.error(f"Error adding predefined job {job_name}: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@scheduler_bp.route('/jobs/default', methods=['POST'])
def setup_default_jobs_endpoint():
    """Setup all default jobs."""
    try:
        scheduler = get_scheduler()
        setup_default_jobs(scheduler)
        
        return jsonify({
            'status': 'success',
            'message': 'Default jobs setup successfully'
        })
    except Exception as e:
        logger.error(f"Error setting up default jobs: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@scheduler_bp.route('/heartbeat', methods=['POST'])
def send_heartbeat():
    """Send heartbeat to update scheduler state."""
    try:
        scheduler = get_scheduler()
        scheduler.send_heartbeat()
        
        return jsonify({
            'status': 'success',
            'message': 'Heartbeat sent successfully'
        })
    except Exception as e:
        logger.error(f"Error sending heartbeat: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
