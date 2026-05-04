"""
CoTHSSum: Hierarchical + Chain-of-Thought para Analytics AI

Implementa un pipeline de 3 capas para razonamiento estructurado:
- Capa 1: Micro-insights (análisis fragmentado con Chain-of-Thought)
- Capa 2: Patrones globales (agregación y síntesis)
- Capa 3: Conclusiones (razonamiento final y decisiones)

Cada capa usa prompts simples con salidas JSON estructuradas,
permitiendo trazabilidad completa y mejor coherencia en respuestas.
"""

import logging
import json
import re
import time
import hashlib
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from functools import lru_cache

logger = logging.getLogger(__name__)

# Pydantic schemas for JSON validation
try:
    from pydantic import BaseModel, validator, Field
    PYDANTIC_AVAILABLE = True
except ImportError:
    logger.warning("Pydantic not available, JSON validation disabled")
    PYDANTIC_AVAILABLE = False
    
    # Fallback classes if Pydantic is not available
    class BaseModel:
        pass
    
    def validator(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    def Field(*args, **kwargs):
        return kwargs.get('default', None)


if PYDANTIC_AVAILABLE:
    class MicroInsightSchema(BaseModel):
        """Schema para validación de micro-insights (Capa 1)."""
        fragment_id: str
        insight: str = Field(..., min_length=1, description="Insight específico del chunk")
        reasoning: List[str] = Field(..., min_items=1, max_items=5, description="Pasos de Chain-of-Thought")
        confidence: float = Field(..., ge=0.0, le=1.0, description="Nivel de confianza 0-1")
        data_points: List[str] = Field(default_factory=list, description="Referencias a datos específicos")
        
        @validator('reasoning')
        def reasoning_must_not_be_empty(cls, v):
            if not v or len(v) == 0:
                raise ValueError('reasoning cannot be empty')
            return v
    
    class PatternItemSchema(BaseModel):
        """Schema para un patrón individual (Capa 2)."""
        description: str = Field(..., min_length=1, description="Descripción del patrón")
        category: str = Field(..., description="Categoría: trend, anomaly, opportunity, risk")
        significance: float = Field(..., ge=0.0, le=1.0, description="Significancia 0-1")
        supporting_insights: List[str] = Field(default_factory=list, description="IDs de insights que respaldan")
        reasoning: List[str] = Field(default_factory=list, description="Razonamiento paso a paso")
        
        @validator('category')
        def category_must_be_valid(cls, v):
            valid_categories = ['trend', 'anomaly', 'opportunity', 'risk']
            if v.lower() not in valid_categories:
                raise ValueError(f'category must be one of {valid_categories}')
            return v.lower()
    
    class Layer2ResponseSchema(BaseModel):
        """Schema para respuesta completa de Capa 2."""
        patterns: List[PatternItemSchema] = Field(default_factory=list, description="Lista de patrones identificados")
        
        @validator('patterns')
        def patterns_max_limit(cls, v):
            if len(v) > 5:
                logger.warning(f"Too many patterns ({len(v)}), limiting to 5")
                return v[:5]
            return v
    
    class Layer3ResponseSchema(BaseModel):
        """Schema para respuesta de Capa 3."""
        conclusion: str = Field(..., min_length=1, description="Conclusión final")
        reasoning: List[str] = Field(..., min_items=1, max_items=5, description="Razonamiento final")
        
        @validator('conclusion')
        def conclusion_must_be_reasonable(cls, v):
            if len(v) > 500:
                logger.warning(f"Conclusion too long ({len(v)} chars), may need truncation")
            return v


@dataclass
class MicroInsight:
    """Resultado de la Capa 1: análisis individual de un fragmento de datos."""
    fragment_id: str
    insight: str
    reasoning: List[str]  # Pasos de Chain-of-Thought
    confidence: float  # 0.0 a 1.0
    data_points: List[str]  # Referencias a datos específicos


@dataclass
class GlobalPattern:
    """Resultado de la Capa 2: patrón identificado al agrupar micro-insights."""
    pattern_id: str
    description: str
    supporting_insights: List[str]  # IDs de micro-insights que respaldan
    significance: float  # 0.0 a 1.0
    category: str  # 'trend', 'anomaly', 'opportunity', 'risk'
    reasoning: List[str]  # CoT explícito para identificación del patrón


@dataclass
class LayerMetrics:
    """Métricas de ejecución por capa."""
    duration_ms: float
    tokens_estimated: int
    success: bool
    cache_hit: bool = False
    error: Optional[str] = None


@dataclass
class CoTHSSumResult:
    """Resultado completo del pipeline CoTHSSum."""
    layer1_micro_insights: List[Dict[str, Any]]
    layer2_global_patterns: List[Dict[str, Any]]
    layer3_conclusion: str
    layer3_reasoning: List[str]
    metadata: Dict[str, Any]
    trace_id: str
    # Métricas granulares por capa
    layer1_metrics: LayerMetrics
    layer2_metrics: LayerMetrics
    layer3_metrics: LayerMetrics


class CoTHSSumPipeline:
    """
    Pipeline jerárquico de 3 capas para razonamiento estructurado.
    
    Flujo:
    1. Fragmentar datos en chunks pequeños
    2. Capa 1: Analizar cada chunk con Chain-of-Thought (micro-insights)
    3. Capa 2: Agrupar insights para identificar patrones globales
    4. Capa 3: Generar conclusión final basada en patrones
    """
    
    def __init__(self, agent, max_chunk_size: int = 5):
        """
        Inicializar el pipeline.
        
        Args:
            agent: Instancia de AnalyticsAgent para llamadas a Ollama
            max_chunk_size: Máximo de elementos por chunk (fragmento)
        """
        self.agent = agent
        self.max_chunk_size = max_chunk_size
        self._insight_cache = {}  # Cache simple: {chunk_hash: MicroInsight}
        self._cache_max_size = 100
    
    def _generate_chunk_hash(self, chunk: Dict[str, Any], question: str) -> str:
        """Generar hash único para un chunk y pregunta."""
        chunk_str = json.dumps(chunk, sort_keys=True)
        combined = f"{question}:{chunk_str}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def _get_cached_insight(self, chunk_hash: str) -> Optional[MicroInsight]:
        """Obtener insight desde cache si existe."""
        return self._insight_cache.get(chunk_hash)
    
    def _cache_insight(self, chunk_hash: str, insight: MicroInsight):
        """Guardar insight en cache con LRU eviction."""
        if len(self._insight_cache) >= self._cache_max_size:
            # Remover el primer elemento (LRU simple)
            self._insight_cache.pop(next(iter(self._insight_cache)))
        self._insight_cache[chunk_hash] = insight
        
    def execute(
        self,
        question: str,
        context: Dict[str, Any],
        trace_id: Optional[str] = None
    ) -> CoTHSSumResult:
        """
        Ejecutar el pipeline completo de CoTHSSum.
        
        Args:
            question: Pregunta del usuario
            context: Contexto de datos (stats, opportunities, etc.)
            trace_id: ID opcional para trazabilidad
            
        Returns:
            CoTHSSumResult con resultados de las 3 capas y métricas
        """
        import uuid
        trace_id = trace_id or str(uuid.uuid4())
        
        logger.info(f"[CoTHSSum {trace_id}] Iniciando pipeline para: {question[:50]}...")
        
        # Capa 1: Fragmentar y generar micro-insights
        start_time = time.time()
        micro_insights = self._layer1_micro_insights(question, context, trace_id)
        layer1_duration = (time.time() - start_time) * 1000
        layer1_tokens = self._estimate_tokens([asdict(i) for i in micro_insights])
        layer1_metrics = LayerMetrics(
            duration_ms=layer1_duration,
            tokens_estimated=layer1_tokens,
            success=len(micro_insights) > 0
        )
        
        # Capa 2: Identificar patrones globales
        start_time = time.time()
        global_patterns = self._layer2_global_patterns(question, micro_insights, trace_id)
        layer2_duration = (time.time() - start_time) * 1000
        layer2_tokens = self._estimate_tokens([asdict(p) for p in global_patterns])
        layer2_metrics = LayerMetrics(
            duration_ms=layer2_duration,
            tokens_estimated=layer2_tokens,
            success=len(global_patterns) > 0
        )
        
        # Capa 3: Generar conclusión final
        start_time = time.time()
        conclusion, reasoning = self._layer3_conclusion(
            question, micro_insights, global_patterns, trace_id
        )
        layer3_duration = (time.time() - start_time) * 1000
        layer3_tokens = self._estimate_tokens({'conclusion': conclusion, 'reasoning': reasoning})
        layer3_metrics = LayerMetrics(
            duration_ms=layer3_duration,
            tokens_estimated=layer3_tokens,
            success=bool(conclusion)
        )
        
        result = CoTHSSumResult(
            layer1_micro_insights=[asdict(i) for i in micro_insights],
            layer2_global_patterns=[asdict(p) for p in global_patterns],
            layer3_conclusion=conclusion,
            layer3_reasoning=reasoning,
            metadata={
                'total_micro_insights': len(micro_insights),
                'total_patterns': len(global_patterns),
                'model': self.agent.model,
                'max_chunk_size': self.max_chunk_size,
                'total_duration_ms': layer1_duration + layer2_duration + layer3_duration,
                'total_tokens': layer1_tokens + layer2_tokens + layer3_tokens
            },
            trace_id=trace_id,
            layer1_metrics=layer1_metrics,
            layer2_metrics=layer2_metrics,
            layer3_metrics=layer3_metrics
        )
        
        logger.info(f"[CoTHSSum {trace_id}] Pipeline completado: {len(micro_insights)} insights, {len(global_patterns)} patrones, {result.metadata['total_duration_ms']:.0f}ms")
        
        return result
    
    def _layer1_micro_insights(
        self,
        question: str,
        context: Dict[str, Any],
        trace_id: str
    ) -> List[MicroInsight]:
        """
        Capa 1: Generar micro-insights por fragmento de datos.
        
        Divide el contexto en chunks pequeños y analiza cada uno
        con Chain-of-Thought para obtener insights granulares.
        Usa caching para reutilizar insights en preguntas similares.
        """
        from ai.prompts import build_layer1_micro_insight_prompt
        
        # Fragmentar el contexto
        chunks = self._fragment_context(context)
        
        micro_insights = []
        
        for idx, chunk in enumerate(chunks):
            logger.debug(f"[CoTHSSum {trace_id}] Capa 1 - Analizando chunk {idx+1}/{len(chunks)}")
            
            # Generar hash del chunk para caching
            chunk_hash = self._generate_chunk_hash(chunk, question)
            
            # Intentar obtener desde cache
            cached_insight = self._get_cached_insight(chunk_hash)
            if cached_insight:
                logger.debug(f"[CoTHSSum {trace_id}] Cache hit para chunk {idx}")
                micro_insights.append(cached_insight)
                continue
            
            # Construir prompt para este chunk
            prompt = build_layer1_micro_insight_prompt(question, chunk, idx, len(chunks))
            
            # Llamar al modelo
            try:
                response = self._call_model_with_json_output(prompt)
                
                # Parsear respuesta JSON
                insight_data = self._parse_json_response(response)
                
                # Validar con Pydantic si está disponible
                if PYDANTIC_AVAILABLE:
                    validated = self._validate_json_schema(insight_data, MicroInsightSchema, "Capa 1")
                    if validated:
                        insight_data = validated
                
                if insight_data:
                    insight = MicroInsight(
                        fragment_id=chunk.get('semantic_group', f"chunk_{idx}"),
                        insight=insight_data.get('insight', ''),
                        reasoning=insight_data.get('reasoning', []),
                        confidence=insight_data.get('confidence', 0.5),
                        data_points=insight_data.get('data_points', [])
                    )
                    micro_insights.append(insight)
                    
                    # Guardar en cache
                    self._cache_insight(chunk_hash, insight)
                    
            except Exception as e:
                logger.warning(f"[CoTHSSum {trace_id}] Error en chunk {idx}: {e}")
                # Continuar con siguiente chunk
        
        return micro_insights
    
    def _layer2_global_patterns(
        self,
        question: str,
        micro_insights: List[MicroInsight],
        trace_id: str
    ) -> List[GlobalPattern]:
        """
        Capa 2: Identificar patrones globales agrupando micro-insights.
        
        Analiza los insights individuales para encontrar tendencias,
        anomalías, oportunidades o riesgos a nivel global con CoT explícito.
        """
        from ai.prompts import build_layer2_pattern_prompt
        
        logger.debug(f"[CoTHSSum {trace_id}] Capa 2 - Identificando patrones globales")
        
        # Agrupar insights por categoría o similitud
        insights_summary = self._summarize_insights(micro_insights)
        
        # Construir prompt para identificar patrones
        prompt = build_layer2_pattern_prompt(question, insights_summary)
        
        try:
            response = self._call_model_with_json_output(prompt)
            patterns_data = self._parse_json_response(response)
            
            # Validar con Pydantic si está disponible
            if PYDANTIC_AVAILABLE:
                validated = self._validate_json_schema(patterns_data, Layer2ResponseSchema, "Capa 2")
                if validated:
                    patterns_data = validated
            
            global_patterns = []
            if patterns_data and 'patterns' in patterns_data:
                for idx, pattern_data in enumerate(patterns_data['patterns']):
                    pattern = GlobalPattern(
                        pattern_id=f"pattern_{idx}",
                        description=pattern_data.get('description', ''),
                        supporting_insights=pattern_data.get('supporting_insights', []),
                        significance=pattern_data.get('significance', 0.5),
                        category=pattern_data.get('category', 'trend'),
                        reasoning=pattern_data.get('reasoning', [])  # CoT explícito
                    )
                    global_patterns.append(pattern)
            
            return global_patterns
            
        except Exception as e:
            logger.warning(f"[CoTHSSum {trace_id}] Error en Capa 2: {e}")
            return []
    
    def _layer3_conclusion(
        self,
        question: str,
        micro_insights: List[MicroInsight],
        global_patterns: List[GlobalPattern],
        trace_id: str
    ) -> tuple[str, List[str]]:
        """
        Capa 3: Generar conclusión final basada en patrones.
        
        Sintetiza los patrones globales para producir una respuesta
        coherente y accionable para el usuario.
        """
        from ai.prompts import build_layer3_conclusion_prompt
        
        logger.debug(f"[CoTHSSum {trace_id}] Capa 3 - Generando conclusión final")
        
        # Resumir patrones para el prompt
        patterns_summary = self._summarize_patterns(global_patterns)
        
        # Construir prompt para conclusión
        prompt = build_layer3_conclusion_prompt(question, patterns_summary)
        
        try:
            response = self._call_model_with_json_output(prompt)
            conclusion_data = self._parse_json_response(response)
            
            # Validar con Pydantic si está disponible
            if PYDANTIC_AVAILABLE:
                validated = self._validate_json_schema(conclusion_data, Layer3ResponseSchema, "Capa 3")
                if validated:
                    conclusion_data = validated
            
            conclusion = conclusion_data.get('conclusion', 'No se pudo generar conclusión.')
            reasoning = conclusion_data.get('reasoning', [])
            
            return conclusion, reasoning
            
        except Exception as e:
            logger.warning(f"[CoTHSSum {trace_id}] Error en Capa 3: {e}")
            # Fallback: generar conclusión simple
            return self._generate_fallback_conclusion(global_patterns), []
    
    def _estimate_tokens(self, data: Any) -> int:
        """
        Estimar tokens consumidos basado en longitud de texto.
        Estimación aproximada: 1 token ≈ 4 caracteres para inglés/español.
        """
        if isinstance(data, str):
            return len(data) // 4
        elif isinstance(data, list):
            return sum(self._estimate_tokens(item) for item in data)
        elif isinstance(data, dict):
            return sum(self._estimate_tokens(str(v)) for v in data.values())
        else:
            return len(str(data)) // 4
    
    def _validate_json_schema(self, data: Dict[str, Any], schema_class, layer_name: str) -> Dict[str, Any]:
        """
        Validar datos JSON contra esquema Pydantic.
        
        Args:
            data: Datos a validar
            schema_class: Clase de esquema Pydantic
            layer_name: Nombre de la capa para logging
            
        Returns:
            Datos validados o None si falla validación
        """
        if not PYDANTIC_AVAILABLE:
            logger.debug(f"[CoTHSSum] Pydantic no disponible, saltando validación para {layer_name}")
            return data
        
        try:
            validated = schema_class(**data)
            return validated.dict()
        except Exception as e:
            logger.warning(f"[CoTHSSum] Validación falló en {layer_name}: {e}")
            return None
    
    def _fragment_context(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fragmentar el contexto en chunks pequeños para análisis individual.
        
        Estrategia mejorada: segmentación semántica que agrupa elementos relacionados
        (por comuna, rango de precio, etc.) en lugar de solo por tamaño fijo.
        """
        chunks = []
        
        # Fragmentar opportunities con segmentación semántica
        opportunities = context.get('opportunities', [])
        if opportunities:
            # Agrupar por comuna para mejor coherencia temática
            chunks.extend(self._fragment_opportunities_semantic(opportunities))
        
        # Fragmentar communes con segmentación semántica
        communes = context.get('communes', [])
        if communes:
            # Agrupar por rango de precio/m²
            chunks.extend(self._fragment_communes_semantic(communes))
        
        # Agregar stats como chunk único (generalmente pequeño)
        stats = context.get('stats', {})
        if stats:
            chunks.append({
                'type': 'stats',
                'index': 0,
                'total_chunks': 1,
                'data': stats
            })
        
        # Si no hay datos fragmentables, usar contexto completo
        if not chunks:
            chunks.append({
                'type': 'general',
                'index': 0,
                'total_chunks': 1,
                'data': context
            })
        
        return chunks
    
    def _fragment_opportunities_semantic(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Fragmentar opportunities usando segmentación semántica por comuna.
        """
        from collections import defaultdict
        
        # Agrupar por comuna
        by_comuna = defaultdict(list)
        for opp in opportunities:
            prop = opp.get('property', opp)
            comuna = prop.get('comuna', 'Desconocida') if isinstance(prop, dict) else 'Desconocida'
            by_comuna[comuna].append(opp)
        
        chunks = []
        chunk_index = 0
        
        # Para cada comuna, crear chunks si excede max_chunk_size
        for comuna, opps in by_comuna.items():
            for i in range(0, len(opps), self.max_chunk_size):
                chunk = {
                    'type': 'opportunities',
                    'index': chunk_index,
                    'total_chunks': (len(opps) + self.max_chunk_size - 1) // self.max_chunk_size,
                    'data': opps[i:i + self.max_chunk_size],
                    'semantic_group': comuna  # Metadata de agrupación semántica
                }
                chunks.append(chunk)
                chunk_index += 1
        
        return chunks
    
    def _fragment_communes_semantic(self, communes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Fragmentar communes usando segmentación semántica por rango de precio/m².
        """
        # Ordenar por precio/m²
        sorted_communes = sorted(communes, key=lambda c: c.get('avg_price_m2', 0))
        
        chunks = []
        chunk_index = 0
        
        # Agrupar en rangos de precio
        for i in range(0, len(sorted_communes), self.max_chunk_size):
            chunk_communes = sorted_communes[i:i + self.max_chunk_size]
            if chunk_communes:
                price_range = f"${chunk_communes[0].get('avg_price_m2', 0):,}-${chunk_communes[-1].get('avg_price_m2', 0):,}"
                chunk = {
                    'type': 'communes',
                    'index': chunk_index,
                    'total_chunks': (len(sorted_communes) + self.max_chunk_size - 1) // self.max_chunk_size,
                    'data': chunk_communes,
                    'semantic_group': f"precio_m2_{price_range}"  # Metadata de agrupación semántica
                }
                chunks.append(chunk)
                chunk_index += 1
        
        return chunks
    
    def _summarize_insights(self, insights: List[MicroInsight]) -> str:
        """Convertir micro-insights a resumen textual para Capa 2."""
        summary_parts = []
        for insight in insights:
            part = f"- [{insight.fragment_id}] {insight.insight} (confianza: {insight.confidence:.2f})"
            summary_parts.append(part)
        return "\n".join(summary_parts)
    
    def _summarize_patterns(self, patterns: List[GlobalPattern]) -> str:
        """Convertir patrones globales a resumen textual para Capa 3."""
        summary_parts = []
        for pattern in patterns:
            part = f"- [{pattern.category.upper()}] {pattern.description} (significancia: {pattern.significance:.2f})"
            summary_parts.append(part)
        return "\n".join(summary_parts) if summary_parts else "No se identificaron patrones claros."
    
    def _call_model_with_json_output(self, prompt: str) -> str:
        """
        Llamar al modelo forzando salida JSON estructurada.
        
        Usa el endpoint /api/chat con instrucciones explícitas de formato JSON.
        """
        try:
            response = self.agent.ask(
                question=prompt,
                context={}  # Contexto ya incluido en el prompt
            )
            return response
        except Exception as e:
            logger.error(f"Error llamando al modelo: {e}")
            raise
    
    def _parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Extraer JSON de la respuesta del modelo.
        
        Maneja casos donde el modelo envuelve JSON en markdown code blocks
        o incluye texto adicional.
        """
        # Intentar extraer JSON de code blocks
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            response = json_match.group(1)
        
        # Intentar extraer JSON sin markdown
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            response = json_match.group(0)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.warning(f"No se pudo parsear JSON: {e}")
            logger.debug(f"Respuesta original: {response[:200]}...")
            return None
    
    def _generate_fallback_conclusion(self, patterns: List[GlobalPattern]) -> str:
        """Generar conclusión simple cuando falla el pipeline."""
        if not patterns:
            return "No hay suficientes datos para responder esta pregunta con confianza."
        
        # Usar el patrón más significativo
        top_pattern = max(patterns, key=lambda p: p.significance)
        return top_pattern.description


def format_cothssum_trace(result: CoTHSSumResult) -> str:
    """
    Formatear el trace completo de CoTHSSum para visualización.
    
    Útil para debugging y para mostrar el proceso de razonamiento
    al usuario (modo transparente).
    """
    lines = [
        f"🔍 CoTHSSum Trace ID: {result.trace_id}",
        f"📊 Capa 1 - Micro-insights: {result.metadata['total_micro_insights']}",
        f"🎯 Capa 2 - Patrones globales: {result.metadata['total_patterns']}",
        f"⏱️ Tiempo total: {result.metadata.get('total_duration_ms', 0):.0f}ms",
        f"🔢 Tokens totales: {result.metadata.get('total_tokens', 0)}",
        "",
        "--- Capa 1: Micro-insights ---",
        f"⏱️ Duración: {result.layer1_metrics.duration_ms:.0f}ms",
        f"🔢 Tokens: {result.layer1_metrics.tokens_estimated}",
        f"✅ Éxito: {result.layer1_metrics.success}",
        f"💾 Cache hits: {sum(1 for m in result.layer1_micro_insights if m.get('cached'))}"
    ]
    
    for insight in result.layer1_micro_insights:
        lines.append(f"\n📌 Fragmento: {insight['fragment_id']}")
        lines.append(f"💡 Insight: {insight['insight']}")
        lines.append(f"🔗 Razonamiento: {' → '.join(insight['reasoning'])}")
        lines.append(f"✅ Confianza: {insight['confidence']:.2f}")
        if insight.get('cached'):
            lines.append(f"💾 (Desde cache)")
    
    lines.extend([
        "",
        "--- Capa 2: Patrones Globales ---",
        f"⏱️ Duración: {result.layer2_metrics.duration_ms:.0f}ms",
        f"🔢 Tokens: {result.layer2_metrics.tokens_estimated}",
        f"✅ Éxito: {result.layer2_metrics.success}"
    ])
    
    for pattern in result.layer2_global_patterns:
        lines.append(f"\n🎯 Patrón: {pattern['pattern_id']}")
        lines.append(f"📝 Descripción: {pattern['description']}")
        lines.append(f"🏷️ Categoría: {pattern['category']}")
        lines.append(f"⭐ Significancia: {pattern['significance']:.2f}")
        if pattern.get('reasoning'):
            lines.append(f"🔗 Razonamiento: {' → '.join(pattern['reasoning'])}")
    
    lines.extend([
        "",
        "--- Capa 3: Conclusión ---",
        f"⏱️ Duración: {result.layer3_metrics.duration_ms:.0f}ms",
        f"🔢 Tokens: {result.layer3_metrics.tokens_estimated}",
        f"✅ Éxito: {result.layer3_metrics.success}",
        f"\n📌 {result.layer3_conclusion}",
        f"\n🔗 Razonamiento final: {' → '.join(result.layer3_reasoning)}"
    ])
    
    return "\n".join(lines)
