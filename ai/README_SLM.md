# Small Language Models (SLM) Integration

## 📋 Descripción

Sistema completo de gestión de **Small Language Models** para AI Analytics Studio, optimizado para análisis inmobiliario con Ollama.

## 🎯 Características

### ✅ Implementado

- **Catálogo de 8+ modelos SLM** optimizados para analytics
- **Auto-detección** de modelos instalados en Ollama
- **Gestión completa** de modelos (listar, descargar, eliminar, cambiar)
- **Benchmarking** de rendimiento con métricas detalladas
- **Filtros inteligentes** por tamaño, tarea y estado
- **API REST completa** para integración
- **Dashboard interactivo** con Alpine.js
- **Métricas de rendimiento** (Speed, Quality, Overall)
- **Soporte multi-modelo** en AnalyticsAgent

## 📁 Estructura

```
ai/
├── slm_manager.py      # Gestor de modelos SLM
├── agent.py            # Agente de analytics con soporte SLM
└── README_SLM.md       # Esta documentación

api/
└── slm_routes.py       # API endpoints para SLM

templates/dashboard/
└── ai_analytics.html   # Dashboard con gestión SLM

test_slm_integration.py # Suite de tests
```

## 🚀 Uso Rápido

### 1. Inicializar SLM Manager

```python
from ai.slm_manager import SLMManager, SLMCatalog

# Crear manager
manager = SLMManager()

# Verificar Ollama
status = manager.check_ollama_status()
print(f"Ollama: {status['status']}")

# Listar modelos instalados
installed = manager.get_installed_models()
for model in installed:
    print(f"- {model.display_name} ({model.size_mb}MB)")
```

### 2. Obtener Recomendaciones

```python
# Mejores modelos para analytics
analytics_models = manager.get_recommendations('analytics')

# Modelo más rápido
fastest = manager.get_recommendations('fast')

# Mejor calidad
best_quality = manager.get_recommendations('quality')
```

### 3. Descargar y Usar Modelo

```python
# Descargar modelo
success, message = manager.pull_model('qwen2.5-coder:1.5b')

# Cambiar modelo en el agente
from ai.agent import AnalyticsAgent
agent = AnalyticsAgent()
agent.switch_model('qwen2.5-coder:1.5b')

# Hacer consulta
response = agent.ask("¿Cuántas propiedades hay?", context)
```

### 4. Benchmark

```python
# Benchmark de rendimiento
result = manager.benchmark_model('qwen2.5-coder:1.5b')

print(f"Duración: {result['duration_ms']}ms")
print(f"Tokens/seg: {result['tokens_per_second']:.2f}")
```

## 🔌 API Endpoints

### Estado y Listado

```bash
# Estado del sistema SLM
GET /api/v2/slm/status

# Todos los modelos (catálogo + instalados)
GET /api/v2/slm/models

# Solo modelos instalados
GET /api/v2/slm/models/installed

# Modelos recomendados
GET /api/v2/slm/models/recommended?use_case=analytics
```

### Gestión de Modelos

```bash
# Cambiar modelo activo
POST /api/v2/slm/models/switch
Content-Type: application/json
{ "model": "qwen2.5-coder:3b" }

# Descargar modelo
POST /api/v2/slm/models/pull
Content-Type: application/json
{ "model": "phi3:mini" }

# Eliminar modelo
DELETE /api/v2/slm/models/qwen2.5-coder:0.5b

# Benchmark
POST /api/v2/slm/models/qwen2.5-coder:1.5b/benchmark
Content-Type: application/json
{ "prompt": "Analiza el mercado inmobiliario" }
```

### Catálogo

```bash
# Categorías de tamaño
GET /api/v2/slm/catalog/sizes

# Categorías de tareas
GET /api/v2/slm/catalog/tasks
```

## 📊 Modelos Disponibles

### Tiny (< 1B parámetros)
| Modelo | Tamaño | Speed | Quality | Overall | Uso |
|--------|--------|-------|---------|---------|-----|
| qwen2.5-coder:0.5b | 352MB | 100 | 55 | 60 | Consultas básicas |

### Small (1-3B parámetros)
| Modelo | Tamaño | Speed | Quality | Overall | Uso |
|--------|--------|-------|---------|---------|-----|
| **qwen2.5-coder:1.5b** | 934MB | 90 | 70 | **75** | **Recomendado** |
| phi3:mini | 2.3GB | 85 | 78 | 80 | Razonamiento |
| gemma2:2b | 1.6GB | 88 | 75 | 78 | General |

