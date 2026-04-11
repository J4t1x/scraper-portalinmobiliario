from flask_restx import Namespace, Resource
from api import token_required, limiter, cache
from data_loader import JSONDataLoader
from logger_config import get_logger

logger = get_logger(__name__)

ns = Namespace('analytics', description='Analytics y estadísticas de propiedades')

@ns.route('/stats')
class Stats(Resource):
    @ns.doc('get_stats', security='apikey')
    @token_required
    @limiter.limit("30 per minute")
    @cache.cached(timeout=300, query_string=True)
    def get(self):
        """Estadísticas básicas del dataset actual"""
        try:
            loader = JSONDataLoader()
            stats = loader.get_stats()
            return {
                'success': True,
                'data': stats
            }
        except Exception as e:
            logger.error(f"Error fetching stats: {e}")
            ns.abort(500, str(e))

@ns.route('/advanced-stats')
class AdvancedStats(Resource):
    @ns.doc('get_advanced_stats', security='apikey')
    @token_required
    @limiter.limit("15 per minute")
    @cache.cached(timeout=600, query_string=True)
    def get(self):
        """Estadísticas detalladas incluyendo promedios y calidad"""
        try:
            loader = JSONDataLoader()
            stats = loader.get_advanced_stats()
            return {
                'success': True,
                'data': stats
            }
        except Exception as e:
            logger.error(f"Error fetching advanced stats: {e}")
            ns.abort(500, str(e))
