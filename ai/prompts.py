"""
Prompts compartidos entre el AnalyticsAgent en producción (ai/agent.py) y el
harness de tuning (scripts/test_ollama_params.py).

Regla: ESTA es la fuente única de verdad del system prompt. Cualquier cambio
aquí se refleja automáticamente tanto en el dashboard como en los benchmarks,
evitando que los resultados del tuning se calculen sobre un prompt distinto al
que corre en producción.
"""

from __future__ import annotations

from typing import Any, Dict, List


def format_analytics_context(context: Dict[str, Any]) -> str:
    """Serializa el contexto analítico (stats, market, opportunities, communes)
    en un bloque de texto compacto y estable para inyectar en el system prompt.
    """
    lines: List[str] = []

    stats = context.get("stats") or {}
    if stats:
        lines.append(f"Total de propiedades: {stats.get('total', 0)}")
        if stats.get("by_operacion"):
            lines.append(f"Por operación: {stats['by_operacion']}")
        if stats.get("by_tipo"):
            lines.append(f"Por tipo: {stats['by_tipo']}")
        if stats.get("precio_promedio"):
            lines.append(f"Precio promedio: ${stats['precio_promedio']:,}")

    ms = context.get("market_stats") or {}
    if ms.get("avg_price_m2"):
        lines.append(f"\nPrecio promedio por m²: ${ms['avg_price_m2']:,}")
    if ms.get("total_value"):
        lines.append(f"Valor total del mercado: ${ms['total_value']:,}")

    opps = context.get("opportunities") or []
    if isinstance(opps, list) and opps:
        lines.append(f"\nTop oportunidades ({len(opps)}):")
        for i, opp in enumerate(opps[:5], 1):
            if not isinstance(opp, dict):
                continue
            prop = opp.get("property", opp)
            titulo = prop.get("titulo", "N/A") if isinstance(prop, dict) else "N/A"
            lines.append(
                f"{i}. {titulo} "
                f"(Score: {opp.get('score', 0)}, "
                f"Precio/m²: ${opp.get('price_m2', 0):,}, "
                f"Descuento: {opp.get('discount_percentage', 0)}%)"
            )

    communes = context.get("communes") or []
    if isinstance(communes, list) and communes:
        lines.append("\nEstadísticas por comuna:")
        for c in communes[:5]:
            if not isinstance(c, dict):
                continue
            lines.append(
                f"- {c.get('name', 'N/A')}: "
                f"${c.get('avg_price_m2', 0):,}/m² "
                f"({c.get('count', 0)} propiedades)"
            )

    # Soporte legacy
    legacy = context.get("stats_by_comuna") or []
    if legacy:
        lines.append("\nEstadísticas por comuna:")
        for s in legacy[:5]:
            lines.append(
                f"- {s.get('comuna', 'N/A')}: "
                f"Promedio ${s.get('avg_precio_m2', 0):,.0f}/m² "
                f"({s.get('total_propiedades', 0)} propiedades)"
            )

    return "\n".join(lines) if lines else "No hay datos disponibles"


def build_analytics_system_prompt(context: Dict[str, Any]) -> str:
    """System prompt del AnalyticsAgent.

    Objetivos (para SLMs 0.5B–3B):
      - Fuerza grounding estricto: nada fuera del contexto.
      - Fuerza formato corto (el chat del dashboard es mobile-first).
      - Anti-hallucination: cifras literales, sin paráfrasis.
      - Puerta de salida explícita ("No hay datos disponibles") cuando falta info.
    """
    ctx_block = format_analytics_context(context)
    return (
        "Eres un analista inmobiliario del mercado chileno.\n"
        "Responde SOLO con datos del CONTEXTO. No inventes ni generalices.\n\n"
        "PROHIBIDO:\n"
        "- Dar consejos generales o teoría del mercado.\n"
        "- Inventar cifras, comunas o propiedades no listadas.\n"
        "- Redondear, parafrasear o convertir números del contexto.\n\n"
        "FORMATO:\n"
        "- Máximo 4 líneas, en español.\n"
        "- Usa cifras concretas, copiadas LITERAL del contexto.\n"
        "- Usa listas markdown si hay varios elementos.\n\n"
        "Si la pregunta no puede responderse con el contexto, responde exactamente:\n"
        "'No hay datos disponibles'.\n\n"
        f"CONTEXTO:\n{ctx_block}"
    )


# ============================================================================
# CoTHSSum: Prompts para Pipeline Jerárquico de 3 Capas
# ============================================================================

