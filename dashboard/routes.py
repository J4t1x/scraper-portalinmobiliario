from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from dashboard.auth import user_manager
from data_loader import JSONDataLoader
from logger_config import get_logger
from datetime import datetime
import subprocess
import threading
import sys
import os
import uuid

logger = get_logger(__name__)
bp = Blueprint('main', __name__)

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
    """Dashboard principal"""
    return render_template('dashboard/index.html', user=current_user)

@bp.route('/data')
@login_required
def data():
    """Explorador de datos"""
    try:
        loader = JSONDataLoader()
        stats = loader.get_stats()
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

@bp.route('/property/<property_id>')
@login_required
def property_detail(property_id):
    """Página de detalle de propiedad"""
    try:
        logger.info(f"Buscando propiedad con ID: {property_id}")
        loader = JSONDataLoader()
        properties = loader.load_all_json_files()
        
        logger.info(f"Total propiedades cargadas: {len(properties)}")
        
        # Buscar por ID
        prop = next((p for p in properties if p.get('id') == property_id), None)
        
        if not prop:
            logger.warning(f"Propiedad no encontrada: {property_id}")
            # Listar algunos IDs disponibles para debugging
            sample_ids = [p.get('id') for p in properties[:5]]
            logger.info(f"Sample IDs disponibles: {sample_ids}")
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
    """API endpoint para listar propiedades desde JSON con filtros y paginación"""
    try:
        loader = JSONDataLoader()

        # Parámetro de archivo específico
        file_param = request.args.get('file')

        # Cargar propiedades (archivo específico o todos)
        if file_param:
            properties = loader.load_specific_json_file(file_param)
        else:
            # Por defecto, cargar el archivo más reciente
            latest_file = loader.get_latest_json_file()
            if latest_file:
                properties = loader.load_specific_json_file(latest_file['filename'])
            else:
                properties = loader.load_all_json_files()

        # Parámetros de filtro
        filters = {
            'operacion': request.args.get('operacion'),
            'tipo': request.args.get('tipo'),
            'precio_min': request.args.get('precio_min', type=float),
            'precio_max': request.args.get('precio_max', type=float),
            'search': request.args.get('search')
        }

        # Filtrar None values
        filters = {k: v for k, v in filters.items() if v is not None}

        # Aplicar filtros
        if filters:
            filtered_properties = []
            for prop in properties:
                # Filtro por operación
                if filters.get('operacion') and prop.get('operacion') != filters['operacion']:
                    continue
                # Filtro por tipo
                if filters.get('tipo') and prop.get('tipo') != filters['tipo']:
                    continue
                # Filtro por rango de precio
                precio_clp = loader._extract_price_clp(prop.get('precio', ''))
                if filters.get('precio_min') is not None and (precio_clp is None or precio_clp < filters['precio_min']):
                    continue
                if filters.get('precio_max') is not None and (precio_clp is None or precio_clp > filters['precio_max']):
                    continue
                # Búsqueda por texto
                if filters.get('search'):
                    search_lower = filters['search'].lower()
                    titulo = prop.get('titulo', '').lower()
                    ubicacion = prop.get('ubicacion', '').lower()
                    if search_lower not in titulo and search_lower not in ubicacion:
                        continue
                filtered_properties.append(prop)
            properties = filtered_properties

        # Transformar datos para que coincidan con el template
        transformed_properties = []
        for prop in properties:
            # Extraer moneda y valor de precio
            precio = prop.get('precio', 'N/A')
            precio_moneda = ''
            precio_valor = precio

            if isinstance(precio, str) and precio != 'N/A':
                parts = precio.split()
                if len(parts) > 1:
                    precio_moneda = parts[0]
                    precio_valor = ' '.join(parts[1:])
                else:
                    precio_valor = precio

            # Mapear ubicacion a comuna
            comuna = prop.get('ubicacion', prop.get('comuna', 'N/A'))

            transformed_prop = {
                'id': prop.get('id', 'N/A'),
                'portal_id': prop.get('id', 'N/A'),
                'titulo': prop.get('titulo', 'N/A'),
                'precio': precio_valor,
                'precio_moneda': precio_moneda,
                'operacion': prop.get('operacion', 'N/A'),
                'tipo': prop.get('tipo', 'N/A'),
                'comuna': comuna,
                'scrapeado_en': prop.get('scrapeado_en', prop.get('fecha_scraping', None)),
                'url': prop.get('url', '#'),
                'direccion': prop.get('direccion', ''),
                'descripcion': prop.get('descripcion', ''),
                'features': prop.get('features', []),
                'publisher': prop.get('publisher', None)
            }
            transformed_properties.append(transformed_prop)

        # Paginación
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        paginated = loader.paginate(transformed_properties, page, per_page)

        return jsonify({
            'success': True,
            'data': paginated['data'],
            'pagination': {
                'page': paginated['page'],
                'per_page': paginated['per_page'],
                'total': paginated['total'],
                'pages': paginated['total_pages']
            },
            'file_info': {
                'filename': file_param if file_param else (latest_file['filename'] if latest_file else 'all'),
                'is_latest': not file_param and latest_file is not None
            }
        })
    except Exception as e:
        logger.error(f"Error en api_properties: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/properties/<property_id>')
@login_required
def api_property_detail(property_id):
    """API endpoint para detalle de propiedad desde JSON"""
    try:
        loader = JSONDataLoader()
        properties = loader.load_all_json_files()

        # Buscar por ID
        prop = next((p for p in properties if p.get('id') == property_id), None)

        if not prop:
            return jsonify({
                'success': False,
                'error': 'Propiedad no encontrada'
            }), 404

        # Transformar datos para que coincidan con el template
        precio = prop.get('precio', 'N/A')
        precio_moneda = ''
        precio_valor = precio

        if isinstance(precio, str) and precio != 'N/A':
            parts = precio.split()
            if len(parts) > 1:
                precio_moneda = parts[0]
                precio_valor = ' '.join(parts[1:])
            else:
                precio_valor = precio

        comuna = prop.get('ubicacion', prop.get('comuna', 'N/A'))

        transformed_prop = {
            'id': prop.get('id', 'N/A'),
            'portal_id': prop.get('id', 'N/A'),
            'titulo': prop.get('titulo', 'N/A'),
            'precio': precio_valor,
            'precio_moneda': precio_moneda,
            'operacion': prop.get('operacion', 'N/A'),
            'tipo': prop.get('tipo', 'N/A'),
            'comuna': comuna,
            'scrapeado_en': prop.get('scrapeado_en', prop.get('fecha_scraping', None)),
            'url': prop.get('url', '#'),
            'direccion': prop.get('direccion', ''),
            'descripcion': prop.get('descripcion', ''),
            'features': prop.get('features', []),
            'publisher': prop.get('publisher', None)
        }

        return jsonify({
            'success': True,
            'data': transformed_prop
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
    """API endpoint para estadísticas básicas desde JSON"""
    try:
        loader = JSONDataLoader()
        stats = loader.get_stats()
        
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
    """API endpoint para valores de filtros disponibles"""
    try:
        loader = JSONDataLoader()
        properties = loader.load_all_json_files()

        # Extraer valores únicos
        operaciones = list(set(p.get('operacion') for p in properties if p.get('operacion')))
        tipos = list(set(p.get('tipo') for p in properties if p.get('tipo')))
        comunas = list(set(p.get('ubicacion') for p in properties if p.get('ubicacion')))

        return jsonify({
            'success': True,
            'data': {
                'operaciones': sorted(operaciones),
                'tipos': sorted(tipos),
                'comunas': sorted(comunas)[:50]  # Top 50 comunas
            }
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
    """API endpoint para ejecutar scraping manual"""
    try:
        socketio = get_socketio()
        
        # Get parameters from JSON body
        data = request.json or {}
        operacion = data.get('operacion', 'venta')
        tipo = data.get('tipo', 'departamento')
        max_pages = data.get('max_pages', 10)
        formato = data.get('formato', 'json')
        scrape_details = data.get('scrape_details', True)
        verbose = data.get('verbose', False)
        
        # Generate unique scraping ID
        scraping_id = str(uuid.uuid4())
        
        # Use python3 explicitly
        python_cmd = sys.executable or 'python3'
        
        # Build command
        cmd = [
            python_cmd,
            'main.py',
            '--operacion', operacion,
            '--tipo', tipo,
            '--max-pages', str(max_pages),
            '--formato', formato
        ]
        
        if scrape_details:
            cmd.append('--scrape-details')
            cmd.extend(['--max-detail-properties', '100'])
        
        if verbose:
            cmd.append('--verbose')
        
        logger.info(f"Iniciando scraping manual: {' '.join(cmd)}")
        
        # Verify main.py exists
        if not os.path.exists('main.py'):
            error_msg = "main.py not found in current directory"
            logger.error(error_msg)
            return jsonify({
                'success': False,
                'error': error_msg
            }), 500
        
        # Run scraping in background thread with real-time log streaming
        def run_scraping():
            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                # Stream output in real-time
                for line in process.stdout:
                    line = line.strip()
                    if line:
                        if socketio:
                            socketio.emit('scraping_log', {
                                'scraping_id': scraping_id,
                                'log': line,
                                'timestamp': datetime.utcnow().isoformat()
                            })
                
                process.wait()
                
                # Send completion message
                if socketio:
                    socketio.emit('scraping_complete', {
                        'scraping_id': scraping_id,
                        'return_code': process.returncode,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                
                logger.info(f"Scraping manual completado. Return code: {process.returncode}")
                
            except subprocess.TimeoutExpired:
                logger.error("Scraping manual timeout después de 1 hora")
                if socketio:
                    socketio.emit('scraping_error', {
                        'scraping_id': scraping_id,
                        'error': 'Timeout después de 1 hora',
                        'timestamp': datetime.utcnow().isoformat()
                    })
            except FileNotFoundError:
                logger.error(f"Comando no encontrado: {python_cmd}")
                if socketio:
                    socketio.emit('scraping_error', {
                        'scraping_id': scraping_id,
                        'error': f'Comando no encontrado: {python_cmd}',
                        'timestamp': datetime.utcnow().isoformat()
                    })
            except Exception as e:
                logger.error(f"Error ejecutando scraping manual: {e}")
                if socketio:
                    socketio.emit('scraping_error', {
                        'scraping_id': scraping_id,
                        'error': str(e),
                        'timestamp': datetime.utcnow().isoformat()
                    })
        
        thread = threading.Thread(target=run_scraping, daemon=True)
        thread.start()
        
        return jsonify({
            'success': True,
            'message': f'Scraping manual iniciado para {operacion} {tipo}. Los logs se mostrarán en tiempo real.',
            'data': {
                'scraping_id': scraping_id,
                'operacion': operacion,
                'tipo': tipo,
                'max_pages': max_pages,
                'formato': formato,
                'command': ' '.join(cmd)
            }
        })
    except Exception as e:
        logger.error(f"Error en api_run_manual_scraping: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/analytics/chat', methods=['POST'])
@login_required
def api_analytics_chat():
    """API endpoint para interactuar con el agente de analítica (OpenAI)"""
    try:
        from api.openai_agent import AnalyticsAgent
        data = request.json or {}
        message = data.get('message', '')
        
        if not message:
            return jsonify({'success': False, 'error': 'El mensaje no puede estar vacío'}), 400
            
        agent = AnalyticsAgent()
        response_text = agent.generate_response(message)
        
        return jsonify({
            'success': True,
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
