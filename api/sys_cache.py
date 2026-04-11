from flask_restx import Namespace, Resource
from api import token_required, limiter, cache
from logger_config import get_logger

logger = get_logger(__name__)

ns = Namespace('cache', description='Operaciones sobre el módulo de Cache')

@ns.route('/invalidate')
class CacheInvalidate(Resource):
    @ns.doc('invalidate_cache', security='apikey')
    @token_required
    @limiter.limit("5 per minute")
    def delete(self):
        """Invalida/Limpia todo el cache (Utilizado tras un job del scraper)"""
        try:
            cache.clear()
            logger.info("El cache fue limpiado via API")
            return {
                'success': True,
                'message': 'Cache limpiado exitosamente'
            }
        except Exception as e:
            logger.error(f"Error limpiando cache: {e}")
            ns.abort(500, str(e))