### Medium (3-7B parámetros)
| Modelo | Tamaño | Speed | Quality | Overall | Uso |
|--------|--------|-------|---------|---------|-----|
| qwen2.5-coder:3b | 1.9GB | 75 | 85 | 85 | Análisis detallado |
| llama3.2:3b | 2GB | 80 | 87 | 88 | Razonamiento avanzado |
| qwen2.5-coder:7b | 4.7GB | 65 | 92 | 92 | Máxima calidad |

### Large (7-13B parámetros)
| Modelo | Tamaño | Speed | Quality | Overall | Uso |
|--------|--------|-------|---------|---------|-----|
| qwen2.5:7b | 4.7GB | 70 | 90 | 90 | Análisis estratégico |

## 🧪 Testing

### Ejecutar Tests

```bash
# Suite completa de tests
python test_slm_integration.py

# Tests individuales
python -c "from ai.slm_manager import SLMManager; m = SLMManager(); print(m.check_ollama_status())"
```

### Tests Incluidos

1. ✅ **Catalog Test** - Verificar catálogo de modelos
2. ✅ **Manager Test** - Conexión Ollama y listado
3. ✅ **Agent Integration** - Integración con AnalyticsAgent
4. ✅ **Model Switching** - Cambio de modelos
5. ✅ **Benchmarking** - Medición de rendimiento

## 🎨 Dashboard

### Características del Dashboard

- **Chat interactivo** con IA
- **Panel lateral** con gestión de modelos
- **Filtros** por tamaño, tarea, estado
- **Métricas en tiempo real** (latencia, tokens, modelo)
- **Descarga directa** de modelos
- **Benchmark visual** con resultados
- **Badges informativos** de rendimiento

### Acceso

1. Iniciar sesión en el dashboard
2. Ir a **AI Analytics** en el menú
3. Panel lateral → Modelos SLM

## 🔧 Configuración

### Variables de Entorno

```bash
# .env
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:1.5b
```

### Requisitos

```bash
# Ollama debe estar instalado y corriendo
ollama serve

# Descargar modelo inicial
ollama pull qwen2.5-coder:1.5b
```

## 📈 Métricas de Rendimiento

### Scores Explicados

- **Speed Score (0-100)**: Velocidad de respuesta
  - 90-100: Ultra-rápido (< 1s)
  - 70-89: Rápido (1-2s)
  - 50-69: Moderado (2-4s)

- **Quality Score (0-100)**: Calidad de respuestas
  - 85-100: Excelente
  - 70-84: Buena
  - 50-69: Aceptable

- **Overall Score (0-100)**: Rendimiento general
  - Combina speed, quality y eficiencia de recursos

### Benchmarks Típicos

| Modelo | Latencia | Tokens/seg | Uso RAM |
|--------|----------|------------|---------|
| qwen2.5-coder:0.5b | 500ms | 80 | 1GB |
| qwen2.5-coder:1.5b | 800ms | 60 | 1.5GB |
| qwen2.5-coder:3b | 1200ms | 45 | 2.5GB |
| qwen2.5-coder:7b | 2000ms | 30 | 5GB |

## 🐛 Troubleshooting

### Ollama Offline

```bash
# Verificar servicio
ps aux | grep ollama

# Iniciar Ollama
ollama serve

# Verificar puerto
curl http://localhost:11434/api/tags
```

### Modelo No Disponible

```bash
# Listar modelos instalados
ollama list

# Descargar modelo
ollama pull qwen2.5-coder:1.5b

# Verificar en Python
python -c "from ai.slm_manager import SLMManager; print(SLMManager().get_installed_models())"
```

### Error de Memoria

- Usar modelos más pequeños (< 3B)
- Cerrar otros procesos
- Aumentar swap si es necesario

## 📚 Referencias

- [Ollama Documentation](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Small Language Models Article](https://medium.com/@lekhashree2012/small-language-models-slms-the-lightweight-ai-revolution-everyones-talking-about-in-2025-b7db3d228bc2)
- [Qwen2.5 Models](https://github.com/QwenLM/Qwen2.5)
- [Phi-3 Models](https://azure.microsoft.com/en-us/products/phi-3)
- [Gemma Models](https://ai.google.dev/gemma)
- [Llama 3.2](https://llama.meta.com/)

## 🤝 Contribuir

Para agregar nuevos modelos al catálogo:

1. Editar `ai/slm_manager.py`
2. Agregar modelo a `SLMCatalog.MODELS`
3. Especificar: nombre, tamaño, scores, tareas
4. Ejecutar tests: `python test_slm_integration.py`

---

**Versión:** 1.0.0  
**Fecha:** Abril 2026  
**Autor:** AI Dev Engine (Cascade)
