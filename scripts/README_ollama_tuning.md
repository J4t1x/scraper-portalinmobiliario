# Ollama SLM Tuning Harness

Script: [`scripts/test_ollama_params.py`](./test_ollama_params.py)

Optimiza la parametrización de Ollama para el `AnalyticsAgent` del dashboard (AI Analytics Studio), buscando **respuestas rápidas, coherentes y sin cifras alucinadas** usando **datos reales** generados por el scraper.

---

## 1. Qué hace

1. Carga los outputs reales más recientes desde `output/*.json` y arma un contexto estilo dashboard: `stats`, `market_stats`, `communes`, `opportunities`.
2. Usa como **system prompt la fuente única de verdad** (`ai/prompts.py → build_analytics_system_prompt`), el mismo que corre en producción.
3. Calienta el KV cache por modelo enviando el system prompt real (warmup) y ejecuta una **matriz de configuraciones** (grid) sobre un set de queries representativas:
   - `corto`, `numerico`, `comparativo`, `ranking` (factuales),
   - `fuera_contexto` → el modelo **debe rehusarse** ("No hay datos…") sin inventar,
   - `followup` → **multi-turno** (simula un chat con historial previo).
4. Mide por cada corrida:
   - **TTFT total** y **TTFT-gen** (= `ttft - prompt_eval`, percepción pura tras ingestión).
   - **Ingest p50** (`prompt_eval_duration` aislado).
   - Latencia total, tokens/seg, `eval_count`, `load/prompt/eval_duration`.
   - **Coherencia** (idioma ES, grounding numérico, repeticiones, markdown, utilidad, truncado, longitud, penalty genérica/coach).
   - **Hallucination penalty** (multiplicativa): castiga cifras que no están en el contexto ni en la pregunta (whitelist mínima 0–10, 100).
   - **Refusal accuracy** sobre queries `fuera_contexto`.
5. Calcula un **score** = `0.5·fluidez + 0.3·coherencia + 0.2·estabilidad` (mediana entre repeticiones).
6. Exporta `JSON` + `Markdown` a `logs/ollama_tuning/` con ranking top-10 y **parámetros recomendados** para copiar a `ai/agent.py`.

---

## 2. Requisitos

- Servicios `ollama` y `dashboard` (o `scraper`) levantados:
  ```bash
  docker compose up -d ollama dashboard postgres
  ```
- Al menos un modelo instalado en Ollama (default: `qwen2.5-coder:1.5b`).
- La carpeta `output/` debe contener **al menos un JSON** del scraper. Si está vacía el script imprime instrucciones y sale con exit code `3`.

Bind mounts (ya configurados en `docker-compose.yml`):
- `./output:/app/output`
- `./logs:/app/logs`
- `./scripts:/app/scripts` ← permite editar el script sin rebuild
- `./ai:/app/ai`

---

## 3. Ejecución (siempre desde contenedor)

### Modo rápido (recomendado para iterar)

```bash
docker exec -it portalinmobiliario-dashboard \
  python3 -u scripts/test_ollama_params.py --repeats 2
```

- Grid: **2 perfiles** (ultra-corto `ctx=1024` + balanceado `ctx=2048`).
- Queries: **4 por default** (`corto`, `numerico`, `fuera_contexto`, `followup`).
- **16 runs por modelo** (2 configs × 4 queries × 2 repeats), ~2-4 min en CPU.

### Modo completo (barrido afinado)

```bash
docker exec -it portalinmobiliario-dashboard \
  python3 -u scripts/test_ollama_params.py --full --repeats 2
```

- Grid: **12 combos** (`top_p × top_k × num_predict` = 2×2×3, con `temperature=0.2`, `num_ctx=2048`, `repeat_penalty=1.15` fijos).
- 12 configs × 4 queries × 2 repeats = **96 runs por modelo**, ~10-15 min.
- Úsalo si el modo rápido deja empate (Δscore < 0.05 entre top-1 y top-2).

### Modelos específicos

```bash
# Un solo modelo
docker exec -it portalinmobiliario-dashboard \
  python3 -u scripts/test_ollama_params.py --model qwen2.5-coder:1.5b

# Lista
docker exec -it portalinmobiliario-dashboard \
  python3 -u scripts/test_ollama_params.py --models qwen2.5-coder:1.5b,phi3:mini
```

