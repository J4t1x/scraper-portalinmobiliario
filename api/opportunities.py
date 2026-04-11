"""
API endpoints for opportunities.
"""

from flask_restx import Namespace, Resource, fields
from flask import request
from api import token_required, limiter, cache
from analytics import PropertyAnalytics, run_analytics_pipeline
from logger_config import get_logger

logger = get_logger(__name__)

ns = Namespace('opportunities', description='Investment opportunities detection and management')

opportunity_model = ns.model('Opportunity', {
    'id': fields.Integer(description='Opportunity ID'),
    'property_id': fields.String(description='Property ID'),
    'tipo_oportunidad': fields.String(description='Opportunity type'),
    'score': fields.Float(description='Opportunity score (0-100)'),
    'precio_m2_propiedad': fields.Float(description='Property price per m²'),
    'precio_m2_promedio_comuna': fields.Float(description='Average price per m² in comuna'),
    'diferencia_porcentual': fields.Float(description='Percentage difference'),
    'razon': fields.String(description='Reason for opportunity'),
    'titulo': fields.String(description='Property title'),
    'precio': fields.Integer(description='Property price'),
    'comuna': fields.String(description='Comuna'),
    'tipo': fields.String(description='Property type'),
    'url': fields.String(description='Property URL')
})


@ns.route('/')
class OpportunitiesList(Resource):
    @ns.doc('get_opportunities', security='apikey')
    @ns.param('limit', 'Maximum number of opportunities to return', type=int, default=20)
    @ns.param('tipo', 'Filter by opportunity type', type=str)
    @ns.param('comuna', 'Filter by comuna', type=str)
    @token_required
    @limiter.limit("30 per minute")
    @cache.cached(timeout=300, query_string=True)
    @ns.marshal_list_with(opportunity_model)
    def get(self):
        """Get top investment opportunities"""
        try:
            limit = request.args.get('limit', 20, type=int)
            tipo = request.args.get('tipo', None, type=str)
            comuna = request.args.get('comuna', None, type=str)
            
            with PropertyAnalytics() as analytics:
                opportunities = analytics.get_top_opportunities(limit=limit)
            
            if tipo:
                opportunities = [o for o in opportunities if o.get('tipo') == tipo]
            
            if comuna:
                opportunities = [o for o in opportunities if o.get('comuna') == comuna]
            
            return opportunities
        except Exception as e:
            logger.error(f"Error fetching opportunities: {e}")
            ns.abort(500, str(e))


@ns.route('/stats')
class OpportunitiesStats(Resource):
    @ns.doc('get_opportunity_stats', security='apikey')
    @token_required
    @limiter.limit("30 per minute")
    @cache.cached(timeout=600)
    def get(self):
        """Get opportunity statistics"""
        try:
            with PropertyAnalytics() as analytics:
                result = analytics.session.execute("""
                    SELECT 
                        tipo_oportunidad,
                        COUNT(*) as total,
                        AVG(score) as avg_score,
                        AVG(diferencia_porcentual) as avg_diff_pct
                    FROM opportunities
                    GROUP BY tipo_oportunidad
                    ORDER BY avg_score DESC
                """)
                
                stats = [
                    {
                        'tipo': row[0],
                        'total': row[1],
                        'avg_score': float(row[2]) if row[2] else 0,
                        'avg_diff_pct': float(row[3]) if row[3] else 0
                    }
                    for row in result
                ]
            
            return {
                'success': True,
                'stats': stats
            }
        except Exception as e:
            logger.error(f"Error fetching opportunity stats: {e}")
            ns.abort(500, str(e))


@ns.route('/run-analytics')
class RunAnalytics(Resource):
    @ns.doc('run_analytics_pipeline', security='apikey')
    @token_required
    @limiter.limit("5 per hour")
    def post(self):
        """Run analytics pipeline manually"""
        try:
            logger.info("Running analytics pipeline via API...")
            result = run_analytics_pipeline()
            
            return {
                'success': True,
                'result': result
            }
        except Exception as e:
            logger.error(f"Error running analytics pipeline: {e}")
            ns.abort(500, str(e))
