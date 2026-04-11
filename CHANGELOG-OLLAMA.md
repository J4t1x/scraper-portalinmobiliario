# Changelog: Migración de OpenAI a Ollama

## Fecha: 2026-04-10

## Resumen

Migración completa del Agente de Analítica desde OpenAI API a Ollama local, eliminando costos de API y permitiendo ejecución 100% local.

## Cambios Realizados

### 1. Código

#### `api/openai_agent.py`
- ✅ Reemplazado cliente `openai.OpenAI` por `requests` + Ollama API
- ✅ Agregado método `_test_connection()` para verificar disponibilidad de Ollama
- ✅ Actualizado `generate_response()` para usar endpoint `/api/chat` de Ollama
- ✅ Mejorado manejo de errores con mensajes específicos para Ollama

#### `config_flask.py`
- ✅ Eliminada variable `OPENAI_API_KEY`
- ✅ Agregadas variables `OLLAMA_URL` y `OLLAMA_MODEL`

### 2. Configuración

#### `.env`
```diff
- OPENAI_API_KEY=sk-proj-...
+ # Configuración de Ollama (Agente de Analítica)
+ OLLAMA_URL=http://localhost:11434
+ OLLAMA_MODEL=qwen2.5-coder:3b
```

#### `.env.example`
- ✅ Actualizado con configuración de Ollama
- ✅ Agregados comentarios de instalación

### 3. Dependencias

#### `requirements.txt`
```diff
- # AI/Analytics
- openai>=1.12.0
+ # AI/Analytics
+ # Ollama se usa vía API REST (requiere: requests, que ya está instalado)
+ # Para instalar Ollama: https://ollama.ai/download
+ # Para ejecutar: ollama serve
+ # Para descargar modelo: ollama pull qwen2.5-coder:3b
```

### 4. Documentación

- ✅ Creado `docs/OLLAMA-INTEGRATION.md` - Guía completa de integración
- ✅ Creado `test_ollama_agent.py` - Script de pruebas
- ✅ Creado `CHANGELOG-OLLAMA.md` - Este archivo

## Modelo Seleccionado

**`qwen2.5-coder:3b`** (1.9 GB)

### Justificación

1. **Especializado en análisis** - Familia Qwen Coder optimizada para código y datos
2. **Tamaño óptimo** - 3B parámetros balancean capacidad y velocidad
3. **Rendimiento** - Superior a phi4-mini para análisis de datos
4. **Eficiencia** - Corre bien en Apple M1 con 5.3 GB VRAM

### Modelos Alternativos

- `qwen2.5-coder:1.5b` - Más rápido, menos capaz
- `phi4-mini:latest` - Alternativa general
- `ministral-3:3b` - Modelo de Mistral
- `granite4:3b` - Modelo de IBM

## Pruebas Realizadas

```bash
$ source venv/bin/activate
$ python test_ollama_agent.py

🧪 PRUEBAS DE INTEGRACIÓN OLLAMA
============================================================
✅ PASS - Conexión
✅ PASS - Consulta simple
✅ PASS - Consulta analítica

Total: 3/3 pruebas exitosas
🎉 ¡Todas las pruebas pasaron!
```

## Ventajas de la Migración

✅ **Sin costos de API** - Todo local, sin límites  
✅ **Privacidad total** - Los datos no salen de tu máquina  
✅ **Funciona offline** - No requiere conexión a internet  
✅ **Rápido** - Respuestas en ~40 segundos con M1  
✅ **Sin rate limits** - Sin restricciones de uso  

## Desventajas

⚠️ **Requiere recursos locales** - ~2 GB RAM + CPU/GPU  
⚠️ **Setup inicial** - Instalar Ollama y descargar modelo  
⚠️ **Calidad variable** - Modelos pequeños menos capaces que GPT-4  

## Instrucciones de Setup

### 1. Instalar Ollama

```bash
# macOS/Linux
curl -fsSL https://ollama.ai/install.sh | sh

# O descargar desde: https://ollama.ai/download
```

### 2. Iniciar Ollama

```bash
ollama serve
```

### 3. Descargar el modelo

```bash
ollama pull qwen2.5-coder:3b
```

### 4. Verificar instalación

```bash
ollama list
# Debe mostrar: qwen2.5-coder:3b
```

### 5. Ejecutar pruebas

```bash
cd /Users/ja/Documents/GitHub/scraper-portalinmobiliario
source venv/bin/activate
python test_ollama_agent.py
```

### 6. Iniciar dashboard

```bash
python app.py
# El agente de analítica ahora usa Ollama
```

## Compatibilidad

- ✅ macOS (Apple Silicon y Intel)
- ✅ Linux
- ✅ Windows (WSL2 recomendado)

## Rollback (si es necesario)

Si necesitas volver a OpenAI:

1. Restaurar `api/openai_agent.py` desde git
2. Restaurar `config_flask.py` desde git
3. Agregar `OPENAI_API_KEY` al `.env`
4. Instalar: `pip install openai>=1.12.0`

```bash
git checkout HEAD -- api/openai_agent.py config_flask.py
echo "OPENAI_API_KEY=tu-api-key" >> .env
pip install openai>=1.12.0
```

## Próximos Pasos

- [ ] Evaluar otros modelos (phi4-mini, ministral-3)
- [ ] Optimizar prompts para modelos locales
- [ ] Agregar caché de respuestas
- [ ] Implementar streaming de respuestas
- [ ] Agregar métricas de rendimiento

## Referencias

- [Ollama Docs](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Qwen2.5-Coder](https://ollama.ai/library/qwen2.5-coder)
- [Modelos disponibles](https://ollama.ai/library)

## Autor

- **Fecha**: 2026-04-10
- **Versión**: 1.0.0
- **Status**: ✅ Completado y probado
