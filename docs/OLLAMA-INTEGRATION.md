# Integración con Ollama

## Descripción

El scraper utiliza **Ollama** para el Agente de Analítica en lugar de OpenAI, permitiendo ejecutar modelos de IA localmente sin costos de API.

## Modelo Seleccionado

**`qwen2.5-coder:3b`** (1.9 GB)

### ¿Por qué este modelo?

1. **Especializado en análisis y código** - Familia Qwen Coder optimizada para tareas analíticas
2. **Tamaño óptimo** - 3B parámetros balancean capacidad y velocidad
3. **Rendimiento superior** - Mejor que phi4-mini para análisis de datos
4. **Eficiente** - Corre bien en Apple M1 con 5.3 GB VRAM disponible

### Modelos alternativos disponibles

Si necesitas cambiar el modelo, estos están disponibles:

- `qwen2.5-coder:1.5b` (986 MB) - Más rápido, menos capaz
- `phi4-mini:latest` (2.5 GB) - Alternativa general
- `ministral-3:3b` (3.0 GB) - Modelo de Mistral
- `granite4:3b` (2.1 GB) - Modelo de IBM

## Configuración

### 1. Instalar Ollama

```bash
# macOS/Linux
curl -fsSL https://ollama.ai/install.sh | sh

# O descargar desde: https://ollama.ai/download
```

### 2. Iniciar el servidor

```bash
ollama serve
```

El servidor escuchará en `http://localhost:11434`

### 3. Descargar el modelo

```bash
ollama pull qwen2.5-coder:3b
```

### 4. Verificar instalación

```bash
ollama list
```

Deberías ver `qwen2.5-coder:3b` en la lista.

## Variables de Entorno

En tu archivo `.env`:

```bash
# Configuración de Ollama (Agente de Analítica)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:3b
```

## Uso

El agente funciona exactamente igual que antes, pero ahora usa Ollama:

1. Asegúrate de que Ollama esté corriendo (`ollama serve`)
2. Inicia el dashboard Flask
3. Usa el chat del agente normalmente

## Ventajas vs OpenAI

✅ **Sin costos de API** - Todo local  
✅ **Sin límites de rate** - Sin restricciones de uso  
✅ **Privacidad total** - Los datos no salen de tu máquina  
✅ **Funciona offline** - No requiere conexión a internet  
✅ **Rápido** - Respuestas en segundos con hardware moderno  

## Desventajas vs OpenAI

⚠️ **Requiere recursos locales** - Necesitas RAM y CPU/GPU  
⚠️ **Calidad variable** - Modelos pequeños son menos capaces que GPT-4  
⚠️ **Setup inicial** - Requiere instalar Ollama y descargar modelos  

## Troubleshooting

### Error: "No se pudo conectar con Ollama"

```bash
# Verifica que Ollama esté corriendo
ollama serve

# En otra terminal, verifica la conexión
curl http://localhost:11434/api/tags
```

### Error: "Model not found"

```bash
# Descarga el modelo
ollama pull qwen2.5-coder:3b

# Verifica que esté instalado
ollama list
```

### Respuestas lentas

1. Usa un modelo más pequeño: `qwen2.5-coder:1.5b`
2. Verifica que tengas suficiente RAM disponible
3. Cierra otras aplicaciones pesadas

### Cambiar de modelo

Edita `.env`:

```bash
OLLAMA_MODEL=qwen2.5-coder:1.5b  # Modelo más rápido
```

Descarga el nuevo modelo:

```bash
ollama pull qwen2.5-coder:1.5b
```

## Arquitectura

```
┌─────────────────┐
│  Flask Dashboard│
│                 │
│  ┌───────────┐  │
│  │ Analytics │  │
│  │   Agent   │  │
│  └─────┬─────┘  │
└────────┼────────┘
         │ HTTP POST
         │ /api/chat
         ▼
┌─────────────────┐
│  Ollama Server  │
│  localhost:11434│
│                 │
│  ┌───────────┐  │
│  │qwen2.5-   │  │
│  │coder:3b   │  │
│  └───────────┘  │
└─────────────────┘
```

## Migración desde OpenAI

Los cambios realizados:

1. ✅ `api/openai_agent.py` - Reemplazado cliente OpenAI por requests + Ollama API
2. ✅ `config_flask.py` - Agregadas variables `OLLAMA_URL` y `OLLAMA_MODEL`
3. ✅ `.env` - Reemplazada `OPENAI_API_KEY` por configuración Ollama
4. ✅ `.env.example` - Actualizado con nuevas variables
5. ✅ `requirements.txt` - Eliminada dependencia `openai`

## Referencias

- [Ollama Docs](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Qwen2.5-Coder](https://ollama.ai/library/qwen2.5-coder)
- [Modelos disponibles](https://ollama.ai/library)
