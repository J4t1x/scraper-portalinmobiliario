#!/usr/bin/env python3
"""
Ollama SLM Parameter Tuning Harness
====================================

Objetivo: Optimizar la parametrización de Ollama para el módulo de analytics
del dashboard (AnalyticsAgent), priorizando **respuestas rápidas y coherentes**
para una experiencia fluida.

Qué hace este script:
  1. Detecta el estado de Ollama y los modelos instalados (usando SLMManager).
  2. Ejecuta una matriz (grid) de pruebas variando los parámetros clave de
     inferencia: temperature, top_p, top_k, num_predict, num_ctx, repeat_penalty.
  3. Mide para cada configuración:
        - TTFT (time-to-first-token) en modo streaming → sensación de fluidez
        - Latencia total (wall clock)
        - Tokens generados y tokens/seg (eval_count / eval_duration)
        - Longitud de respuesta
        - Heurísticas de coherencia:
            * idioma ES (presencia de palabras frecuentes)
            * uso de datos del contexto (cifras presentes en el prompt)
            * ausencia de repeticiones degeneradas
            * markdown válido (listas, énfasis)
  4. Calcula un score ponderado (fluidez 50% + coherencia 30% + estabilidad 20%) y emite una
     recomendación concreta de parámetros para usar en `ai/agent.py`.
  5. Exporta resultados a JSON + reporte Markdown en `logs/ollama_tuning/`.

Uso:
    python scripts/test_ollama_params.py                # modo rápido (default)
    python scripts/test_ollama_params.py --full         # grid completo
    python scripts/test_ollama_params.py --model qwen2.5-coder:1.5b
    python scripts/test_ollama_params.py --models qwen2.5-coder:1.5b,phi3:mini
    python scripts/test_ollama_params.py --warmup 1 --repeats 3
    python scripts/test_ollama_params.py --no-stream    # desactiva streaming (sólo latencia total)

Buenas prácticas aplicadas:
    - Warmup previo por modelo (evita sesgo por cold-start / load_duration).
    - N repeticiones por configuración con mediana (robusto a outliers).
    - Prompts realistas construidos desde un contexto sintético representativo
      del dashboard (stats + oportunidades de inversión), en español.
    - Timeouts controlados y manejo de errores por prueba (una falla no
      aborta la suite).
    - Sin dependencias externas extra (sólo `requests`, stdlib).
    - Salida estable y reproducible (seed fijo cuando aplica).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from itertools import product
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests

# Permitir imports desde la raíz del proyecto
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

try:
    from ai.slm_manager import SLMManager, SLMCatalog  # type: ignore
    SLM_AVAILABLE = True
except Exception:  # pragma: no cover - fallback si no se puede importar
    SLM_AVAILABLE = False

# Fuente única de verdad para el system prompt: debe coincidir 1:1 con el que
# corre en producción (ai/agent.py → AnalyticsAgent._build_system_prompt).
from ai.prompts import build_analytics_system_prompt  # type: ignore

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:1.5b")

OUT_DIR = ROOT / "logs" / "ollama_tuning"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Carpeta de outputs reales del scraper (misma ruta host y contenedor vía bind mount).
SCRAPER_OUTPUT_DIR = Path(os.getenv("SCRAPER_OUTPUT_DIR", str(ROOT / "output")))

# UF aproximada (solo para homogeneizar precios cuando no hay precio_monto ya CLP).
UF_TO_CLP = float(os.getenv("UF_TO_CLP", "38500"))

# --------------------------------------------------------------------------- #
#  Contexto y prompts representativos del módulo analytics del dashboard      #
# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
#  Carga de datos reales desde output/*.json                                  #
# --------------------------------------------------------------------------- #

_M2_RE = re.compile(r"(\d+)\s*(?:-\s*(\d+))?\s*m²")
_UF_RE = re.compile(r"UF\s*([\d\.,]+)", re.IGNORECASE)
_CLP_RE = re.compile(r"\$\s*([\d\.,]+)")


def _price_to_clp(prop: Dict[str, Any]) -> Optional[float]:
    monto = prop.get("precio_monto")
    moneda = (prop.get("precio_moneda") or "").upper()
    if monto is not None:
        try:
            m = float(monto)
            return m * UF_TO_CLP if moneda == "UF" else m
        except (TypeError, ValueError):
            pass
    s = prop.get("precio") or ""
    mt = _UF_RE.search(s)
    if mt:
        try:
            return float(mt.group(1).replace(".", "").replace(",", ".")) * UF_TO_CLP
        except ValueError:
            return None
    mt = _CLP_RE.search(s)
    if mt:
        try:
            return float(mt.group(1).replace(".", "").replace(",", ""))
        except ValueError:
            return None
    return None


def _metros(prop: Dict[str, Any]) -> Optional[float]:
    mt = _M2_RE.search(prop.get("atributos") or "")
    if not mt:
        return None
    a = int(mt.group(1))
    b = int(mt.group(2)) if mt.group(2) else a
    return (a + b) / 2


def _commune(prop: Dict[str, Any]) -> Optional[str]:
    ubi = prop.get("ubicacion") or ""
    if not ubi:
        return None
    tail = ubi.split(",")[-1].strip()
    return tail or None


def load_real_context(output_dir: Path, max_files: int = 12) -> Optional[Dict[str, Any]]:
    """Agrega los outputs reales más recientes del scraper en un contexto estilo dashboard."""
    if not output_dir.exists():
        return None
    files = sorted(output_dir.glob("*.json"),
                   key=lambda p: p.stat().st_mtime, reverse=True)[:max_files]
    if not files:
        return None

    by_op: Dict[str, int] = {}
    by_tipo: Dict[str, int] = {}
    props: List[Dict[str, Any]] = []
    seen_ids: set = set()
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        meta = data.get("metadata", {}) or {}
        default_op = meta.get("operacion", "?")
        default_tp = meta.get("tipo", "?")
        for p in data.get("propiedades", []) or []:
            pid = p.get("id")
            if pid and pid in seen_ids:
                continue
            if pid:
                seen_ids.add(pid)
            p = dict(p)
            p.setdefault("operacion", default_op)
            p.setdefault("tipo", default_tp)
            props.append(p)

    if not props:
        return None

    prices_clp: List[float] = []
    price_m2_all: List[float] = []
    commune_agg: Dict[str, Dict[str, Any]] = {}

    for p in props:
        by_op[p["operacion"]] = by_op.get(p["operacion"], 0) + 1
        by_tipo[p["tipo"]] = by_tipo.get(p["tipo"], 0) + 1

        price = _price_to_clp(p)
        mts = _metros(p)
        comm = _commune(p)
        if price:
            prices_clp.append(price)
        if not comm:
            continue
        cs = commune_agg.setdefault(comm, {"count": 0, "prices": [], "pm2": []})
        cs["count"] += 1
        if price:
            cs["prices"].append(price)
        if price and mts and mts >= 10:
            pm2 = price / mts
            cs["pm2"].append(pm2)
            price_m2_all.append(pm2)

    communes = []
    for name, cs in commune_agg.items():
        if cs["count"] < 2:
            continue
        avg_m2 = int(statistics.mean(cs["pm2"])) if cs["pm2"] else 0
        communes.append({"name": name, "avg_price_m2": avg_m2, "count": cs["count"]})
    communes.sort(key=lambda c: c["count"], reverse=True)
    top_communes = communes[:6]

    total = len(props)
    precio_promedio = int(statistics.mean(prices_clp)) if prices_clp else 0
    avg_price_m2 = int(statistics.mean(price_m2_all)) if price_m2_all else 0

    opps: List[Dict[str, Any]] = []
    if avg_price_m2 > 0:
        for p in props:
            price = _price_to_clp(p); mts = _metros(p); comm = _commune(p)
            if not (price and mts and mts >= 10 and comm):
                continue
            pm2 = price / mts
            discount = round((1 - pm2 / avg_price_m2) * 100)
            if discount < 5:
                continue
            score = max(50, min(99, 60 + discount))
            opps.append({
                "property": {"titulo": (p.get("titulo") or "")[:70]},
                "commune": comm,
                "score": score,
                "price_m2": int(pm2),
                "discount_percentage": int(discount),
            })
    opps.sort(key=lambda o: o["discount_percentage"], reverse=True)
    top_opps = opps[:3]

    ctx = {
        "stats": {
            "total": total,
            "by_operacion": by_op,
            "by_tipo": by_tipo,
            "precio_promedio": precio_promedio,
        },
        "market_stats": {
            "avg_price_m2": avg_price_m2,
            "total_value": precio_promedio * total,
        },
        "opportunities": top_opps,
        "communes": top_communes,
        "_source_files": [f.name for f in files],
    }
    return ctx


@dataclass
class TestQuery:
    """Query de evaluación. Soporta multi-turno y flags especiales.

    - ``label``: etiqueta corta para agrupar en el reporte.
    - ``question``: último mensaje del usuario (lo que responde el modelo).
    - ``prior_turns``: historial previo (user/assistant) para probar memoria
      conversacional — caso real del AI Analytics Studio que es un chat.
    - ``expect_refusal``: si True, la respuesta correcta es
      "No hay datos disponibles" o similar (query fuera de contexto).
      El scoring invierte la expectativa: premia brevedad + rechazo explícito
      y castiga cualquier número inventado.
    """
    label: str
    question: str
    prior_turns: List[Tuple[str, str]] = field(default_factory=list)
    expect_refusal: bool = False


# Frases válidas para declarar ausencia de datos (alineadas con ai/prompts.py).
REFUSAL_MARKERS = (
    "no hay datos",
    "no tengo datos",
    "no dispongo",
    "no puedo responder",
    "fuera del contexto",
)


def build_test_queries(ctx: Dict[str, Any]) -> List[TestQuery]:
    """Construye queries representativas usando nombres reales del contexto.

    Incluye casos reales del AI Analytics Studio:
      - preguntas factuales (corto, numerico),
      - comparativas y rankings,
      - **out-of-context** (el modelo debe rehusarse),
      - **follow-up multi-turno** (el chat mantiene historial).
    """
    communes = ctx.get("communes", []) or []
    c0 = communes[0]["name"] if len(communes) > 0 else "Santiago"
    c1 = communes[1]["name"] if len(communes) > 1 else c0
    c2 = communes[2]["name"] if len(communes) > 2 else c1

    return [
        TestQuery("corto",       "¿Cuántas propiedades hay en total?"),
        TestQuery("numerico",    f"¿Cuál es el precio promedio por m² en {c0}?"),
        TestQuery("comparativo", f"Compara {c1} vs {c2}: ¿dónde conviene invertir y por qué?"),
        TestQuery("ranking",     "Dame las 3 mejores oportunidades de inversión con su score y descuento."),
        # Out-of-context: el modelo NO tiene estos datos. Debe rehusarse sin inventar.
        TestQuery(
            "fuera_contexto",
            "¿Cuál es el precio del dólar hoy en Chile?",
            expect_refusal=True,
        ),
        # Multi-turno: simula un chat del Analytics Studio donde el usuario
        # hace una pregunta inicial y luego profundiza.
        TestQuery(
            "followup",
            "¿Y cuál tiene mayor descuento?",
            prior_turns=[
                ("user", "Dame las 3 mejores oportunidades."),
                ("assistant", "Aquí están las top 3 según el score del contexto."),
            ],
        ),
    ]


def derive_grounding(ctx: Dict[str, Any]) -> Tuple[set, Tuple[str, ...]]:
    """Extrae números y lugares esperados del contexto para scoring dinámico."""
    numbers: set = set()
    s = ctx.get("stats", {})
    if s.get("total"):
        numbers.add(int(s["total"]))
    ms = ctx.get("market_stats", {})
    if ms.get("avg_price_m2"):
        numbers.add(int(ms["avg_price_m2"]))
    for c in ctx.get("communes", []) or []:
        if c.get("avg_price_m2"):
            numbers.add(int(c["avg_price_m2"]))
        if c.get("count"):
            numbers.add(int(c["count"]))
    for o in ctx.get("opportunities", []) or []:
        for k in ("score", "price_m2", "discount_percentage"):
            if o.get(k):
                numbers.add(int(o[k]))
    places = tuple({c["name"] for c in ctx.get("communes", []) if c.get("name")})
    return numbers, places


def build_system_prompt(ctx: Dict[str, Any]) -> str:
    """Delega en ``ai.prompts.build_analytics_system_prompt``.

    Garantiza que el harness mida exactamente el mismo prompt que el
    AnalyticsAgent usa en producción. Cualquier cambio al prompt debe hacerse
    en ``ai/prompts.py`` (fuente única de verdad).
    """
    return build_analytics_system_prompt(ctx)


# --------------------------------------------------------------------------- #
#  Matriz de parámetros                                                       #
# --------------------------------------------------------------------------- #

# Grid "quick": determinista, respuestas cortas (modelos chicos tipo 0.5b/1.5b).
# Trimmed a 2 configs para reducir tiempo total (≈50% menos runs vs 3 perfiles).
QUICK_GRID: List[Dict[str, Any]] = [
    # Perfil ultra-corto (óptimo para TTFT en CPU)
    {"temperature": 0.2, "top_p": 0.8, "top_k": 20, "num_predict": 80,
     "num_ctx": 1024, "repeat_penalty": 1.15},
    # Perfil balanceado (mejor coherencia en comparativos)
    {"temperature": 0.2, "top_p": 0.9, "top_k": 40, "num_predict": 120,
     "num_ctx": 2048, "repeat_penalty": 1.1},
]

# Grid "full": barrido acotado (solo ejes con impacto real según pruebas previas).
# 2×2×3 = 12 combos (vs 96 del grid original).
FULL_GRID_AXES: Dict[str, List[Any]] = {
    "temperature": [0.2],
    "top_p":       [0.8, 0.9],
    "top_k":       [20, 40],
    "num_predict": [80, 120, 160],
    "num_ctx":     [2048],
    "repeat_penalty": [1.15],
}


def expand_full_grid() -> List[Dict[str, Any]]:
    keys = list(FULL_GRID_AXES.keys())
    combos: List[Dict[str, Any]] = []
    for values in product(*FULL_GRID_AXES.values()):
        combos.append(dict(zip(keys, values)))
    return combos


# --------------------------------------------------------------------------- #
#  Heurísticas de coherencia                                                  #
# --------------------------------------------------------------------------- #

SPANISH_HINTS = {"el", "la", "los", "las", "de", "que", "en", "por", "para",
                 "con", "es", "un", "una", "más", "precio", "propiedad",
                 "oportunidad", "comuna", "inversión"}

def _spanish_ratio(text: str) -> float:
    tokens = re.findall(r"[a-záéíóúñ]+", text.lower())
    if not tokens:
        return 0.0
    hits = sum(1 for t in tokens if t in SPANISH_HINTS)
    return min(1.0, hits / max(1, len(tokens) / 8))  # ~12% tokens comunes = 1.0


def _context_grounding(text: str, ctx: Dict[str, Any]) -> float:
    """¿Cuántos hechos verificables del contexto aparecen en la respuesta?"""
    numbers, places = derive_grounding(ctx)
    low = text.lower()
    hits = sum(1 for p in places if p.lower() in low)
    for n in numbers:
        s = str(n)
        if s in text or f"{n:,}".replace(",", ".") in text:
            hits += 1
    return min(1.0, hits / 3.0)


def _repetition_penalty(text: str) -> float:
    """1.0 si no hay repeticiones degeneradas; baja si se detectan."""
    if not text.strip():
        return 0.0
    # Repetición de 4-gramas consecutivos
    words = text.split()
    if len(words) < 8:
        return 1.0
    grams = [" ".join(words[i:i+4]) for i in range(len(words) - 3)]
    dup_ratio = 1 - (len(set(grams)) / len(grams))
    return max(0.0, 1.0 - dup_ratio * 3)  # castiga fuerte duplicados


def _markdown_bonus(text: str) -> float:
    has_list = bool(re.search(r"(?m)^\s*[-*\d]+[.)]?\s+", text))
    has_bold = "**" in text or "__" in text
    return 1.0 if (has_list or has_bold) else 0.7


# Frases típicas de "modo blog/consejos" que queremos penalizar.
GENERIC_PATTERNS = [
    "es importante",
    "te recomiendo",
    "debes considerar",
    "al invertir",
    "en el mercado",
    "una buena opción",
]

COACH_PATTERNS = ["aprende", "investigar", "te ayudará", "es recomendable"]

def _generic_penalty(text: str) -> float:
    low = text.lower()
    hits = sum(1 for p in GENERIC_PATTERNS if p in low)
    return max(0.0, 1 - hits * 0.3)


def _coach_penalty(text: str) -> float:
    low = text.lower()
    hits = sum(1 for b in COACH_PATTERNS if b in low)
    return max(0.0, 1 - hits * 0.4)


def _usefulness(text: str, places: Tuple[str, ...]) -> float:
    has_numbers = any(c.isdigit() for c in text)
    has_context = any(w in text for w in places) if places else has_numbers
    return 1.0 if (has_numbers and has_context) else 0.3


def _length_penalty(chars: int) -> float:
    if chars < 300:
        return 1.0
    if chars > 1000:
        return 0.4
    return 1.0 - ((chars - 300) / 700) * 0.6


def _extract_numbers(text: str) -> List[int]:
    """Extrae enteros del texto, ignorando separadores de miles (`.` / `,`)."""
    cleaned = text.replace(",", "").replace(".", "")
    out: List[int] = []
    for n in re.findall(r"\d+", cleaned):
        try:
            out.append(int(n))
        except ValueError:
            continue
    return out


def _numeric_grounding(text: str, ctx: Dict[str, Any]) -> float:
    """Mide cuántos números concretos del contexto aparecen en la respuesta."""
    numbers, _ = derive_grounding(ctx)
    if not numbers:
        return 0.5
    hits = sum(1 for n in _extract_numbers(text) if n in numbers)
    return min(1.0, hits / 2.0)


# Números que el modelo puede legítimamente usar aunque no estén en el contexto
# (rankings "1/2/3", porcentajes bajos comunes, años, etc.).
_NUMERIC_WHITELIST = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 100}


def _numeric_hallucination_penalty(text: str, question: str,
                                   ctx: Dict[str, Any]) -> float:
    """Penaliza números en la respuesta que NO provienen del contexto ni de la
    pregunta. Es el tipo de error más costoso en el Analytics Studio porque
    parece una cifra fiable sin serlo.

    Retorna 1.0 si no hay alucinación, decreciendo 0.25 por cada cifra inventada
    hasta un piso de 0.0.
    """
    ctx_numbers, _ = derive_grounding(ctx)
    allowed: set = set(ctx_numbers) | _NUMERIC_WHITELIST | set(_extract_numbers(question))
    found = _extract_numbers(text)
    if not found:
        return 1.0
    hallucinated = [n for n in found if n not in allowed]
    if not hallucinated:
        return 1.0
    return max(0.0, 1.0 - 0.25 * len(hallucinated))


def _is_truncated(text: str) -> bool:
    t = text.strip()
    if not t:
        return True
    # Termina en marcador de formato abierto o palabra cortada típica
    if t.endswith(("**", "__", "-", "•", ":", ",")):
        return True
    last = t.split()[-1] if t.split() else ""
    if last.startswith("**") and not last.endswith("**"):
        return True
    # No termina en puntuación de cierre
    return not t.endswith((".", "!", "?", ")", "]", "%"))


def is_valid(text: str) -> bool:
    """Respuesta aceptable: corta y con al menos un número."""
    return len(text) < 800 and any(c.isdigit() for c in text)


def coherence_score(text: str, ctx: Dict[str, Any],
                    question: str = "") -> Dict[str, float]:
    _, places = derive_grounding(ctx)
    es = _spanish_ratio(text)
    grounding = _numeric_grounding(text, ctx)
    halluc = _numeric_hallucination_penalty(text, question, ctx)
    rep = _repetition_penalty(text)
    md = _markdown_bonus(text)
    gen = _generic_penalty(text)
    coach = _coach_penalty(text)
    useful = _usefulness(text, places)
    length = _length_penalty(len(text))
    trunc = 0.6 if _is_truncated(text) else 1.0

    base = (
        0.25 * es +
        0.35 * grounding +
        0.15 * rep +
        0.10 * md +
        0.15 * gen
    )
    # Mezcla con utilidad real y aplica penalizaciones multiplicativas
    overall = 0.5 * base + 0.5 * useful
    overall *= length
    overall *= coach
    overall *= trunc
    overall *= halluc  # castigo fuerte por cifras inventadas
    overall = max(0.0, min(1.0, overall))

    return {
        "es": es,
        "grounding": grounding,
        "hallucination": halluc,
        "non_repetition": rep,
        "markdown": md,
        "generic": gen,
        "coach": coach,
        "useful": useful,
        "length": length,
        "truncated": 0.0 if trunc < 1.0 else 1.0,
        "overall": round(overall, 3),
    }


# --------------------------------------------------------------------------- #
#  Ollama calls                                                               #
# --------------------------------------------------------------------------- #

@dataclass
class RunResult:
    ok: bool
    model: str
    params: Dict[str, Any]
    query_label: str
    question: str
    ttft_ms: Optional[int] = None           # tiempo al primer byte útil (incluye ingestión)
    ttft_generation_ms: Optional[int] = None  # ttft_ms - prompt_eval_ms (percepción pura)
    total_ms: int = 0
    eval_count: int = 0
    tokens_per_sec: float = 0.0
    load_ms: int = 0
    prompt_eval_ms: int = 0
    eval_ms: int = 0
    response_chars: int = 0
    response_preview: str = ""
    coherence: Dict[str, float] = field(default_factory=dict)
    expect_refusal: bool = False
    refused: Optional[bool] = None  # None si no aplica; True/False si expect_refusal
    error: Optional[str] = None


# Threads dinámicos según CPU disponible (mínimo 2).
_NUM_THREAD = max(2, (os.cpu_count() or 4) // 2)

# num_predict dinámico por tipo de query (si el grid no fuerza uno ad-hoc).
QUERY_NUM_PREDICT = {
    "corto": 60,
    "numerico": 120,   # subido de 80: el modelo necesita espacio para citar cifras exactas
    "ranking": 120,
    "comparativo": 140,
}


def _post_chat(ollama_url: str, model: str, system: str, user: str,
               params: Dict[str, Any], stream: bool, timeout: int,
               prior_turns: Optional[List[Tuple[str, str]]] = None) -> requests.Response:
    messages: List[Dict[str, str]] = [{"role": "system", "content": system}]
    for role, content in (prior_turns or []):
        messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user})
    return requests.post(
        f"{ollama_url}/api/chat",
        json={
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {**params, "seed": 42, "num_thread": _NUM_THREAD},
            "keep_alive": "30m",
        },
        stream=stream,
        timeout=timeout,
    )


def _is_refusal(text: str) -> bool:
    low = text.lower()
    return any(m in low for m in REFUSAL_MARKERS)


def run_single(
    ollama_url: str,
    model: str,
    system: str,
    query: TestQuery,
    params: Dict[str, Any],
    stream: bool,
    ctx: Dict[str, Any],
    timeout: int = 90,
    _retry: bool = False,
) -> RunResult:
    label, question = query.label, query.question
    # Ajuste dinámico de num_predict por tipo de query (sin mutar el dict original).
    params = dict(params)
    if label in QUERY_NUM_PREDICT:
        params["num_predict"] = min(params.get("num_predict", 120),
                                    QUERY_NUM_PREDICT[label])
    # Para refusals queremos respuestas aún más cortas.
    if query.expect_refusal:
        params["num_predict"] = min(params.get("num_predict", 120), 40)
    result = RunResult(ok=False, model=model, params=params,
                       query_label=label, question=question,
                       expect_refusal=query.expect_refusal)
    t0 = time.perf_counter()
    try:
        if stream:
            resp = _post_chat(ollama_url, model, system, question, params, True,
                              timeout, prior_turns=query.prior_turns)
            resp.raise_for_status()
            ttft_ms: Optional[int] = None
            chunks: List[str] = []
            last: Dict[str, Any] = {}
            for line in resp.iter_lines():
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                content = obj.get("message", {}).get("content", "")
                if content and ttft_ms is None:
                    ttft_ms = int((time.perf_counter() - t0) * 1000)
                if content:
                    chunks.append(content)
                if obj.get("done"):
                    last = obj
            total_ms = int((time.perf_counter() - t0) * 1000)
            text = "".join(chunks)
            eval_count = last.get("eval_count", 0)
            eval_duration_ns = last.get("eval_duration", 0)
            tps = (eval_count / (eval_duration_ns / 1e9)) if eval_duration_ns else 0.0
            result.ok = True
            result.ttft_ms = ttft_ms
            result.total_ms = total_ms
            result.eval_count = eval_count
            result.tokens_per_sec = round(tps, 2)
            result.load_ms = last.get("load_duration", 0) // 1_000_000
            result.prompt_eval_ms = last.get("prompt_eval_duration", 0) // 1_000_000
            result.eval_ms = eval_duration_ns // 1_000_000
            result.response_chars = len(text)
            result.response_preview = text[:220]
            # TTFT "puro" (percepción del usuario tras la ingestión del prompt).
            if ttft_ms is not None:
                result.ttft_generation_ms = max(0, ttft_ms - result.prompt_eval_ms)
            result.coherence = coherence_score(text, ctx, question)
            if query.expect_refusal:
                result.refused = _is_refusal(text)
        else:
            resp = _post_chat(ollama_url, model, system, question, params, False,
                              timeout, prior_turns=query.prior_turns)
            resp.raise_for_status()
            total_ms = int((time.perf_counter() - t0) * 1000)
            data = resp.json()
            text = data.get("message", {}).get("content", "")
            eval_count = data.get("eval_count", 0)
            eval_duration_ns = data.get("eval_duration", 0)
            tps = (eval_count / (eval_duration_ns / 1e9)) if eval_duration_ns else 0.0
            result.ok = True
            result.total_ms = total_ms
            result.eval_count = eval_count
            result.tokens_per_sec = round(tps, 2)
            result.load_ms = data.get("load_duration", 0) // 1_000_000
            result.prompt_eval_ms = data.get("prompt_eval_duration", 0) // 1_000_000
            result.eval_ms = eval_duration_ns // 1_000_000
            result.response_chars = len(text)
            result.response_preview = text[:220]
            result.coherence = coherence_score(text, ctx, question)
            if query.expect_refusal:
                result.refused = _is_refusal(text)
    except Exception as e:  # noqa: BLE001
        result.error = f"{type(e).__name__}: {e}"
        result.total_ms = int((time.perf_counter() - t0) * 1000)

    # Retry 1 vez con parámetros más estrictos si la respuesta no es válida.
    # En queries de refusal, una respuesta corta SIN números es lo correcto,
    # así que nunca disparamos retry para esos casos.
    if (not _retry and result.ok and not query.expect_refusal
            and not is_valid(result.response_preview)):
        retry_params = {**params, "temperature": 0.2, "num_predict": 80,
                        "top_p": 0.8, "top_k": 20}
        r2 = run_single(ollama_url, model, system, query, retry_params,
                        stream, ctx, timeout, _retry=True)
        if r2.ok and r2.coherence.get("overall", 0) >= result.coherence.get("overall", 0):
            return r2
    return result


def warmup(ollama_url: str, model: str, rounds: int = 1,
           system: Optional[str] = None) -> None:
    """Precarga el modelo y — si se provee ``system`` — calienta el KV cache
    con ese prefijo, de modo que el primer run real no pague la ingestión
    completa del system prompt.

    Sin ``system`` hace un warmup mínimo (compatibilidad hacia atrás).
    """
    for _ in range(max(0, rounds)):
        try:
            if system:
                # Mismo endpoint y mismo system que los tests → Ollama cachea
                # el prefijo y las primeras iteraciones no inflarán prompt_eval.
                requests.post(
                    f"{ollama_url}/api/chat",
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": "ok"},
                        ],
                        "stream": False,
                        "options": {"num_predict": 4, "num_thread": _NUM_THREAD},
                        "keep_alive": "30m",
                    },
                    timeout=180,
                )
            else:
                requests.post(
                    f"{ollama_url}/api/generate",
                    json={"model": model, "prompt": "ok", "stream": False,
                          "options": {"num_predict": 4}},
                    timeout=120,
                )
        except Exception:  # noqa: BLE001
            return


# --------------------------------------------------------------------------- #
#  Agregación y scoring                                                       #
# --------------------------------------------------------------------------- #

@dataclass
class ConfigSummary:
    model: str
    params: Dict[str, Any]
    samples: int
    ttft_p50_ms: Optional[float]           # TTFT total (incluye ingestión)
    ttft_gen_p50_ms: Optional[float]       # TTFT "puro" (ttft - prompt_eval)
    prompt_eval_p50_ms: Optional[float]    # ingestión del prompt (aislada)
    total_p50_ms: float
    total_p95_ms: float
    tokens_per_sec: float
    coherence: float
    hallucination: float                   # 1.0 = sin cifras inventadas
    refusal_accuracy: Optional[float]      # % de refusals correctos (None si no aplica)
    fluidity: float                        # 0..1
    stability: float                       # 0..1 (consistencia entre runs)
    score: float                           # 0..1 (fluidez 50% + coherencia 30% + estabilidad 20%)
    errors: int


def _p(values: List[float], q: float) -> float:
    if not values:
        return 0.0
    values_sorted = sorted(values)
    k = max(0, min(len(values_sorted) - 1, int(round(q * (len(values_sorted) - 1)))))
    return float(values_sorted[k])


def _stability(values: List[float]) -> float:
    """1.0 = runs consistentes; cae con alta variabilidad relativa."""
    if len(values) < 2:
        return 1.0
    mean = statistics.mean(values)
    if mean <= 0:
        return 1.0
    cv = statistics.stdev(values) / (mean + 1e-6)
    return max(0.0, min(1.0, 1 - cv))


def summarize(results: List[RunResult]) -> List[ConfigSummary]:
    buckets: Dict[Tuple[str, str], List[RunResult]] = {}
    for r in results:
        key = (r.model, json.dumps(r.params, sort_keys=True))
        buckets.setdefault(key, []).append(r)

    summaries: List[ConfigSummary] = []
    for (model, params_key), rs in buckets.items():
        oks = [r for r in rs if r.ok]
        errors = len(rs) - len(oks)
        if not oks:
            continue
        ttfts = [r.ttft_ms for r in oks if r.ttft_ms is not None]
        ttfts_gen = [r.ttft_generation_ms for r in oks if r.ttft_generation_ms is not None]
        prompt_evals = [r.prompt_eval_ms for r in oks if r.prompt_eval_ms > 0]
        totals = [r.total_ms for r in oks]
        tps = [r.tokens_per_sec for r in oks if r.tokens_per_sec > 0]
        coh = [r.coherence.get("overall", 0.0) for r in oks]
        halluc = [r.coherence.get("hallucination", 1.0) for r in oks]

        # Fluidez: ahora basada en TTFT de *generación* (ingestión se mide aparte).
        # Lo que el usuario percibe tras el spinner de "pensando..." es
        # ttft_generation_ms; prompt_eval se amortiza con keep_alive + KV cache.
        ttft_gen_med = statistics.median(ttfts_gen) if ttfts_gen else (
            statistics.median(ttfts) if ttfts else statistics.median(totals))
        total_med = statistics.median(totals)
        # Normalización: 150ms→1, 1500ms→0 (el "time-to-first-generated-token"
        # debería ser < 1s para sensación fluida en chat).
        ttft_norm = max(0.0, min(1.0, 1 - (ttft_gen_med - 150) / 1350))
        total_norm = max(0.0, min(1.0, 1 - (total_med - 1500) / 8500))
        fluidity = round(0.6 * ttft_norm + 0.4 * total_norm, 3)

        coherence_med = round(statistics.median(coh), 3) if coh else 0.0
        halluc_med = round(statistics.median(halluc), 3) if halluc else 1.0
        # Estabilidad: consistencia de la coherencia entre runs
        stability = round(_stability(coh), 3) if coh else 1.0
        score = round(0.5 * fluidity + 0.3 * coherence_med + 0.2 * stability, 3)

        # Refusal accuracy: solo sobre queries con expect_refusal=True.
        refusal_runs = [r for r in oks if r.expect_refusal]
        refusal_acc: Optional[float] = None
        if refusal_runs:
            hits = sum(1 for r in refusal_runs if r.refused)
            refusal_acc = round(hits / len(refusal_runs), 3)

        summaries.append(ConfigSummary(
            model=model,
            params=json.loads(params_key),
            samples=len(oks),
            ttft_p50_ms=round(statistics.median(ttfts), 1) if ttfts else None,
            ttft_gen_p50_ms=round(statistics.median(ttfts_gen), 1) if ttfts_gen else None,
            prompt_eval_p50_ms=round(statistics.median(prompt_evals), 1) if prompt_evals else None,
            total_p50_ms=round(total_med, 1),
            total_p95_ms=round(_p([float(x) for x in totals], 0.95), 1),
            tokens_per_sec=round(statistics.median(tps), 2) if tps else 0.0,
            coherence=coherence_med,
            hallucination=halluc_med,
            refusal_accuracy=refusal_acc,
            fluidity=fluidity,
            stability=stability,
            score=score,
            errors=errors,
        ))
    summaries.sort(key=lambda s: s.score, reverse=True)
    return summaries


# --------------------------------------------------------------------------- #
#  Reporte                                                                    #
# --------------------------------------------------------------------------- #

def write_reports(
    results: List[RunResult],
    summaries: List[ConfigSummary],
    meta: Dict[str, Any],
) -> Tuple[Path, Path]:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = OUT_DIR / f"ollama_tuning_{ts}.json"
    md_path = OUT_DIR / f"ollama_tuning_{ts}.md"

    payload = {
        "meta": meta,
        "summaries": [asdict(s) for s in summaries],
        "runs": [asdict(r) for r in results],
    }
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    # Markdown
    lines: List[str] = []
    lines.append(f"# Ollama SLM Tuning Report — {ts}\n")
    lines.append(f"- **Ollama URL:** `{meta['ollama_url']}`")
    lines.append(f"- **Modelos probados:** {', '.join(meta['models'])}")
    lines.append(f"- **Queries:** {len(meta['queries'])}  |  **Grid:** {meta['grid']}  "
                 f"|  **Repeats:** {meta['repeats']}  |  **Stream:** {meta['stream']}")
    lines.append(f"- **Total runs OK/TOTAL:** {meta['ok_runs']}/{meta['total_runs']}\n")

    lines.append("## 🏆 Top 10 configuraciones (score = 50% fluidez + 30% coherencia + 20% estabilidad)\n")
    lines.append("| # | Modelo | Params | TTFT-gen p50 | Ingest p50 | Total p50 | Tok/s | Coh. | Halluc. | Refusal | Fluidez | Estab. | **Score** |")
    lines.append("|---|--------|--------|-------------:|-----------:|----------:|------:|-----:|--------:|--------:|--------:|-------:|---------:|")
    for i, s in enumerate(summaries[:10], 1):
        p = s.params
        pretty = (f"T={p.get('temperature')} top_p={p.get('top_p')} "
                  f"top_k={p.get('top_k')} n_pred={p.get('num_predict')} "
                  f"ctx={p.get('num_ctx')} rp={p.get('repeat_penalty')}")
        ttft_gen = f"{s.ttft_gen_p50_ms:.0f}ms" if s.ttft_gen_p50_ms is not None else "—"
        ingest = f"{s.prompt_eval_p50_ms:.0f}ms" if s.prompt_eval_p50_ms is not None else "—"
        refusal = f"{s.refusal_accuracy:.0%}" if s.refusal_accuracy is not None else "—"
        lines.append(
            f"| {i} | `{s.model}` | {pretty} | {ttft_gen} | {ingest} | "
            f"{s.total_p50_ms:.0f}ms | {s.tokens_per_sec:.1f} | "
            f"{s.coherence:.2f} | {s.hallucination:.2f} | {refusal} | "
            f"{s.fluidity:.2f} | {s.stability:.2f} | **{s.score:.2f}** |"
        )

    if summaries:
        best = summaries[0]
        lines.append("\n## ✅ Recomendación\n")
        lines.append(f"**Modelo:** `{best.model}`\n")
        lines.append("**Parámetros recomendados (copiar a `ai/agent.py` → `options`):**\n")
        lines.append("```python")
        lines.append("options = {")
        for k, v in best.params.items():
            lines.append(f"    \"{k}\": {v!r},")
        lines.append(f"    \"num_thread\": {_NUM_THREAD},")
        lines.append("}")
        lines.append("```")
        refusal_str = (f"{best.refusal_accuracy:.0%}"
                       if best.refusal_accuracy is not None else "n/a")
        lines.append(
            f"\n- TTFT-gen p50: **{best.ttft_gen_p50_ms}ms**  "
            f"| Ingest p50: **{best.prompt_eval_p50_ms}ms**  "
            f"| Total p50: **{best.total_p50_ms:.0f}ms**  "
            f"| Tok/s: **{best.tokens_per_sec:.1f}**\n"
            f"- Coherencia: **{best.coherence:.2f}**  "
            f"| Halluc.: **{best.hallucination:.2f}**  "
            f"| Refusal acc.: **{refusal_str}**"
        )

    lines.append("\n## Notas\n")
    lines.append("- **TTFT-gen** = tiempo desde el envío hasta el primer token *generado* "
                 "(descuenta ingestión del prompt). Es la métrica real de fluidez percibida.")
    lines.append("- **Ingest p50** = `prompt_eval_duration`. Se amortiza entre llamadas "
                 "gracias a `keep_alive` + KV cache del prefijo del system prompt.")
    lines.append("- **Coherencia** combina: idioma ES, grounding numérico, no-repetición, markdown "
                 "y penalty multiplicativa por cifras alucinadas.")
    lines.append("- **Halluc.** (1.0 = sin cifras inventadas) es la métrica más importante para "
                 "el AI Analytics Studio: un número falso invalida toda la respuesta.")
    lines.append("- **Refusal accuracy** mide si el modelo dice 'No hay datos disponibles' ante "
                 "preguntas fuera del contexto, en vez de improvisar.")
    lines.append("- Para experiencia fluida en UI, prioriza configuraciones con "
                 "`TTFT-gen p50 < 500ms` y `Total p50 < 5s`.")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path


# --------------------------------------------------------------------------- #
#  Main                                                                       #
# --------------------------------------------------------------------------- #

def resolve_models(args_models: Optional[str], url: str) -> List[str]:
    if args_models:
        return [m.strip() for m in args_models.split(",") if m.strip()]
    # Auto-detect instalados y elegir SLMs pequeños/medianos para analytics
    if SLM_AVAILABLE:
        try:
            mgr = SLMManager(url)
            status = mgr.check_ollama_status()
            if status.get("status") == "online":
                installed = mgr.get_installed_models(refresh=True)
                names = [m.name for m in installed]
                if names:
                    return names[:3]  # limitar a 3 para no tardar
        except Exception:  # noqa: BLE001
            pass
    return [DEFAULT_MODEL]


def ollama_online(url: str) -> bool:
    try:
        r = requests.get(f"{url}/api/tags", timeout=5)
        return r.ok
    except Exception:  # noqa: BLE001
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Tune Ollama SLM params for analytics.")
    parser.add_argument("--url", default=OLLAMA_URL, help="Ollama URL")
    parser.add_argument("--model", help="Single model name (shortcut for --models)")
    parser.add_argument("--models", help="Comma-separated model list")
    parser.add_argument("--full", action="store_true", help="Use full parameter grid")
    parser.add_argument("--repeats", type=int, default=2, help="Repeats per (config,query)")
    parser.add_argument("--warmup", type=int, default=1, help="Warmup rounds per model")
    parser.add_argument("--no-stream", action="store_true", help="Disable streaming (no TTFT)")
    parser.add_argument("--queries", type=int, default=0,
                        help="Limit queries (0 = all; useful for quick runs)")
    args = parser.parse_args()

    print(f"[i] Ollama URL: {args.url}")
    if not ollama_online(args.url):
        print("[x] Ollama no está accesible. Inicia `ollama serve` o ajusta --url / OLLAMA_URL.")
        return 2

    models: List[str] = []
    if args.model:
        models.append(args.model)
    models += resolve_models(args.models, args.url) if not args.model else []
    # dedupe preservando orden
    seen = set()
    models = [m for m in models if not (m in seen or seen.add(m))]
    if not models:
        models = [DEFAULT_MODEL]

    ctx = load_real_context(SCRAPER_OUTPUT_DIR)
    if not ctx:
        print(f"[x] No se encontraron outputs reales en {SCRAPER_OUTPUT_DIR}.")
        print("    Ejecuta primero el scraper para generar archivos JSON, por ejemplo:")
        print("      docker compose run --rm scraper python scraper_selenium.py "
              "--operacion venta --tipo departamento")
        print("    (La carpeta ./output está montada como /app/output dentro del contenedor,")
        print("     por lo que los JSON aparecerán en ambos lados.)")
        return 3
    print(f"[i] Contexto cargado desde {len(ctx['_source_files'])} archivos: "
          f"{ctx['stats']['total']} propiedades, {len(ctx['communes'])} comunas top.")

    grid = expand_full_grid() if args.full else QUICK_GRID
    all_queries = build_test_queries(ctx)
    # Default: 4 queries para reducir tiempo cubriendo los 4 casos útiles:
    # corto + numerico + fuera_contexto + followup (+ comparativo/ranking en --full).
    default_n = 4
    n = args.queries if args.queries else default_n
    queries = all_queries[:n]
    stream = not args.no_stream
    system = build_system_prompt(ctx)

    total_configs = len(models) * len(grid) * len(queries) * args.repeats
    print(f"[i] Modelos: {models}")
    print(f"[i] Grid size: {len(grid)} configs × {len(queries)} queries × "
          f"{args.repeats} repeats = {total_configs} runs por modelo")
    print(f"[i] Stream: {stream} | Warmup: {args.warmup}")
    print(f"[i] Output: {OUT_DIR}\n")

    all_results: List[RunResult] = []
    started = time.time()

    for model in models:
        print(f"=== Modelo: {model} ===")
        print("  · Warmup (calentando KV cache con system prompt real)...", flush=True)
        warmup(args.url, model, rounds=args.warmup, system=system)

        for ci, params in enumerate(grid, 1):
            for qi, query in enumerate(queries, 1):
                for rep in range(args.repeats):
                    res = run_single(args.url, model, system, query,
                                     params, stream, ctx)
                    all_results.append(res)
                    tag = "OK" if res.ok else f"ERR({res.error})"
                    ttft_gen = (f"ttft_gen={res.ttft_generation_ms}ms "
                                if res.ttft_generation_ms is not None else "")
                    halluc = res.coherence.get("hallucination", 1.0)
                    refusal_flag = ""
                    if query.expect_refusal:
                        refusal_flag = " refused=✓" if res.refused else " refused=✗"
                    print(
                        f"  [{ci:02d}/{len(grid)}] q={query.label:<15} "
                        f"rep={rep+1}/{args.repeats} {tag} "
                        f"{ttft_gen}total={res.total_ms}ms "
                        f"tps={res.tokens_per_sec} "
                        f"coh={res.coherence.get('overall', 0):.2f} "
                        f"halluc={halluc:.2f}{refusal_flag}",
                        flush=True,
                    )
        print()

    elapsed = time.time() - started
    summaries = summarize(all_results)
    meta = {
        "ollama_url": args.url,
        "models": models,
        "queries": [q.label for q in queries],
        "grid": "full" if args.full else "quick",
        "grid_size": len(grid),
        "repeats": args.repeats,
        "stream": stream,
        "total_runs": len(all_results),
        "ok_runs": sum(1 for r in all_results if r.ok),
        "elapsed_sec": round(elapsed, 1),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }
    json_path, md_path = write_reports(all_results, summaries, meta)

    print("=" * 70)
    print(f"✓ Completado en {elapsed:.1f}s. Runs OK: {meta['ok_runs']}/{meta['total_runs']}")
    print(f"  JSON:     {json_path}")
    print(f"  Markdown: {md_path}")
    if summaries:
        best = summaries[0]
        print("\n🏆 Mejor configuración:")
        print(f"   modelo={best.model}")
        print(f"   params={best.params}")
        refusal_str = (f"{best.refusal_accuracy:.0%}"
                       if best.refusal_accuracy is not None else "n/a")
        print(f"   TTFT-gen p50={best.ttft_gen_p50_ms}ms  ingest p50={best.prompt_eval_p50_ms}ms  "
              f"total p50={best.total_p50_ms:.0f}ms  tok/s={best.tokens_per_sec}")
        print(f"   coh={best.coherence:.2f}  halluc={best.hallucination:.2f}  "
              f"refusal={refusal_str}  score={best.score:.2f}")
    return 0 if meta["ok_runs"] > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
