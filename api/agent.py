"""
API endpoints for AI agent chat.
"""

from flask_restx import Namespace, Resource, fields
from flask import request
from api import token_required, limiter
from ai.agent import AnalyticsAgent, OLLAMA_URL, MODEL
from logger_config import get_logger
import requests

logger = get_logger(__name__)

ns = Namespace('agent', description='AI agent for analytics interpretation')

chat_request = ns.model('ChatRequest', {
    'question': fields.String(required=True, description='User question')
})

chat_response = ns.model('ChatResponse', {
    'question': fields.String(description='User question'),
    'response': fields.String(description='Agent response')
})

ollama_status = ns.model('OllamaStatus', {
    'status': fields.String(description='Ollama status (online/offline)'),
    'url': fields.String(description='Ollama URL'),
    'model': fields.String(description='Model name'),
    'models': fields.List(fields.Raw, description='Available models')
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
            
            # Build context from analytics, with graceful fallback
            context = {}
            try:
                from analytics import PropertyAnalytics
                with PropertyAnalytics() as analytics:
                    opportunities = analytics.get_top_opportunities(limit=10)
                    stats_by_comuna = analytics.get_avg_by_comuna()
                
                context = {
                    'opportunities': opportunities,
                    'stats_by_comuna': stats_by_comuna
                }
            except Exception as e:
                logger.warning(f"Could not load analytics context: {e}. Falling back to DatabaseLoader.")
                try:
                    from db_loader import DatabaseLoader
                    db_loader = DatabaseLoader()
                    stats = db_loader.get_stats()
                    context = {'stats': stats}
                    
                    try:
                        inv = db_loader.get_investment_opportunities()
                        context['opportunities'] = inv.get('top_5', [])
                        context['market_stats'] = inv.get('market_stats', {})
                    except Exception:
                        pass
                except Exception as e2:
                    logger.warning(f"Could not load DB context either: {e2}")
            
            agent = AnalyticsAgent()
            response = agent.ask(question, context)
            
            return {
                'question': question,
                'response': response
            }
        except Exception as e:
            logger.error(f"Error in agent chat: {e}")
            ns.abort(500, str(e))


@ns.route('/status')
class OllamaStatus(Resource):
    @ns.doc('ollama_status')
    @ns.marshal_with(ollama_status)
    def get(self):
        """Check Ollama server status and available models"""
        try:
            response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
            if response.ok:
                data = response.json()
                return {
                    'status': 'online',
                    'url': OLLAMA_URL,
                    'model': MODEL,
                    'models': data.get('models', [])
                }
            else:
                return {
                    'status': 'offline',
                    'url': OLLAMA_URL,
                    'model': MODEL,
                    'models': []
                }
        except Exception as e:
            logger.warning(f"Error checking Ollama status: {e}")
            return {
                'status': 'offline',
                'url': OLLAMA_URL,
                'model': MODEL,
                'models': []
            }
