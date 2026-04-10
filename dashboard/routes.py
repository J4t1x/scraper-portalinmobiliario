from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from dashboard.auth import user_manager

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
    return render_template('dashboard/data.html', user=current_user)

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
