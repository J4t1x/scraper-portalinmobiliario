from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from dashboard.auth import user_manager
from data_loader import JSONDataLoader
from logger_config import get_logger

logger = get_logger(__name__)
bp = Blueprint('main', __name__)

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
    """Analytics avanzado"""
    return render_template('dashboard/analytics.html', user=current_user)

@bp.route('/api/properties')
@login_required
def api_properties():
    """API endpoint para listar propiedades desde JSON con filtros y paginación"""
    try:
        loader = JSONDataLoader()
        
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
        
        # Cargar propiedades con filtros
        properties = loader.load_by_filters(**filters)
        
        # Paginación
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        paginated = loader.paginate(properties, page, per_page)
        
        return jsonify({
            'success': True,
            'data': paginated['data'],
            'pagination': {
                'page': paginated['page'],
                'per_page': paginated['per_page'],
                'total': paginated['total'],
                'pages': paginated['total_pages']
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
    """API endpoint para estadísticas desde JSON"""
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
