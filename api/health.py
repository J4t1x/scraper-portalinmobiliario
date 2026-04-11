from flask_restx import Namespace, Resource
from logger_config import get_logger

logger = get_logger(__name__)

ns = Namespace('health', description='Estado de los servicios')

@ns.route('')
class HealthCheck(Resource):
    @ns.doc('health_check')
    def get(self):
        """Monitor de salud del sistema, incluyendo PostgreSQL y Redis (cuando aplique)"""
        try:
            status = {
                'success': True,
                'data': {
                    'status': 'healthy',
                    'services': {
                        'api': 'online'
                    }
                }
            }
            # En el fututo comprobar estado de Redis y DB aquí (SPEC-019)
            return status
        except Exception as e:
            logger.error(f"Error checking health: {e}")
            return {
                'success': False,
                'data': {
                    'status': 'unhealthy',
                    'error': str(e)
                }
            }, 500
