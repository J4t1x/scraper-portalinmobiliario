"""
API endpoints for AI agent chat.
"""

from flask_restx import Namespace, Resource, fields
from flask import request
from api import token_required, limiter
from ai.agent import AnalyticsAgent
from analytics import PropertyAnalytics
from logger_config import get_logger

logger = get_logger(__name__)

ns = Namespace('agent', description='AI agent for analytics interpretation')

chat_request = ns.model('ChatRequest', {
    'question': fields.String(required=True, description='User question')
})

chat_response = ns.model('ChatResponse', {
    'question': fields.String(description='User question'),
    'response': fields.String(description='Agent response')
})


@ns.route('/chat')
class AgentChat(Resource):
    @ns.doc('chat_with_agent', security='apikey')
    @ns.expect(chat_request)
    @ns.marshal_with(chat_response)
    @token_required
    @limiter.limit("10 per minute")
    def post(self):
        """Chat with the AI agent about investment opportunities"""
        try:
            data = request.get_json()
            question = data.get('question', '')
            
            if not question:
                ns.abort(400, 'Question is required')
            
            with PropertyAnalytics() as analytics:
                opportunities = analytics.get_top_opportunities(limit=10)
                stats_by_comuna = analytics.get_avg_by_comuna()
            
            context = {
                'opportunities': opportunities,
                'stats_by_comuna': stats_by_comuna
            }
            
            agent = AnalyticsAgent()
            response = agent.ask(question, context)
            
            return {
                'question': question,
                'response': response
            }
        except Exception as e:
            logger.error(f"Error in agent chat: {e}")
            ns.abort(500, str(e))
