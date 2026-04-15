from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from dashboard.auth import user_manager
from data_loader import JSONDataLoader
from db_loader import DatabaseLoader
from logger_config import get_logger
from datetime import datetime
from typing import Dict, Optional
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
from collections import deque
import sys
import os
import uuid
import re

logger = get_logger(__name__)
bp = Blueprint('main', __name__)

# ============================================================================
# SCRAPER EXECUTION QUEUE
# Max 1 concurrent execution, up to 5 pending in queue
# ============================================================================
_scraper_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='scraper')
_scraper_queue = deque(maxlen=10)  # Track queue entries
_scraper_lock = threading.Lock()

# SocketIO se importará dinámicamente cuando sea necesario
_socketio = None

def get_socketio():
    """Lazy import de socketio para evitar circular imports"""
    global _socketio
    if _socketio is None:
        try:
            from flask import current_app
            _socketio = current_app.extensions.get('socketio')
        except Exception as e:
            logger.warning(f"SocketIO no disponible: {e}")
    return _socketio

@bp.route('/')
def index():
    """Redirige al dashboard si está autenticado, sino al login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('main.login'))

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        user = user_manager.authenticate(username, password)
        
        if user:
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.dashboard'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')
    
    return render_template('auth/login.html')

@bp.route('/logout')
@login_required
def logout():
    """Cerrar sesión"""
    logout_user()
    flash('Sesión cerrada exitosamente', 'success')
    return redirect(url_for('main.login'))

@bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal - Oportunidades de inversión"""
    return render_template('dashboard/home.html', user=current_user)

@bp.route('/dashboard/stats')
@login_required
def dashboard_stats():
    """Dashboard de estadísticas (vista anterior)"""
    return render_template('dashboard/index.html', user=current_user)

@bp.route('/data')
@login_required
def data():
    """Explorador de datos"""
    try:
        db_loader = DatabaseLoader()
        stats = db_loader.get_stats()
        total_properties = stats.get('total', 0)
        return render_template('dashboard/data.html', user=current_user, total=total_properties)
    except Exception as e:
        logger.error(f"Error en /data: {e}")
        flash('Error cargando datos', 'error')
        return render_template('dashboard/data.html', user=current_user, total=0)

@bp.route('/scraper')
@login_required
def scraper():
    """Panel de control del scraper"""
    return render_template('dashboard/scraper.html', user=current_user)

@bp.route('/analytics')
@login_required
def analytics():
    """AI Analytics Studio - Experiencia premium de analítica con IA"""
    return render_template('dashboard/ai_analytics.html', user=current_user)

@bp.route('/property/<int:property_id>')
@login_required
def property_detail(property_id):
    """Página de detalle de propiedad"""
    try:
        logger.info(f"Buscando propiedad con ID: {property_id}")
        db_loader = DatabaseLoader()
        prop = db_loader.get_property_by_id(property_id)
        
        if not prop:
            logger.warning(f"Propiedad no encontrada: {property_id}")
            flash('Propiedad no encontrada', 'error')
            return redirect(url_for('main.data'))
        
        logger.info(f"Propiedad encontrada: {prop.get('titulo', 'Sin título')}")
        return render_template('dashboard/property_detail.html', user=current_user, property=prop)
    except Exception as e:
        logger.error(f"Error en property_detail: {e}", exc_info=True)
        flash('Error cargando detalle de propiedad', 'error')
        return redirect(url_for('main.data'))

