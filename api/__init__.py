from flask import Blueprint, jsonify, request
import os
from flask_restx import Api
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache

# Blueprint and API
api_bp = Blueprint('api_rest', __name__, url_prefix='/api/v2')
api = Api(api_bp, version='2.0', title='Portal Inmobiliario API',
          description='API para consultar resultados y estadísticas del scraping con Flask-RESTX',
          doc='/docs',
          authorizations={
              'apikey': {
                  'type': 'apiKey',
                  'in': 'header',
                  'name': 'X-API-KEY'
              }
          },
          security='apikey')

# Rate Limiter setup (to be initialized by app)
limiter = Limiter(key_func=get_remote_address)

# Cache setup
cache = Cache()

def init_api(app):
    """Inicializa la API REST, Cache y Rate Limiting en la app."""
    limiter.init_app(app)
    
    redis_url = os.getenv('REDIS_URL')
    if redis_url:
        app.config['CACHE_TYPE'] = 'RedisCache'
        app.config['CACHE_REDIS_URL'] = redis_url
    else:
        app.config['CACHE_TYPE'] = 'SimpleCache'
        
    app.config['CACHE_DEFAULT_TIMEOUT'] = 300
    cache.init_app(app)
    
    # Import namespaces to register them
    from api.properties import ns as properties_ns
    from api.analytics import ns as analytics_ns
    from api.health import ns as health_ns
    from api.sys_cache import ns as cache_ns
    from api.opportunities import ns as opportunities_ns
    from api.agent import ns as agent_ns
    
    api.add_namespace(properties_ns, path='/properties')
    api.add_namespace(analytics_ns, path='/analytics')
    api.add_namespace(health_ns, path='/health')
    api.add_namespace(cache_ns, path='/cache')
    api.add_namespace(opportunities_ns, path='/opportunities')
    api.add_namespace(agent_ns, path='/agent')
    
    app.register_blueprint(api_bp)

# Decorador simple de auth
def token_required(f):
    from functools import wraps
    import os
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('X-API-KEY')
        expected_token = os.getenv('API_KEY', 'default-secret-key')
        if not token or token != expected_token:
            return {'message': 'Token es invalido o falta'}, 401
        return f(*args, **kwargs)
    return decorated