def build_layer1_micro_insight_prompt(
    question: str,
    chunk: Dict[str, Any],
    chunk_index: int,
    total_chunks: int
) -> str:
    """
    Prompt para Capa 1: Generar micro-insights con Chain-of-Thought.

    Objetivo: Analizar un fragmento pequeño de datos y generar un insight
    específico con razonamiento paso a paso.
    """
    chunk_type = chunk.get('type', 'general')
    chunk_data = chunk.get('data', [])
    
    # Formatear datos según tipo
    if chunk_type == 'opportunities':
        data_text = "\n".join([
            f"- {i+1}. {p.get('titulo', 'N/A')} (Score: {p.get('score', 0)}, Precio/m²: ${p.get('price_m2', 0):,})"
            for i, p in enumerate(chunk_data)
        ])
    elif chunk_type == 'communes':
        data_text = "\n".join([
            f"- {c.get('name', 'N/A')}: ${c.get('avg_price_m2', 0):,}/m² ({c.get('count', 0)} props)"
            for c in chunk_data
        ])
    elif chunk_type == 'stats':
        data_text = f"Total: {chunk_data.get('total', 0)} props, Precio prom: ${chunk_data.get('precio_promedio', 0):,}"
    else:
        data_text = str(chunk_data)[:500]  # Fallback
    
    return (
        "Eres un analista de datos especializado en micro-insights inmobiliarios.\n"
        "Tu tarea es analizar UN FRAGMENTO de datos y generar un insight específico.\n\n"
        f"PREGUNTA DEL USUARIO: {question}\n\n"
        f"FRAGMENTO {chunk_index + 1} de {total_chunks} (tipo: {chunk_type}):\n{data_text}\n\n"
        "INSTRUCCIONES:\n"
        "1. Identifica el insight más relevante de este fragmento para la pregunta.\n"
        "2. Usa Chain-of-Thought: razona paso a paso (máximo 3 pasos).\n"
        "3. Asigna un nivel de confianza (0.0 a 1.0) basado en la claridad de los datos.\n"
        "4. Lista los puntos de datos específicos que respaldan tu insight.\n\n"
        "RESPUESTA EN FORMATO JSON (solo el JSON, sin texto adicional):\n"
        "{\n"
        '  "insight": "tu insight específico",\n'
        '  "reasoning": ["paso 1", "paso 2", "paso 3"],\n'
        '  "confidence": 0.8,\n'
        '  "data_points": ["dato 1", "dato 2"]\n'
        "}\n\n"
        "REGLAS:\n"
        "- Insight debe ser específico a este fragmento, no general.\n"
        "- Confidence debe ser realista (0.0 si datos insuficientes).\n"
        "- Reasoning debe mostrar lógica clara y simple."
    )


def build_layer2_pattern_prompt(question: str, insights_summary: str) -> str:
    """
    Prompt para Capa 2: Identificar patrones globales.

    Objetivo: Agrupar micro-insights para identificar tendencias,
    anomalías, oportunidades o riesgos a nivel global con CoT explícito.
    """
    return (
        "Eres un analista de patrones especializado en síntesis de insights.\n"
        "Tu tarea es analizar múltiples micro-insights y encontrar patrones globales.\n\n"
        f"PREGUNTA DEL USUARIO: {question}\n\n"
        f"MICRO-INSIGHTS DISPONIBLES:\n{insights_summary}\n\n"
        "INSTRUCCIONES:\n"
        "1. Agrupa insights similares para identificar patrones.\n"
        "2. Clasifica cada patrón en: trend, anomaly, opportunity, o risk.\n"
        "3. Asigna significancia (0.0 a 1.0) basada en cantidad y calidad de insights.\n"
        "4. Lista qué insights respaldan cada patrón (por fragment_id).\n"
        "5. Usa Chain-of-Thought: razona paso a paso cómo identificaste cada patrón.\n\n"
        "RESPUESTA EN FORMATO JSON (solo el JSON, sin texto adicional):\n"
        "{\n"
        '  "patterns": [\n'
        '    {\n'
        '      "description": "descripción del patrón",\n'
        '      "category": "trend|anomaly|opportunity|risk",\n'
        '      "significance": 0.9,\n'
        '      "supporting_insights": ["chunk_0", "chunk_2"],\n'
        '      "reasoning": ["paso 1: agrupar insights similares", "paso 2: identificar tendencia", "paso 3: validar con datos"]\n'
        '    }\n'
        '  ]\n'
        "}\n\n"
        "REGLAS:\n"
        "- Máximo 5 patrones (solo los más significativos).\n"
        "- Significancia debe reflejar relevancia para la pregunta del usuario.\n"
        "- Category debe ser precisa según la naturaleza del patrón.\n"
        "- Reasoning debe mostrar lógica clara de identificación del patrón (máximo 3 pasos)."
    )


def build_layer3_conclusion_prompt(question: str, patterns_summary: str) -> str:
    """
    Prompt para Capa 3: Generar conclusión final.

    Objetivo: Sintetizar patrones globales para producir una respuesta
    coherente y accionable para el usuario.
    """
    return (
        "Eres un analista inmobiliario experto en comunicación clara.\n"
        "Tu tarea es sintetizar patrones globales en una respuesta directa y útil.\n\n"
        f"PREGUNTA DEL USUARIO: {question}\n\n"
        f"PATRONES GLOBALES IDENTIFICADOS:\n{patterns_summary}\n\n"
        "INSTRUCCIONES:\n"
        "1. Genera una conclusión directa que responda la pregunta.\n"
        "2. Usa los patrones más significativos como base.\n"
        "3. Sé conciso: máximo 3-4 líneas en español.\n"
        "4. Incluye cifras concretas si están disponibles en los patrones.\n"
        "5. Razona paso a paso cómo llegas a la conclusión.\n\n"
        "RESPUESTA EN FORMATO JSON (solo el JSON, sin texto adicional):\n"
        "{\n"
        '  "conclusion": "tu respuesta final al usuario",\n'
        '  "reasoning": ["paso 1", "paso 2", "paso 3"]\n'
        "}\n\n"
        "REGLAS:\n"
        "- Conclusion debe responder directamente la pregunta.\n"
        "- Si no hay patrones relevantes, indica que no hay datos suficientes.\n"
        "- Reasoning debe ser simple y lógico."
    )