---

## 4. Argumentos CLI

| Flag | Default | Descripción |
|---|---|---|
| `--url` | `http://localhost:11434` | URL de Ollama. Dentro del compose usar `http://ollama:11434` (ya inyectado via env). |
| `--model` | — | Un solo modelo (atajo de `--models`). |
| `--models` | auto-detect (top 3 instalados) | Lista separada por coma. |
| `--full` | `False` | Usa `FULL_GRID_AXES` en lugar del quick grid. |
| `--repeats` | `2` | Repeticiones por (config, query). Mediana para robustez. |
| `--warmup` | `1` | Rondas de warmup por modelo (evita sesgo por cold-start). |
| `--no-stream` | `False` | Desactiva streaming (no mide TTFT). |
| `--queries` | `0` (= 4 por default) | Limita cantidad de queries (toma las primeras N del set). |

Variables de entorno:
- `OLLAMA_URL` — default `http://localhost:11434` (en contenedor `dashboard` ya apunta a `http://ollama:11434`).
- `OLLAMA_MODEL` — modelo por defecto si no se pasa `--model` y no hay SLM autodetectado. Default: `qwen2.5-coder:1.5b`.
- `SCRAPER_OUTPUT_DIR` — override de la carpeta de outputs. Default: `/app/output`.
- `UF_TO_CLP` — valor UF para normalizar precios. Default: `38500`.

---

## 5. Salida

Se genera por cada corrida en `logs/ollama_tuning/`:

```
logs/ollama_tuning/
├── ollama_tuning_YYYYMMDD_HHMMSS.json   # runs + summaries + meta
└── ollama_tuning_YYYYMMDD_HHMMSS.md     # ranking top 10 + recomendación
```

El Markdown del reporte (`ollama_tuning_*.md`) incluye:

- Top-10 del ranking con columnas: **Modelo, Params, TTFT-gen p50, Ingest p50, Total p50, Tok/s, Coh, Halluc, Refusal, Fluidez, Estab, Score**.
- Bloque `options` listo para pegar en `ai/agent.py`:

```python
options = {
    "temperature": 0.2,
    "top_p": 0.8,
    "top_k": 20,
    "num_predict": 80,
    "num_ctx": 1024,
    "repeat_penalty": 1.15,
    "num_thread": 4,  # auto: max(2, cpu_count // 2)
}
```

---

## 6. Métricas y scoring

### Fluidez (0..1)
Basada en **TTFT-gen** (time-to-first-*generated*-token = `ttft - prompt_eval`), no en TTFT total: la ingestión del prompt se amortiza vía `keep_alive` + KV cache.
- `ttft_norm`: 150ms → 1.0, 1500ms → 0.0
- `total_norm`: 1500ms → 1.0, 10000ms → 0.0
- `fluidity = 0.6·ttft_norm + 0.4·total_norm`

### Coherencia (0..1)
Base aditiva (pesos fijos):
- `0.25` **Español** (`_spanish_ratio`) — frecuencia de stopwords ES.
- `0.35` **Grounding numérico** (`_numeric_grounding`) — números del contexto real presentes en la respuesta.
- `0.15` **No-repetición** — penaliza 4-gramas duplicados.
- `0.10` **Markdown** — listas o énfasis.
- `0.15` **Penalty genérica** — castiga "es importante…", "en el mercado…", etc.

Mezcla con **utilidad** (tiene cifras Y menciona una comuna real) al 50/50, y luego penalizaciones **multiplicativas**:
- **Longitud** — óptima < 300 chars; `0.4` si > 1000.
- **Coach penalty** — palabras tipo "aprende", "te ayudará", "investigar".
- **Truncado** (`0.6`) — termina en `**`, `:`, `-`, `,`, sin puntuación de cierre.
- **Hallucination penalty** — `1 - 0.25·n_cifras_inventadas` (números no presentes en contexto/pregunta, whitelist `{0..10, 100}`). Es el castigo más fuerte: un número falso puede bajar `overall` a 0.

### Estabilidad (0..1)
`1 - CV` (coef. de variación) de la coherencia entre repeticiones.

### Refusal accuracy
Solo sobre queries con `expect_refusal=True` (p.ej. `fuera_contexto`). Premia que la respuesta contenga marcadores tipo "no hay datos", "no tengo datos", "no dispongo", "fuera del contexto". No afecta al score global; se reporta aparte.

