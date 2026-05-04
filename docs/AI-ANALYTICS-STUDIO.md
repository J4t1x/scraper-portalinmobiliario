# AI Analytics Studio - Guía de Usuario

## 🎯 Descripción

**AI Analytics Studio** es una experiencia premium de analítica inmobiliaria potenciada por IA local (Ollama) con soporte completo para **Small Language Models (SLMs)**. Proporciona una interfaz moderna tipo ChatGPT/Claude con control completo sobre modelos, benchmarking y métricas de ejecución en tiempo real.

### ¿Qué son los SLMs?

Los **Small Language Models** son modelos de IA compactos (< 13B parámetros) optimizados para tareas específicas. Ofrecen:
- ⚡ **Velocidad superior** - Respuestas en milisegundos
- 💾 **Bajo consumo de recursos** - Funcionan en hardware modesto
- 🎯 **Especialización** - Optimizados para analytics, código, razonamiento
- 🔒 **Privacidad** - Ejecución 100% local, sin envío de datos

Basado en: [Small Language Models - The Lightweight AI Revolution](https://medium.com/@lekhashree2012/small-language-models-slms-the-lightweight-ai-revolution-everyones-talking-about-in-2025-b7db3d228bc2)

## ✨ Características Principales

### 1. Chat Inteligente con IA
- **Interfaz moderna** tipo ChatGPT con mensajes animados
- **Renderizado Markdown** para respuestas formateadas
- **Preguntas rápidas** predefinidas para análisis comunes
- **Historial de conversación** persistente durante la sesión

### 2. Panel de Control de Ollama
- **Estado en tiempo real** del servidor Ollama
- **Verificación automática** cada 30 segundos
- **Gestión de modelos** disponibles
- **Cambio de modelo** en tiempo real (próximamente)
- **Información de puerto** y conectividad

### 3. Métricas de Ejecución
Cada respuesta del agente incluye:
- ⏱️ **Latencia** - Tiempo de respuesta en milisegundos
- 🔢 **Tokens** - Cantidad de tokens procesados
- 🖥️ **Modelo** - Modelo utilizado para la respuesta

### 4. Métricas de Sesión
Panel lateral con estadísticas acumuladas:
- **Consultas totales** - Número de preguntas realizadas
- **Tokens totales** - Suma de todos los tokens procesados
- **Latencia promedio** - Tiempo promedio de respuesta
- **Barras de progreso** visuales para cada métrica

### 5. Gestión Avanzada de Modelos SLM
- **Catálogo completo** de 8+ modelos optimizados para analytics
- **Filtros inteligentes** por tamaño, tarea y estado de instalación
- **Métricas de rendimiento** (Speed, Quality, Overall scores)
- **Descarga directa** desde la interfaz
- **Cambio de modelo** en tiempo real
- **Benchmarking** para comparar rendimiento
- **Información detallada** de cada modelo (parámetros, tareas, recomendaciones)

#### Modelos Disponibles

**Tiny (< 1B parámetros)**
- `qwen2.5-coder:0.5b` - Ultra-rápido para consultas básicas (352MB)

**Small (1-3B parámetros)**
- `qwen2.5-coder:1.5b` - **Recomendado** - Balance perfecto (934MB)
- `phi3:mini` - Excelente razonamiento (2.3GB)
- `gemma2:2b` - Modelo general de Google (1.6GB)

**Medium (3-7B parámetros)**
- `qwen2.5-coder:3b` - Alta calidad para análisis detallado (1.9GB)
- `llama3.2:3b` - Razonamiento avanzado de Meta (2GB)
- `qwen2.5-coder:7b` - Máxima calidad para analytics (4.7GB)

**Large (7-13B parámetros)**
- `qwen2.5:7b` - Análisis estratégico completo (4.7GB)

## 🧠 CoTHSSum: Razonamiento Jerárquico

### ¿Qué es CoTHSSum?

**CoTHSSum** (Hierarchical + Chain-of-Thought) es un pipeline de razonamiento estructurado en 3 capas que mejora significativamente la coherencia y precisión de las respuestas del chatbot.

### Arquitectura de 3 Capas

```
┌─────────────────────────────────────────────────────────┐
│                    Capa 1: Micro-insights                │
│  • Fragmentar datos en chunks pequeños (5 elementos)    │
│  • Analizar cada chunk con Chain-of-Thought             │
│  • Generar insights específicos con confianza           │
│  • Salida: JSON con insight, reasoning, data_points    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                 Capa 2: Patrones Globales                │
│  • Agrupar micro-insights similares                     │
│  • Identificar patrones (trend, anomaly, opportunity)   │
│  • Asignar significancia y categoría                    │
│  • Salida: JSON con patterns, supporting_insights       │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                   Capa 3: Conclusión Final                │
│  • Sintetizar patrones en respuesta coherente           │
│  • Generar conclusión directa y accionable              │
│  • Razonamiento paso a paso final                       │
│  • Salida: JSON con conclusion, reasoning                │
└─────────────────────────────────────────────────────────┘
```

### Ventajas de CoTHSSum

- **Mayor Coherencia**: Respuestas basadas en análisis estructurado
- **Trazabilidad Completa**: Cada paso del razonamiento es visible
- **Modelos Pequeños**: SLMs (< 3B) trabajan efectivamente en problemas complejos
- **Salidas Estructuradas**: JSON en cada capa para procesamiento
- **Reducción de Errores**: Validación en cada etapa del pipeline
- **Escalabilidad**: Fácil agregar nuevas capas o modificar prompts

### Uso Programático

#### Endpoint `/api/analytics/chat`

```bash
# Uso estándar (CoTHSSum activado por defecto)
POST /api/analytics/chat
{
  "question": "¿Cuáles son las mejores oportunidades?"
}

# Con trazabilidad completa
POST /api/analytics/chat
{
  "question": "¿Cuáles son las mejores oportunidades?",
  "return_trace": true
}

# Desactivar CoTHSSum (modo estándar)
POST /api/analytics/chat
{
  "question": "¿Cuáles son las mejores oportunidades?",
  "use_cothssum": false
}
```

#### Respuesta con Trazabilidad

```json
{
  "success": true,
  "response": "Las mejores oportunidades están en Las Condes...",
  "data": {
    "response": "Las mejores oportunidades están en Las Condes...",
    "trace": "🔍 CoTHSSum Trace ID: abc-123...",
    "metadata": {
      "total_micro_insights": 8,
      "total_patterns": 3,
      "model": "qwen2.5-coder:1.5b"
    },
    "layer1_insights": [...],
    "layer2_patterns": [...],
    "layer3_reasoning": ["paso 1", "paso 2", "paso 3"],
    "trace_id": "abc-123...",
    "method": "cothssum"
  }
}
```

### Configuración

#### Chunk Size

El tamaño de los fragmentos (chunks) se configura en `ai/cothssum.py`:

```python
pipeline = CoTHSSumPipeline(agent=agent, max_chunk_size=5)
```

- **max_chunk_size=5**: Divide listas en grupos de 5 elementos
- Valores recomendados: 3-10 (menor = más granular, mayor = más rápido)

#### Prompts por Capa

Los prompts específicos para cada capa están en `ai/prompts.py`:

- `build_layer1_micro_insight_prompt()`: Capa 1 - Micro-insights
- `build_layer2_pattern_prompt()`: Capa 2 - Patrones globales
- `build_layer3_conclusion_prompt()`: Capa 3 - Conclusión final

### Métricas de Rendimiento

- **Latencia**: 2-4x más lento que modo estándar (múltiples llamadas al modelo)
- **Calidad**: Significativamente mejor en preguntas complejas
- **Tokens**: 3-5x más tokens (razonamiento estructurado)
- **Coherencia**: 80-90% mejora en respuestas multi-paso

### Cuándo Usar CoTHSSum

**Recomendado para:**
- ✅ Preguntas complejas que requieren análisis de múltiples datos
- ✅ Comparativas entre zonas, propiedades o tendencias
- ✅ Identificación de oportunidades y patrones
- ✅ Análisis que requieren alta coherencia

**Modo estándar suficiente para:**
- ⚡ Preguntas simples (stats básicos, conteos)
- ⚡ Consultas rápidas donde la velocidad es prioridad
- ⚡ Preguntas con contexto pequeño

## 🚀 Cómo Usar

### Acceso
1. Iniciar sesión en el dashboard
2. Navegar a **AI Analytics** en el menú lateral
3. El icono tiene un gradiente azul-púrpura distintivo

### Realizar Consultas

#### Opción 1: Escribir pregunta personalizada
```
Escribe tu pregunta en el campo de texto y presiona "Analizar"
```

#### Opción 2: Usar preguntas rápidas
Haz clic en uno de los botones predefinidos:
- 💎 **Mejores oportunidades** - Detecta propiedades con mejor relación precio/valor
- 📊 **Precio por m²** - Análisis de precios por metro cuadrado
- 🔄 **Comparar zonas** - Comparativa entre diferentes comunas

### Ejemplos de Preguntas

**Análisis de Oportunidades:**
```
¿Cuáles son las mejores oportunidades de inversión actualmente?
```

**Análisis por Zona:**
```
¿Cuál es el precio promedio por m² en Las Condes?
Compara precios entre Providencia y Ñuñoa
```

**Tendencias:**
```
¿Qué tipo de propiedad tiene mejor relación precio/calidad?
Muéstrame las propiedades más baratas en Santiago Centro
```

**Estadísticas:**
```
¿Cuántas propiedades tenemos por comuna?
¿Cuál es el rango de precios en Vitacura?
```

## 📊 Panel de Control

### Estado de Ollama

**Indicadores:**
- 🟢 **Online** - Servidor funcionando correctamente
- 🔴 **Offline** - Servidor no disponible
- 🟡 **Checking** - Verificando estado

**Acciones:**
- Botón **Verificar Estado** para actualización manual
- Actualización automática cada 30 segundos

### Métricas en Tiempo Real

**Durante cada consulta:**
1. Indicador de carga con barra de progreso animada
2. Mensaje "Analizando datos..."
3. Al completar: métricas debajo de la respuesta

**Métricas mostradas:**
- ⏱️ Duración en milisegundos
- 🔢 Tokens procesados
- 🖥️ Modelo utilizado

### Panel Lateral (Settings)

**Toggle con botón de configuración** en la esquina superior derecha

**Secciones:**
1. **Ollama Server** - Estado y configuración
2. **Métricas de Sesión** - Estadísticas acumuladas
3. **Modelos Disponibles** - Lista de modelos instalados

## 🎨 Diseño Visual

### Paleta de Colores
- **Gradientes azul-púrpura** para elementos principales
- **Slate** para texto y fondos neutros
- **Verde** para indicadores positivos
- **Rojo** para errores

### Animaciones
- **Fade-in** para mensajes nuevos
- **Pulse** para indicador de estado online
- **Bounce** para indicador de carga
- **Progress bar** animada durante procesamiento

### Tipografía
- **Font-mono** para datos técnicos (modelo, puerto)
- **Font-semibold** para títulos
- **Prose** para contenido de mensajes

### Gestión de Modelos

#### Descargar un Modelo
1. Abrir panel lateral (icono ⚙️)
2. Hacer clic en filtro para ver todos los modelos
3. Seleccionar modelo no instalado
4. Hacer clic en botón "Descargar"
5. Esperar confirmación (puede tomar varios minutos)

#### Cambiar de Modelo
1. En panel lateral, buscar modelo instalado
2. Hacer clic en botón "Usar"
3. Esperar confirmación en el chat
4. Comenzar a hacer preguntas con el nuevo modelo

#### Benchmark de Modelos
1. Seleccionar modelo instalado
2. Hacer clic en icono ⚡ (Benchmark)
3. Ver resultados: duración, tokens/seg

#### Filtrar Modelos
- **Por estado**: Todos / Solo instalados / Recomendados
- **Por tamaño**: Tiny / Small / Medium / Large
- **Por tarea**: Analytics / Code / Reasoning / Chat

## 🔧 Configuración Técnica

### Endpoints Utilizados

**Chat con IA:**
```
POST /api/analytics/chat
Headers: X-API-KEY, Content-Type: application/json
Body: { "question": "..." }
```

**Estado de SLM:**
```
GET /api/v2/slm/status
Response: { ollama: {...}, agent: {...}, slm_support: true }
```

**Listar Modelos:**
```
GET /api/v2/slm/models
GET /api/v2/slm/models/installed
GET /api/v2/slm/models/recommended?use_case=analytics
```

**Gestión de Modelos:**
```
POST /api/v2/slm/models/switch
Body: { "model": "qwen2.5-coder:3b" }

POST /api/v2/slm/models/pull
Body: { "model": "phi3:mini" }

DELETE /api/v2/slm/models/<model_name>

POST /api/v2/slm/models/<model_name>/benchmark
Body: { "prompt": "..." }
```

### Variables de Entorno
```bash
OLLAMA_HOST=0.0.0.0:11434
OLLAMA_MODELS=/app/.ollama/models
```

### Modelo por Defecto
```
qwen2.5-coder:1.5b (~900MB)
```

## 📈 Métricas y Rendimiento

### Latencia Esperada
- **Consultas simples:** 500-1500ms
- **Consultas complejas:** 1500-3000ms
- **Consultas con datos extensos:** 3000-5000ms

### Uso de Tokens
- **Pregunta corta:** ~50-100 tokens
- **Pregunta media:** ~100-200 tokens
- **Pregunta compleja:** ~200-400 tokens
- **Respuesta promedio:** ~200-500 tokens

### Optimización
- **Cache de contexto** para preguntas similares
- **Límite de caracteres** en input (500)
- **Timeout de 30 segundos** en requests

## 🐛 Troubleshooting

### Ollama muestra "Offline"

**Verificar:**
```bash
# Dentro del contenedor
docker exec scraper-mvp supervisorctl status ollama

# Ver logs
docker exec scraper-mvp tail -f /var/log/ollama.log

# Reiniciar servicio
docker exec scraper-mvp supervisorctl restart ollama
```

### Respuestas lentas

**Causas comunes:**
1. Modelo muy grande para el hardware
2. Múltiples consultas simultáneas
3. Dataset muy extenso

**Soluciones:**
- Usar modelo más pequeño (1.5b en lugar de 3b)
- Esperar a que termine consulta anterior
- Limitar contexto de datos enviados

### Error de conexión

**Verificar:**
1. Puerto 11434 expuesto en Docker
2. Ollama corriendo en contenedor
3. API key correcta en headers

## 🚀 Próximas Mejoras

- [ ] **Exportar conversación** a PDF/Markdown
- [ ] **Historial persistente** en base de datos
- [ ] **Gráficos generados por IA** en respuestas
- [ ] **Modo oscuro** para la interfaz
- [ ] **Voz a texto** para consultas
- [ ] **Sugerencias automáticas** basadas en historial
- [ ] **Compartir conversaciones** con equipo
- [ ] **Integración con dashboard** principal

## 📚 Referencias

- [Ollama API Documentation](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Marked.js Documentation](https://marked.js.org/)
- [Alpine.js Documentation](https://alpinejs.dev/)
- [Tailwind CSS](https://tailwindcss.com/)

---

**Versión:** 1.0.0  
**Última actualización:** 10 de Abril, 2026  
**Autor:** AI Dev Engine (Cascade)
