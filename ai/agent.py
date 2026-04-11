"""
AI agent for interpreting analytics insights using Ollama.
Implementa lazy loading para reducir RAM en idle (ahorra 1.2GB).
"""

import logging
import requests
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:1.5b")


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
    
    def _ensure_loaded(self) -> bool:
        """
        Carga el modelo Ollama solo cuando se necesita (lazy loading).
        
        Returns:
            True si el modelo está disponible, False si no
        """
        # Si ya verificamos disponibilidad, retornar resultado cacheado
        if self._ollama_available is not None:
            return self._ollama_available
        
        try:
            # Verificar si Ollama está corriendo
            health_url = self.ollama_url.replace("/api/generate", "/api/tags")
            response = requests.get(health_url, timeout=5)
            response.raise_for_status()
            
            if not self._model_loaded:
                logger.info(f"🤖 Cargando modelo Ollama '{self.model}' (primera vez)...")
                
                # Pre-cargar modelo en memoria con una consulta de prueba
                test_response = requests.post(
                    self.ollama_url,
                    json={
                        "model": self.model,
                        "prompt": "test",
                        "stream": False
                    },
                    timeout=30
                )
                test_response.raise_for_status()
                
                self._model_loaded = True
                logger.info(f"✅ Modelo '{self.model}' cargado y listo")
            
            self._ollama_available = True
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Ollama no disponible: {e}. Agente IA deshabilitado.")
            self._ollama_available = False
            return False
    
    def ask(self, question: str, context: Dict[str, Any]) -> str:
        """
        Ask the agent a question with analytics context.
        Usa lazy loading: el modelo solo se carga en la primera consulta.
        
        Args:
            question: User's question
            context: Analytics insights (opportunities, stats, etc.)
            
        Returns:
            Agent's response
        """
        # Lazy loading: cargar modelo solo cuando se necesita
        if not self._ensure_loaded():
            return "⚠️ El agente IA no está disponible en este momento. Por favor, verifica que Ollama esté corriendo."
        
        prompt = self._build_prompt(question, context)
        
        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "max_tokens": 500
                    }
                },
                timeout=30
            )
            response.raise_for_status()
            
            return response.json()["response"]
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Ollama: {e}")
            return "Lo siento, no pude procesar tu pregunta en este momento."
    
    def _build_prompt(self, question: str, context: Dict[str, Any]) -> str:
        """Build prompt for the agent."""
        return f"""Eres un asistente de analítica inmobiliaria experto.

Tu tarea es responder preguntas sobre oportunidades de inversión en propiedades.

CONTEXTO (insights ya calculados):
{self._format_context(context)}

PREGUNTA DEL USUARIO:
{question}

INSTRUCCIONES:
- Responde de forma concisa y clara
- Usa los datos del contexto, NO inventes números
- Si no tienes suficiente información, dilo
- Menciona las mejores oportunidades si es relevante
- Usa formato markdown para listas y énfasis

RESPUESTA:"""
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context for the prompt."""
        formatted = []
        
        if 'opportunities' in context:
            formatted.append(f"Total de oportunidades: {len(context['opportunities'])}")
            
            if context['opportunities']:
                formatted.append("\nTop 5 oportunidades:")
                for i, opp in enumerate(context['opportunities'][:5], 1):
                    formatted.append(
                        f"{i}. {opp.get('titulo', 'N/A')} - {opp.get('comuna', 'N/A')} "
                        f"(Score: {opp.get('score', 0):.1f}, "
                        f"Precio/m²: ${opp.get('precio_m2_propiedad', 0):,.0f}, "
                        f"Ahorro: {opp.get('diferencia_porcentual', 0):.1f}%)"
                    )
        
        if 'stats_by_comuna' in context:
            formatted.append("\n\nEstadísticas por comuna:")
            for stat in context['stats_by_comuna'][:5]:
                formatted.append(
                    f"- {stat.get('comuna', 'N/A')}: "
                    f"Promedio ${stat.get('avg_precio_m2', 0):,.0f}/m² "
                    f"({stat.get('total_propiedades', 0)} propiedades)"
                )
        
        return "\n".join(formatted) if formatted else "No hay datos disponibles"