### Score final
`score = 0.5·fluidez + 0.3·coherencia + 0.2·estabilidad` (mediana entre repeticiones).

---

## 7. Optimizaciones aplicadas

- **System prompt unificado** vía `ai.prompts.build_analytics_system_prompt` → se mide exactamente lo que corre en producción (SSOT).
- **Warmup con system real** → calienta el KV cache del prefijo; el primer run real no paga la ingestión completa.
- **`keep_alive: 30m`** en cada request → evita la descarga del modelo entre configs (eliminó picos de TTFT ~19s observados en pruebas previas).
- **`seed: 42`** → runs reproducibles.
- **`num_thread`** dinámico: `max(2, cpu_count // 2)`.
- **`num_predict` dinámico por tipo de query** (capado por el grid):
  - `corto=60`, `numerico=120`, `ranking=120`, `comparativo=140`.
  - Queries `expect_refusal` → `num_predict=40` (respuestas deben ser brevísimas).
- **Multi-turno**: las queries pueden incluir `prior_turns` (historial user/assistant) para medir el comportamiento real del chat del Analytics Studio.
- **Retry** automático (1 vez) con parámetros más estrictos (`T=0.2, top_p=0.8, top_k=20, num_predict=80`) si la respuesta falla `is_valid` (< 800 chars y ≥ 1 número). **No aplica** a queries de refusal (una respuesta corta sin números es la correcta).
- **Datos reales** desde `output/*.json` (hasta 12 archivos más recientes): el grounding, las comunas y las oportunidades provienen del dataset actual. Precios normalizados a CLP usando `UF_TO_CLP`.

---

## 8. Flujo recomendado

1. Asegúrate de tener datos: `ls output/*.json` — si está vacío, corre primero el scraper.
2. **Quick pass:**
   ```bash
   docker exec -it portalinmobiliario-dashboard \
     python3 -u scripts/test_ollama_params.py --repeats 2
   ```
3. Revisa el top-10 en `logs/ollama_tuning/*.md`.
4. Si el ganador es claro (Δscore ≥ 0.05 vs #2), copia el bloque `options` a `ai/agent.py` (métodos `ask` y `ask_stream`).
5. Si hay empate, **full pass** para desempatar:
   ```bash
   docker exec -it portalinmobiliario-dashboard \
     python3 -u scripts/test_ollama_params.py --full --repeats 2
   ```
6. Repite cuando cambies de modelo o cuando el dataset crezca significativamente (el grounding depende de los datos).

---

## 9. Troubleshooting

| Síntoma | Causa probable | Fix |
|---|---|---|
| `python: can't open file '/app/scripts/...'` | Imagen construida antes de agregar el script | Ya resuelto con bind mount `./scripts:/app/scripts`. Recrear si hace falta: `docker compose up -d --force-recreate dashboard`. |
| Exit `3`: no hay outputs | `output/` vacío | Corre primero el scraper o copia un JSON de ejemplo. |
| TTFT = 15-20s en rep=1 de cada config | Ollama unload entre configs | Ya mitigado con `keep_alive: 30m`. Si persiste, aumentar a `"1h"`. |
| `ConnectionError` hacia Ollama | Servicio no está up o URL incorrecta | `docker compose ps ollama` y verificar `OLLAMA_URL=http://ollama:11434` dentro del contenedor. |
| Todos los runs con `coh` muy baja | Grounding numérico falla por formato de número | Revisar `derive_grounding()` / `_extract_numbers()` (normaliza separadores `.` y `,`). Verificar que los números del contexto aparezcan en la respuesta. |
| `halluc < 1.0` persistente | El modelo inventa cifras (%/precios) | Bajar `temperature` a 0.1, reducir `num_predict`, y revisar el system prompt en `ai/prompts.py` (reglas de "no inventar"). |
| `refusal_accuracy` baja | El modelo improvisa ante preguntas fuera de contexto | Reforzar en `ai/prompts.py` la instrucción de decir "No hay datos disponibles" literal, y verificar que esté en `REFUSAL_MARKERS`. |
| KeyboardInterrupt durante `--full` | Grid grande (96 runs/modelo) | Usar `--queries 2` o `--repeats 1`, o limitar con `--model`. |
