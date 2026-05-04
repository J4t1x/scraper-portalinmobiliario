"""
API routes for Small Language Model (SLM) management.

Endpoints:
- GET /api/v2/slm/models - List all available models
- GET /api/v2/slm/models/installed - List installed models
- GET /api/v2/slm/models/recommended - Get recommended models
- POST /api/v2/slm/models/switch - Switch active model
- POST /api/v2/slm/models/pull - Download a model
- DELETE /api/v2/slm/models/<name> - Delete a model
- POST /api/v2/slm/models/<name>/benchmark - Benchmark a model
- GET /api/v2/slm/status - Get Ollama and SLM status
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required
from ai.slm_manager import SLMManager, SLMCatalog, ModelSize, ModelTask
from ai.agent import AnalyticsAgent
from logger_config import get_logger
from typing import Dict, Any

logger = get_logger(__name__)

slm_bp = Blueprint('slm', __name__, url_prefix='/api/v2/slm')


@slm_bp.route('/status', methods=['GET'])
@login_required
def get_status():
    """Get Ollama server and SLM system status"""
    try:
        manager = SLMManager()
        ollama_status = manager.check_ollama_status()
        
        # Get agent status
        agent = AnalyticsAgent()
        agent_status = agent.check_status()
        
        return jsonify({
            'success': True,
            'data': {
                'ollama': ollama_status,
                'agent': {
                    'current_model': agent.model,
                    'loaded': agent._model_loaded,
                    'available': agent._ollama_available
                },
                'slm_support': True
            }
        })
    except Exception as e:
        logger.error(f"Error getting SLM status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@slm_bp.route('/models', methods=['GET'])
@login_required
def list_all_models():
    """List all available models from catalog with installation status"""
    try:
        manager = SLMManager()
        models = manager.get_available_models()
        
        # Convert to dict format
        models_data = [m.to_dict() for m in models]
        
        # Group by size category
        by_size = {}
        for model in models_data:
            size = model['size_category']
            if size not in by_size:
                by_size[size] = []
            by_size[size].append(model)
        
        return jsonify({
            'success': True,
            'data': {
                'models': models_data,
                'by_size': by_size,
                'total': len(models_data),
                'installed': sum(1 for m in models_data if m['installed'])
            }
        })
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@slm_bp.route('/models/installed', methods=['GET'])
@login_required
def list_installed_models():
    """List only installed models"""
    try:
        manager = SLMManager()
        models = manager.get_installed_models(refresh=True)
        
        models_data = [m.to_dict() for m in models]
        
        return jsonify({
            'success': True,
            'data': {
                'models': models_data,
                'total': len(models_data)
            }
        })
    except Exception as e:
        logger.error(f"Error listing installed models: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@slm_bp.route('/models/recommended', methods=['GET'])
@login_required
def get_recommended_models():
    """Get recommended models for different use cases"""
    try:
        use_case = request.args.get('use_case', 'analytics')
        
        manager = SLMManager()
        models = manager.get_recommendations(use_case)
        
        models_data = [m.to_dict() for m in models]
        
        return jsonify({
            'success': True,
            'data': {
                'use_case': use_case,
                'models': models_data,
                'total': len(models_data)
            }
        })
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@slm_bp.route('/models/switch', methods=['POST'])
@login_required
def switch_model():
    """Switch to a different model"""
    try:
        data = request.json or {}
        model_name = data.get('model')
        
        if not model_name:
            return jsonify({
                'success': False,
                'error': 'Model name is required'
            }), 400
        
        agent = AnalyticsAgent()
        success = agent.switch_model(model_name)
        
        if success:
            model_info = agent.get_model_info()
            return jsonify({
                'success': True,
                'message': f'Switched to model: {model_name}',
                'data': {
                    'model': model_info
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to switch to model: {model_name}'
            }), 400
            
    except Exception as e:
        logger.error(f"Error switching model: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@slm_bp.route('/models/pull', methods=['POST'])
@login_required
def pull_model():
    """Download a model from Ollama registry"""
    try:
        data = request.json or {}
        model_name = data.get('model')
        
        if not model_name:
            return jsonify({
                'success': False,
                'error': 'Model name is required'
            }), 400
        
        manager = SLMManager()
        success, message = manager.pull_model(model_name)
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'data': {
                    'model': model_name
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400
            
    except Exception as e:
        logger.error(f"Error pulling model: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@slm_bp.route('/models/<model_name>', methods=['DELETE'])
@login_required
def delete_model(model_name: str):
    """Delete a model from Ollama"""
    try:
        manager = SLMManager()
        success, message = manager.delete_model(model_name)
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400
            
    except Exception as e:
        logger.error(f"Error deleting model: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@slm_bp.route('/models/<model_name>/benchmark', methods=['POST'])
@login_required
def benchmark_model(model_name: str):
    """Benchmark a model's performance"""
    try:
        data = request.json or {}
        test_prompt = data.get('prompt', 'Analyze real estate market trends in Santiago')
        
        manager = SLMManager()
        result = manager.benchmark_model(model_name, test_prompt)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'data': result
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Benchmark failed')
            }), 400
            
    except Exception as e:
        logger.error(f"Error benchmarking model: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@slm_bp.route('/models/<model_name>/info', methods=['GET'])
@login_required
def get_model_info(model_name: str):
    """Get detailed information about a model"""
    try:
        manager = SLMManager()
        
        # Get from catalog
        catalog_model = SLMCatalog.get_by_name(model_name)
        
        # Get from Ollama
        ollama_info = manager.get_model_info(model_name)
        
        data = {}
        if catalog_model:
            data['catalog'] = catalog_model.to_dict()
        
        if ollama_info:
            data['ollama'] = ollama_info
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Model not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': data
        })
        
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@slm_bp.route('/catalog/sizes', methods=['GET'])
@login_required
def get_size_categories():
    """Get available size categories"""
    return jsonify({
        'success': True,
        'data': {
            'sizes': [
                {
                    'value': size.value,
                    'name': size.name,
                    'models': len(SLMCatalog.get_by_size(size))
                }
                for size in ModelSize
            ]
        }
    })


@slm_bp.route('/catalog/tasks', methods=['GET'])
@login_required
def get_task_categories():
    """Get available task categories"""
    return jsonify({
        'success': True,
        'data': {
            'tasks': [
                {
                    'value': task.value,
                    'name': task.name,
                    'models': len(SLMCatalog.get_by_task(task))
                }
                for task in ModelTask
            ]
        }
    })
