"""
AI agent for interpreting analytics insights using Ollama.
Implementa lazy loading para reducir RAM en idle (ahorra 1.2GB).
Soporte completo para Small Language Models (SLMs) con gestión dinámica.
"""

import logging
import requests
import os
import time
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
# Modelo por defecto elegido tras benchmark (scripts/test_ollama_params.py):
# qwen2.5-coder:0.5b ofrece TTFT ~950ms y total ~1.6s en CPU, ideal para UI fluida.
MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:0.5b")

# Import SLM manager for model management
try:
    from ai.slm_manager import SLMManager, SLMCatalog
    SLM_SUPPORT = True
except ImportError:
    logger.warning("SLM Manager not available, using basic mode")
    SLM_SUPPORT = False


class AnalyticsAgent:
    """
    AI agent for analytics interpretation with lazy loading.
    
    El modelo Ollama solo se carga cuando se hace la primera consulta,
    reduciendo RAM en idle de 2.2GB a 1.0GB si no se usa IA.
    """
    
    def __init__(self, model: str = MODEL, ollama_url: str = OLLAMA_URL):
        self.model = model
        self.ollama_url = ollama_url
        self._model_loaded = False
        self._ollama_available = None
        self._last_check = 0
        self._check_interval = 60  # Re-check availability every 60 seconds
        
        # SLM Manager integration
        self.slm_manager = SLMManager(ollama_url) if SLM_SUPPORT else None
        self._model_cache = {}  # Cache for model metadata
    
    def _ensure_loaded(self) -> bool:
        """
        Carga el modelo Ollama solo cuando se necesita (lazy loading).
        Reintenta periódicamente si Ollama no estaba disponible.
        
        Returns:
            True si el modelo está disponible, False si no
        """
        now = time.time()
        
        # Re-check if previously unavailable and enough time has passed
        if self._ollama_available is False and (now - self._last_check) > self._check_interval:
            self._ollama_available = None  # Reset to force re-check
        
        # If already verified and available, return cached result
        if self._ollama_available is True and self._model_loaded:
            return True
        
        self._last_check = now
        
        for attempt in range(3):
            try:
                # Verificar si Ollama está corriendo
                health_url = f"{self.ollama_url}/api/tags"
                response = requests.get(health_url, timeout=5)
                response.raise_for_status()
                
                if not self._model_loaded:
                    logger.info(f"🤖 Cargando modelo Ollama '{self.model}' (primera vez)...")
                    
                    # Pre-cargar modelo en memoria con una consulta de prueba
                    test_response = requests.post(
                        f"{self.ollama_url}/api/generate",
                        json={
                            "model": self.model,
                            "prompt": "test",
                            "stream": False
                        },
                        timeout=60
                    )
                    test_response.raise_for_status()
                    
                    self._model_loaded = True
                    logger.info(f"✅ Modelo '{self.model}' cargado y listo")
                
                self._ollama_available = True
                return True
                
            except requests.exceptions.ConnectionError as e:
                if attempt < 2:
                    logger.warning(f"⚠️ Ollama no disponible (intento {attempt + 1}/3): {e}. Reintentando...")
                    time.sleep(2 * (attempt + 1))
                else:
                    logger.warning(f"⚠️ Ollama no disponible después de 3 intentos: {e}. Agente IA deshabilitado.")
                    self._ollama_available = False
                    return False
            except Exception as e:
                logger.warning(f"⚠️ Ollama error: {e}. Agente IA deshabilitado.")
                self._ollama_available = False
                return False
    
    def check_status(self) -> Dict[str, Any]:
        """
        Check Ollama server status and available models.
        Enhanced with SLM metadata.
        
        Returns:
            Dict with status info including SLM details
        """
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.ok:
                data = response.json()
                models_list = data.get('models', [])
                
                # Enhance with SLM metadata if available
                if self.slm_manager:
                    enhanced_models = []
                    for m in models_list:
                        model_name = m.get('name', '')
                        catalog_model = SLMCatalog.get_by_name(model_name)
                        if catalog_model:
                            enhanced_models.append({
                                'name': model_name,
                                'display_name': catalog_model.display_name,
                                'size': m.get('size', 0),
                                'size_mb': m.get('size', 0) // (1024 * 1024),
                                'parameters': catalog_model.parameters,
                                'performance_score': catalog_model.performance_score,
                                'speed_score': catalog_model.speed_score,
                                'quality_score': catalog_model.quality_score,
                                'tasks': [t.value for t in catalog_model.tasks],
                                'recommended_for': catalog_model.recommended_for
                            })
                        else:
                            enhanced_models.append({
                                'name': model_name,
                                'display_name': model_name,
                                'size': m.get('size', 0),
                                'size_mb': m.get('size', 0) // (1024 * 1024)
                            })
                    models_list = enhanced_models
                
                return {
                    'status': 'online',
                    'url': self.ollama_url,
                    'model': self.model,
                    'models': models_list,
                    'slm_support': SLM_SUPPORT
                }
        except Exception as e:
            logger.debug(f"Ollama status check failed: {e}")
        
        return {
            'status': 'offline',
            'url': self.ollama_url,
            'model': self.model,
            'models': [],
            'slm_support': SLM_SUPPORT
        }
    
    def switch_model(self, model_name: str) -> bool:
        """
        Switch to a different model.
        
        Args:
            model_name: Name of the model to switch to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Verify model is available
            if self.slm_manager:
                installed = self.slm_manager.get_installed_models(refresh=True)
                if not any(m.name == model_name for m in installed):
                    logger.warning(f"Model {model_name} not installed")
                    return False
            
            # Test model with a simple query
            test_response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": model_name,
                    "prompt": "test",
                    "stream": False
                },
                timeout=30
            )
            
            if test_response.ok:
                self.model = model_name
                self._model_loaded = True
                logger.info(f"Switched to model: {model_name}")
                return True
            else:
                logger.error(f"Failed to switch to {model_name}: {test_response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error switching model: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.
        
        Returns:
            Dict with model metadata
        """
        info = {
            'name': self.model,
            'loaded': self._model_loaded,
            'available': self._ollama_available
        }
        
        if self.slm_manager:
            catalog_model = SLMCatalog.get_by_name(self.model)
            if catalog_model:
                info.update({
                    'display_name': catalog_model.display_name,
                    'parameters': catalog_model.parameters,
                    'size_mb': catalog_model.size_mb,
                    'performance_score': catalog_model.performance_score,
                    'speed_score': catalog_model.speed_score,
                    'quality_score': catalog_model.quality_score,
                    'tasks': [t.value for t in catalog_model.tasks],
                    'recommended_for': catalog_model.recommended_for
                })
        
        return info
    
    def ask(self, question: str, context: Dict[str, Any]) -> str:
        """
        Ask the agent a question with analytics context.
        Usa lazy loading: el modelo solo se carga en la primera consulta.
        Uses the /api/chat endpoint for better conversational quality.
        
        Args:
            question: User's question
            context: Analytics insights (opportunities, stats, etc.)
            
        Returns:
            Agent's response
        """
        # Lazy loading: cargar modelo solo cuando se necesita
        if not self._ensure_loaded():
            return "⚠️ El agente IA no está disponible en este momento. Por favor, verifica que Ollama esté corriendo."
        
        system_prompt = self._build_system_prompt(context)
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": question}
                    ],
                    "stream": False,
                    "options": {
                        # Parámetros optimizados vía scripts/test_ollama_params.py
                        # (perfil "fluido": TTFT ~950ms, total ~1.6s, score 0.79)
                        "temperature": 0.2,
                        "top_p": 0.8,
                        "top_k": 20,
                        "num_predict": 180,
                        "num_ctx": 2048,
                        "repeat_penalty": 1.15,
                        "num_thread": 4
                    }
                },
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("message", {}).get("content", "No se pudo generar respuesta.")
        
        except requests.exceptions.Timeout:
            logger.error("Timeout calling Ollama")
            return "La solicitud tardó demasiado. Intenta con una pregunta más simple."
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Ollama: {e}")
            # Reset availability to force re-check
            self._ollama_available = None
            return "Lo siento, no pude procesar tu pregunta en este momento. Reintentando conexión con Ollama."
    
    def ask_stream(self, question: str, context: Dict[str, Any]):
        """
        Ask the agent a question with streaming response.
        Yields chunks of the response as they are generated.
        
        Args:
            question: User's question
            context: Analytics insights (opportunities, stats, etc.)
            
        Yields:
            Response chunks as they arrive
        """
        # Lazy loading: cargar modelo solo cuando se necesita
        if not self._ensure_loaded():
            yield "⚠️ El agente IA no está disponible en este momento. Por favor, verifica que Ollama esté corriendo."
            return
        
        system_prompt = self._build_system_prompt(context)
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": question}
                    ],
                    "stream": True,
                    "options": {
                        # Parámetros optimizados vía scripts/test_ollama_params.py
                        "temperature": 0.2,
                        "top_p": 0.8,
                        "top_k": 20,
                        "num_predict": 180,
                        "num_ctx": 2048,
                        "repeat_penalty": 1.15,
                        "num_thread": 4
                    }
                },
                stream=True,
                timeout=120
            )
            response.raise_for_status()
            
            import json
            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        if "message" in chunk:
                            content = chunk["message"].get("content", "")
                            if content:
                                yield content
                    except json.JSONDecodeError:
                        continue
        
        except requests.exceptions.Timeout:
            logger.error("Timeout calling Ollama stream")
            yield "\n\n⚠️ La solicitud tardó demasiado."
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Ollama stream: {e}")
            self._ollama_available = None
            yield "\n\n⚠️ Error de conexión con Ollama."
    
    def generate_response(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None,
        use_cothssum: bool = True,
        return_trace: bool = False
    ) -> str | Dict[str, Any]:
        """
        Generate a response using context from the database.
        Compatible API for use from dashboard routes.
        
        Args:
            user_message: User's question
            context: Optional pre-built context dict
            use_cothssum: Whether to use CoTHSSum pipeline (default: True)
            return_trace: Whether to return full trace with metadata
            
        Returns:
            Agent's response string or dict with response + trace
        """
        if context is None:
            context = self._build_context_from_db()
        
        if use_cothssum:
            return self.ask_cothssum(user_message, context, return_trace=return_trace)
        else:
            return self.ask(user_message, context)
    
    def ask_cothssum(
        self,
        question: str,
        context: Dict[str, Any],
        return_trace: bool = False
    ) -> str | Dict[str, Any]:
        """
        Ask the agent using CoTHSSum hierarchical pipeline.
        
        CoTHSSum ejecuta un pipeline de 3 capas:
        - Capa 1: Micro-insights (análisis fragmentado con Chain-of-Thought)
        - Capa 2: Patrones globales (agregación y síntesis)
        - Capa 3: Conclusiones (razonamiento final y decisiones)
        
        Args:
            question: User's question
            context: Analytics insights (opportunities, stats, etc.)
            return_trace: Whether to return full trace with metadata
            
        Returns:
            Agent's response string or dict with response + full trace
        """
        # Lazy loading: cargar modelo solo cuando se necesita
        if not self._ensure_loaded():
            if return_trace:
                return {
                    'response': "⚠️ El agente IA no está disponible en este momento. Por favor, verifica que Ollama esté corriendo.",
                    'trace': None,
                    'error': 'Ollama not available'
                }
            return "⚠️ El agente IA no está disponible en este momento. Por favor, verifica que Ollama esté corriendo."
        
        try:
            from ai.cothssum import CoTHSSumPipeline, format_cothssum_trace
            
            # Inicializar pipeline CoTHSSum
            pipeline = CoTHSSumPipeline(agent=self, max_chunk_size=5)
            
            # Ejecutar pipeline
            result = pipeline.execute(question, context)
            
            if return_trace:
                # Retornar respuesta completa con trace y métricas
                return {
                    'response': result.layer3_conclusion,
                    'trace': format_cothssum_trace(result),
                    'metadata': result.metadata,
                    'layer1_insights': result.layer1_micro_insights,
                    'layer2_patterns': result.layer2_global_patterns,
                    'layer3_reasoning': result.layer3_reasoning,
                    'trace_id': result.trace_id,
                    # Métricas granulares por capa
                    'layer1_metrics': {
                        'duration_ms': result.layer1_metrics.duration_ms,
                        'tokens_estimated': result.layer1_metrics.tokens_estimated,
                        'success': result.layer1_metrics.success,
                        'cache_hit': result.layer1_metrics.cache_hit
                    },
                    'layer2_metrics': {
                        'duration_ms': result.layer2_metrics.duration_ms,
                        'tokens_estimated': result.layer2_metrics.tokens_estimated,
                        'success': result.layer2_metrics.success,
                        'cache_hit': result.layer2_metrics.cache_hit
                    },
                    'layer3_metrics': {
                        'duration_ms': result.layer3_metrics.duration_ms,
                        'tokens_estimated': result.layer3_metrics.tokens_estimated,
                        'success': result.layer3_metrics.success,
                        'cache_hit': result.layer3_metrics.cache_hit
                    }
                }
            else:
                # Retornar solo la conclusión final
                return result.layer3_conclusion
                
        except ImportError as e:
            logger.warning(f"CoTHSSum no disponible: {e}. Usando modo estándar.")
            # Fallback al modo estándar
            return self.ask(question, context)
        except Exception as e:
            logger.error(f"Error en CoTHSSum pipeline: {e}")
            # Fallback al modo estándar
            return self.ask(question, context)
    
    def _build_context_from_db(self) -> Dict[str, Any]:
        """Build context from database using DatabaseLoader."""
        context = {}
        try:
            from db_loader import DatabaseLoader
            db_loader = DatabaseLoader()
            
            stats = db_loader.get_stats()
            context['stats'] = stats
            
            try:
                opportunities = db_loader.get_investment_opportunities()
                context['opportunities'] = opportunities.get('top_5', [])
                context['market_stats'] = opportunities.get('market_stats', {})
                context['communes'] = opportunities.get('communes', [])
            except Exception as e:
                logger.warning(f"Could not load investment opportunities: {e}")
            
        except Exception as e:
            logger.warning(f"Could not build context from DB: {e}")
        
        return context
    
    def _build_system_prompt(self, context: Dict[str, Any]) -> str:
        """Build system prompt for the agent.

        Delega en ``ai.prompts`` para mantener una única fuente de verdad
        compartida con el harness de tuning (scripts/test_ollama_params.py).
        """
        from ai.prompts import build_analytics_system_prompt
        return build_analytics_system_prompt(context)

    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context for the prompt (delegado a ai.prompts)."""
        from ai.prompts import format_analytics_context
        return format_analytics_context(context)