@bp.route('/api/properties')
@login_required
def api_properties():
    """API endpoint para listar propiedades desde PostgreSQL con filtros y paginación"""
    try:
        db_loader = DatabaseLoader()

        # Parámetros de filtro
        operacion = request.args.get('operacion')
        tipo = request.args.get('tipo')
        comuna = request.args.get('comuna')
        precio_min = request.args.get('precio_min', type=int)
        precio_max = request.args.get('precio_max', type=int)
        search = request.args.get('search')
        execution_id = request.args.get('execution_id')
        
        # Paginación
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        # Obtener propiedades desde BD
        result = db_loader.get_properties(
            operacion=operacion,
            tipo=tipo,
            comuna=comuna,
            precio_min=precio_min,
            precio_max=precio_max,
            search=search,
            page=page,
            per_page=per_page,
            execution_id=execution_id
        )

        return jsonify({
            'success': True,
            'data': result['data'],
            'pagination': result['pagination']
        })
    except Exception as e:
        logger.error(f"Error en api_properties: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/properties/<int:property_id>')
@login_required
def api_property_detail(property_id):
    """API endpoint para detalle de propiedad desde PostgreSQL"""
    try:
        db_loader = DatabaseLoader()
        prop = db_loader.get_property_by_id(property_id)

        if not prop:
            return jsonify({
                'success': False,
                'error': 'Propiedad no encontrada'
            }), 404

        return jsonify({
            'success': True,
            'data': prop
        })
    except Exception as e:
        logger.error(f"Error en api_property_detail: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/stats')
@login_required
def api_stats():
    """API endpoint para estadísticas básicas desde PostgreSQL"""
    try:
        db_loader = DatabaseLoader()
        stats = db_loader.get_stats()
        
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        logger.error(f"Error en api_stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/advanced-stats')
@login_required
def api_advanced_stats():
    """API endpoint para estadísticas avanzadas con KPIs adicionales"""
    try:
        loader = JSONDataLoader()
        stats = loader.get_advanced_stats()
        
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        logger.error(f"Error en api_advanced_stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/filters')
@login_required
def api_filters():
    """API endpoint para valores de filtros disponibles desde PostgreSQL"""
    try:
        db_loader = DatabaseLoader()
        filter_options = db_loader.get_filter_options()

        return jsonify({
            'success': True,
            'data': filter_options
        })
    except Exception as e:
        logger.error(f"Error en api_filters: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/json-files')
@login_required
def api_json_files():
    """API endpoint para listar archivos JSON disponibles"""
    try:
        loader = JSONDataLoader()
        files = loader.list_json_files()
        latest = loader.get_latest_json_file()

        return jsonify({
            'success': True,
            'data': {
                'files': files,
                'latest': latest
            }
        })
    except Exception as e:
        logger.error(f"Error en api_json_files: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/scraper/run', methods=['POST'])
@login_required
def api_run_manual_scraping():
    """API endpoint para ejecutar scraping manual con tracking y cola de ejecución"""
    try:
        from execution_tracker import ExecutionTracker
        socketio = get_socketio()
        
        # Get parameters from JSON body
        data = request.json or {}
        operacion = data.get('operacion', 'venta')
        tipo = data.get('tipo', 'departamento')
        max_pages = data.get('max_pages', 10)
        formato = data.get('formato', 'json')
        scrape_details = data.get('scrape_details', True)
        verbose = data.get('verbose', False)
        
        # Check queue capacity
        with _scraper_lock:
            pending_count = sum(1 for e in _scraper_queue if e.get('status') in ('queued', 'running'))
            if pending_count >= 5:
                return jsonify({
                    'success': False,
                    'error': 'Cola de ejecución llena. Espera a que finalicen algunas ejecuciones.',
                    'queue_size': pending_count
                }), 429
        
        # Create execution tracker
        tracker = ExecutionTracker()
        execution_id = tracker.start_execution(
            operacion=operacion,
            tipo=tipo,
            triggered_by='manual',
            user_id=current_user.username if current_user else None,
            parameters={
                'max_pages': max_pages,
                'formato': formato,
                'scrape_details': scrape_details,
                'verbose': verbose
            }
        )
        
        # Add to queue tracking
        queue_entry = {
            'execution_id': execution_id,
            'operacion': operacion,
            'tipo': tipo,
            'status': 'queued',
            'queued_at': datetime.utcnow().isoformat(),
            'user': current_user.username if current_user else None
        }
        with _scraper_lock:
            _scraper_queue.append(queue_entry)
        
        # Use python3 explicitly
        python_cmd = sys.executable or 'python3'
        
        # Build command with execution ID
        cmd = [
            python_cmd,
            'main.py',
            '--operacion', operacion,
            '--tipo', tipo,
            '--max-pages', str(max_pages),
            '--formato', formato,
            '--execution-id', execution_id
        ]
        
        if scrape_details:
            cmd.append('--scrape-details')
            cmd.extend(['--max-detail-properties', '100'])
        
        if verbose:
            cmd.append('--verbose')
        
        logger.info(f"Encolando scraping manual: {' '.join(cmd)}")
        tracker.log_info(f"Comando encolado: {' '.join(cmd)}", source='dashboard')
        
        # Verify main.py exists
        if not os.path.exists('main.py'):
            error_msg = "main.py not found in current directory"
            logger.error(error_msg)
            tracker.complete_execution(status='failed', error_message=error_msg)
            queue_entry['status'] = 'failed'
            return jsonify({'success': False, 'error': error_msg}), 500
        
        # Submit to thread pool (queue) for sequential execution
        def run_scraping():
            queue_entry['status'] = 'running'
            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                for line in process.stdout:
                    line = line.strip()
                    if line:
                        tracker.log_info(line, source='scraper')
                        if socketio:
                            socketio.emit('scraping_log', {
                                'execution_id': execution_id,
                                'log': line,
                                'timestamp': datetime.utcnow().isoformat()
                            })
                
                process.wait()
                
                if process.returncode == 0:
                    tracker.complete_execution(status='completed')
                    queue_entry['status'] = 'completed'
                else:
                    tracker.complete_execution(
                        status='failed',
                        error_message=f'Process exited with code {process.returncode}'
                    )
                    queue_entry['status'] = 'failed'
                
                if socketio:
                    socketio.emit('scraping_complete', {
                        'execution_id': execution_id,
                        'return_code': process.returncode,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                
                logger.info(f"Scraping manual completado. Return code: {process.returncode}")
                
            except FileNotFoundError:
                error_msg = f'Comando no encontrado: {python_cmd}'
                logger.error(error_msg)
                tracker.complete_execution(status='failed', error_message=error_msg)
                queue_entry['status'] = 'failed'
                if socketio:
                    socketio.emit('scraping_error', {
                        'execution_id': execution_id,
                        'error': error_msg,
                        'timestamp': datetime.utcnow().isoformat()
                    })
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error ejecutando scraping manual: {error_msg}")
                tracker.complete_execution(status='failed', error_message=error_msg)
                queue_entry['status'] = 'failed'
                if socketio:
                    socketio.emit('scraping_error', {
                        'execution_id': execution_id,
                        'error': error_msg,
                        'timestamp': datetime.utcnow().isoformat()
                    })
        
        # Submit to executor (runs sequentially, 1 at a time)
        _scraper_executor.submit(run_scraping)
        
        # Calculate queue position
        with _scraper_lock:
            position = sum(1 for e in _scraper_queue if e.get('status') in ('queued', 'running'))
        
        return jsonify({
            'success': True,
            'message': f'Scraping encolado para {operacion} {tipo}. Posición en cola: {position}.',
            'data': {
                'execution_id': execution_id,
                'operacion': operacion,
                'tipo': tipo,
                'max_pages': max_pages,
                'formato': formato,
                'queue_position': position,
                'command': ' '.join(cmd)
            }
        })
    except Exception as e:
        logger.error(f"Error en api_run_manual_scraping: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/scraper/queue')
@login_required
def api_scraper_queue():
    """API endpoint para consultar el estado de la cola de ejecución"""
    with _scraper_lock:
        queue_data = list(_scraper_queue)
    
    return jsonify({
        'success': True,
        'data': {
            'queue': queue_data,
            'running': sum(1 for e in queue_data if e.get('status') == 'running'),
            'queued': sum(1 for e in queue_data if e.get('status') == 'queued'),
            'completed': sum(1 for e in queue_data if e.get('status') == 'completed'),
            'failed': sum(1 for e in queue_data if e.get('status') == 'failed'),
            'max_concurrent': 1,
            'max_queue_size': 5
        }
    })

@bp.route('/api/db/health')
@login_required
def api_db_health():
    """API endpoint para verificar el estado de la conexión a la base de datos"""
    try:
        from database import health_check
        result = health_check()
        status_code = 200 if result['status'] == 'healthy' else 503
        return jsonify({'success': True, 'data': result}), status_code
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 503

@bp.route('/api/analytics/chat', methods=['POST'])
@login_required
def api_analytics_chat():
    """API endpoint para interactuar con el agente de analítica (Ollama).
    Acepta tanto 'message' como 'question' para compatibilidad con ambas interfaces."""
    try:
        from ai.agent import AnalyticsAgent
        data = request.json or {}
        # Accept both 'message' (from old interface) and 'question' (from AI analytics template)
        message = data.get('message') or data.get('question', '')
        
        if not message:
            return jsonify({'success': False, 'error': 'El mensaje no puede estar vacío'}), 400
            
        agent = AnalyticsAgent()
        response_text = agent.generate_response(message)
        
        return jsonify({
            'success': True,
            'response': response_text,
            'data': {
                'response': response_text
            }
        })
    except Exception as e:
        logger.error(f"Error en api_analytics_chat: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/analytics/chat/stream', methods=['POST'])
@login_required
def api_analytics_chat_stream():
    """API endpoint para interactuar con el agente de analítica con streaming (SSE).
    Retorna respuestas en tiempo real a medida que se generan."""
    try:
        from ai.agent import AnalyticsAgent
        from flask import Response, stream_with_context
        import json
        
        data = request.json or {}
        message = data.get('message') or data.get('question', '')
        
        if not message:
            return jsonify({'success': False, 'error': 'El mensaje no puede estar vacío'}), 400
        
        def generate():
            """Generator function for streaming response"""
            try:
                agent = AnalyticsAgent()
                context = agent._build_context_from_db()
                
                # Send initial event
                yield f"data: {json.dumps({'type': 'start', 'message': 'Iniciando análisis...'})}\n\n"
                
                # Stream response chunks
                for chunk in agent.ask_stream(message, context):
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                
                # Send completion event
                yield f"data: {json.dumps({'type': 'done', 'message': 'Análisis completado'})}\n\n"
                
            except Exception as e:
                logger.error(f"Error en streaming: {str(e)}", exc_info=True)
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive'
            }
        )
        
    except Exception as e:
        logger.error(f"Error en api_analytics_chat_stream: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/scraper/executions')
@login_required
def api_scraper_executions():
    """API endpoint para listar historial de ejecuciones del scraper"""
    try:
        db_loader = DatabaseLoader()
        
        # Parámetros de filtro
        status = request.args.get('status')
        operacion = request.args.get('operacion')
        tipo = request.args.get('tipo')
        
        # Paginación
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        result = db_loader.get_scraper_executions(
            status=status,
            operacion=operacion,
            tipo=tipo,
            page=page,
            per_page=per_page
        )
        
        return jsonify({
            'status': 'success',
            'success': True,
            'data': result['data'],
            'pagination': result['pagination']
        })
    except Exception as e:
        logger.error(f"Error en api_scraper_executions: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/scraper/executions/<execution_id>')
@login_required
def api_scraper_execution_detail(execution_id):
    """API endpoint para detalle de una ejecución del scraper con logs"""
    try:
        db_loader = DatabaseLoader()
        execution = db_loader.get_execution_by_id(execution_id)
        
        if not execution:
            return jsonify({
                'success': False,
                'error': 'Ejecución no encontrada'
            }), 404
        
        return jsonify({
            'success': True,
            'data': execution
        })
    except Exception as e:
        logger.error(f"Error en api_scraper_execution_detail: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/scraper/executions/<execution_id>/logs')
@login_required
def api_scraper_execution_logs(execution_id):
    """API endpoint para obtener logs de una ejecución específica"""
    try:
        db_loader = DatabaseLoader()
        
        # Parámetros
        level = request.args.get('level')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 100, type=int)
        
        result = db_loader.get_execution_logs(
            execution_id=execution_id,
            level=level,
            page=page,
            per_page=per_page
        )
        
        return jsonify({
            'success': True,
            'data': result['data'],
            'pagination': result['pagination']
        })
    except Exception as e:
        logger.error(f"Error en api_scraper_execution_logs: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/scraper/executions/<execution_id>/cancel', methods=['POST'])
@login_required
def api_scraper_execution_cancel(execution_id):
    """API endpoint para cancelar una ejecución del scraper"""
    try:
        db_loader = DatabaseLoader()
        
        # Cancelar la ejecución
        success = db_loader.cancel_execution(execution_id)
        
        if success:
            logger.info(f"Ejecución {execution_id} cancelada por usuario {current_user.username}")
            return jsonify({
                'success': True,
                'message': 'Ejecución cancelada exitosamente'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No se pudo cancelar la ejecución. Puede que ya haya finalizado.'
            }), 400
    except Exception as e:
        logger.error(f"Error en api_scraper_execution_cancel: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/investment-opportunities')
@login_required
def api_investment_opportunities():
    """API endpoint para obtener oportunidades de inversión destacadas con fallback a JSON"""
    try:
        db_loader = DatabaseLoader()
        opportunities = db_loader.get_investment_opportunities()
        
        # Check if we have data from database
        has_db_data = (
            opportunities.get('featured') is not None or 
            len(opportunities.get('top_5', [])) > 0 or
            len(opportunities.get('highlighted', [])) > 0
        )
        
        # If no data from DB, try to load from JSON files as fallback
        if not has_db_data:
            logger.warning("No data from database, attempting to load from JSON files")
            try:
                json_loader = JSONDataLoader()
                opportunities = _get_opportunities_from_json(json_loader)
                opportunities['data_source'] = 'json'
            except Exception as json_error:
                logger.error(f"Error loading from JSON: {json_error}")
                # Return empty structure
                opportunities = {
                    'featured': None,
                    'top_5': [],
                    'highlighted': [],
                    'market_stats': {'avg_price_m2': 0, 'total_value': 0},
                    'communes': [],
                    'alerts': [{
                        'type': 'warning',
                        'message': 'No hay datos disponibles. Ejecuta el scraper para obtener propiedades.'
                    }],
                    'data_source': 'empty'
                }
        else:
            opportunities['data_source'] = 'database'
        
        return jsonify({
            'success': True,
            'data': opportunities
        })
    except Exception as e:
        logger.error(f"Error en api_investment_opportunities: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def _get_opportunities_from_json(json_loader: JSONDataLoader) -> Dict:
    """
    Get opportunities from JSON files when database is empty.
    This is a simplified version that works with JSON data structure.
    """
    import re
    
    # Load all properties from JSON
    all_properties = json_loader.load_all_json_files()
    
    if not all_properties:
        return {
            'featured': None,
            'top_5': [],
            'highlighted': [],
            'market_stats': {'avg_price_m2': 0, 'total_value': 0},
            'communes': [],
            'alerts': []
        }
    
    # Filter only venta properties with valid data
    venta_props = []
    for prop in all_properties:
        if prop.get('operacion') != 'venta':
            continue
        
        # Extract superficie from atributos
        superficie = _extract_superficie_from_atributos(prop.get('atributos', ''))
        precio_clp = _extract_price_clp_from_json(prop.get('precio', ''))
        
        if superficie and superficie > 0 and precio_clp and precio_clp > 0:
            prop['superficie_total'] = superficie
            prop['precio_clp'] = precio_clp
            prop['precio_m2'] = int(precio_clp / superficie)
            venta_props.append(prop)
    
    if not venta_props:
        return {
            'featured': None,
            'top_5': [],
            'highlighted': [],
            'market_stats': {'avg_price_m2': 0, 'total_value': 0},
            'communes': [],
            'alerts': []
        }
    
    # Calculate market average
    avg_price_m2 = sum(p['precio_m2'] for p in venta_props) / len(venta_props)
    total_value = sum(p['precio_clp'] for p in venta_props)
    
    # Find opportunities (below 85% of market average)
    opportunities = [p for p in venta_props if p['precio_m2'] < avg_price_m2 * 0.85]
    opportunities.sort(key=lambda x: x['precio_m2'])
    
    # Calculate scores
    opportunities_with_scores = []
    for prop in opportunities[:10]:
        discount = ((avg_price_m2 - prop['precio_m2']) / avg_price_m2 * 100)
        score = min(100, int(100 - (prop['precio_m2'] / avg_price_m2 * 100)))
        
        opportunities_with_scores.append({
            'property': _json_prop_to_dict(prop),
            'score': score,
            'price_m2': prop['precio_m2'],
            'market_avg_m2': int(avg_price_m2),
            'discount_percentage': int(discount)
        })
    
    # Get commune stats
    commune_stats = {}
    for prop in venta_props:
        comuna = _extract_comuna_from_ubicacion(prop.get('ubicacion', ''))
        if not comuna:
            continue
        if comuna not in commune_stats:
            commune_stats[comuna] = {'count': 0, 'prices_m2': []}
        commune_stats[comuna]['count'] += 1
        commune_stats[comuna]['prices_m2'].append(prop['precio_m2'])
    
    communes_data = []
    for comuna, stats in commune_stats.items():
        avg_comuna = sum(stats['prices_m2']) / len(stats['prices_m2'])
        variation = ((avg_comuna - avg_price_m2) / avg_price_m2 * 100)
        communes_data.append({
            'name': comuna,
            'count': stats['count'],
            'avg_price_m2': int(avg_comuna),
            'variation': int(variation)
        })
    
    communes_data.sort(key=lambda x: x['avg_price_m2'], reverse=True)
    
    return {
        'featured': opportunities_with_scores[0] if opportunities_with_scores else None,
        'top_5': opportunities_with_scores[:5],
        'highlighted': opportunities_with_scores[:4],
        'market_stats': {
            'avg_price_m2': int(avg_price_m2),
            'total_value': int(total_value)
        },
        'communes': communes_data[:10],
        'alerts': [{
            'type': 'info',
            'message': f'Datos cargados desde archivos JSON ({len(venta_props)} propiedades)'
        }]
    }

def _extract_superficie_from_atributos(atributos: str) -> Optional[int]:
    """Extract superficie from atributos string like '31 - 50 m² útiles'"""
    if not atributos:
        return None
    match = re.search(r'(\d+)\s*-\s*(\d+)\s*m²', atributos)
    if match:
        return int(match.group(2))  # Return max value
    match = re.search(r'(\d+)\s*m²', atributos)
    if match:
        return int(match.group(1))
    return None

def _extract_price_clp_from_json(precio_str: str) -> Optional[int]:
    """Extract CLP price from string, skip UF prices"""
    if not precio_str or 'UF' in precio_str.upper():
        return None
    price_clean = re.sub(r'[^\d]', '', precio_str)
    if not price_clean:
        return None
    try:
        return int(price_clean)
    except ValueError:
        return None

def _extract_comuna_from_ubicacion(ubicacion: str) -> Optional[str]:
    """Extract comuna from ubicacion string"""
    if not ubicacion:
        return None
    parts = ubicacion.split(',')
    if len(parts) >= 2:
        return parts[-2].strip()
    return None

def _json_prop_to_dict(prop: Dict) -> Dict:
    """Convert JSON property to standard dict format"""
    # Extract dormitorios and banos from atributos
    dormitorios = _extract_number_from_atributos(prop.get('atributos', ''), 'dormitorio')
    banos = _extract_number_from_atributos(prop.get('atributos', ''), 'baño')
    
    return {
        'id': prop.get('id', 0),
        'portal_id': prop.get('id'),
        'titulo': prop.get('titulo'),
        'precio': prop.get('precio_clp'),
        'precio_original': prop.get('precio'),
        'operacion': prop.get('operacion'),
        'tipo': prop.get('tipo'),
        'comuna': _extract_comuna_from_ubicacion(prop.get('ubicacion', '')),
        'direccion': prop.get('ubicacion'),
        'url': prop.get('url'),
        'superficie_total': prop.get('superficie_total'),
        'superficie_util': prop.get('superficie_total'),
        'dormitorios': dormitorios,
        'banos': banos,
        'precio_m2': prop.get('precio_m2'),
        'imagenes': [],
        'features': []
    }

def _extract_number_from_atributos(atributos: str, keyword: str) -> Optional[int]:
    """Extract number before keyword from atributos"""
    if not atributos:
        return None
    pattern = rf'(\d+)\s*(?:a\s*\d+\s*)?{keyword}'
    match = re.search(pattern, atributos, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None
