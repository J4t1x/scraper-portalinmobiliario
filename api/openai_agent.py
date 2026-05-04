import requests
from config_flask import FlaskConfig
from logger_config import get_logger
import json

logger = get_logger(__name__)

class AnalyticsAgent:
    """
    Analytics Agent that uses Ollama for AI-powered data analysis.
    Uses DatabaseLoader as primary data source (falls back to JSONDataLoader).
    """
    
    def __init__(self):
        self.ollama_url = FlaskConfig.OLLAMA_URL
        self.model = FlaskConfig.OLLAMA_MODEL
        self.client = self._test_connection()
        
    def _test_connection(self) -> bool:
        """Verifica que Ollama esté disponible"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info(f"✅ Ollama conectado en {self.ollama_url}")
                return True
            return False
        except Exception as e:
            logger.warning(f"No se pudo conectar a Ollama en {self.ollama_url}: {e}")
            return False
    
    def _get_stats_data(self) -> str:
        """Get stats from database, falling back to JSON files."""
        try:
            from db_loader import DatabaseLoader
            db_loader = DatabaseLoader()
            stats = db_loader.get_stats()
            
            # Try to get investment data too
            try:
                opportunities = db_loader.get_investment_opportunities()
                stats['market_stats'] = opportunities.get('market_stats', {})
                stats['top_communes'] = opportunities.get('communes', [])[:5]
                stats['top_opportunities'] = len(opportunities.get('top_5', []))
            except Exception as e:
                logger.debug(f"Could not load investment data: {e}")
            
            return json.dumps(stats, indent=2, ensure_ascii=False, default=str)
            
        except Exception as e:
            logger.warning(f"Error obteniendo datos de BD: {e}. Fallback a JSON.")
            try:
                from data_loader import JSONDataLoader
                loader = JSONDataLoader()
                try:
                    advanced_stats = loader.get_advanced_stats()
                except Exception:
                    advanced_stats = loader.get_stats()
                return json.dumps(advanced_stats, indent=2, ensure_ascii=False, default=str)
            except Exception as e2:
                logger.error(f"Error obteniendo datos JSON: {e2}")
                return '{"error": "No se pudieron cargar datos"}'
    
    def generate_response(self, user_message: str) -> str:
        if not self.client:
            # Retry connection
            self.client = self._test_connection()
            if not self.client:
                return "Error: El Agente de Analítica no está disponible. Verifica que Ollama esté corriendo y accesible."
            
        try:
            stats_json = self._get_stats_data()
            
            system_prompt = f"""
            Eres un agente experto en análisis de datos del mercado inmobiliario chileno. 
            Trabajas dentro del dashboard del 'Portal Inmobiliario Scraper'.
            Tienes acceso al siguiente resumen estadístico detallado de las propiedades que han sido scrapeadas:
            
            ```json
            {stats_json}
            ```
            
            Instrucciones para tus respuestas:
            1. Responde a las preguntas del usuario basándote SIEMPRE en los datos proporcionados arriba.
            2. Extrae conclusiones útiles de los datos (ej: zonas más caras, promedios, relación precio/m2).
            3. Si te preguntan algo que no puedes responder con este resumen, indícalo educadamente.
            4. Forma de escribir: Sé profesional, analítico, conciso y utiliza formato Markdown para listas, negritas y ordenar tu respuesta.
            """
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 600
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/chat",
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("message", {}).get("content", "No se pudo generar respuesta.")
        except requests.exceptions.Timeout:
            logger.error("Timeout al conectar con Ollama")
            return "La solicitud tardó demasiado. Intenta con una pregunta más simple o verifica que Ollama esté corriendo."
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión con Ollama: {str(e)}")
            self.client = False  # Force re-check on next call
            return "No se pudo conectar con Ollama. Verifica que el servicio esté corriendo."
        except Exception as e:
            logger.error(f"Error generando respuesta con Ollama: {str(e)}")
            return "Ocurrió un error al procesar tu consulta con la IA. Verifica los logs para más detalles."
