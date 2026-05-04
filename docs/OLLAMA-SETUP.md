# Ollama - Configuración y Uso

## Estado del Servicio

✅ **Ollama está operativo y healthy**

- **URL**: http://localhost:4423
- **Modelo instalado**: `qwen2.5-coder:1.5b` (986 MB)
- **API Endpoint**: http://localhost:4423/api/generate

## Información del Modelo

```bash
# Listar modelos instalados
docker exec portalinmobiliario-ollama ollama list

# Output:
# NAME                  ID              SIZE      MODIFIED       
# qwen2.5-coder:1.5b    d7372fd82851    986 MB    XX minutes ago
```

## Uso del API

### Generar Texto

```bash
curl http://localhost:4423/api/generate -d '{
  "model": "qwen2.5-coder:1.5b",
  "prompt": "Write a Python function to calculate fibonacci",
  "stream": false
}'
```

### Desde Python

```python
import requests

def generate_code(prompt):
    response = requests.post('http://localhost:4423/api/generate', json={
        'model': 'qwen2.5-coder:1.5b',
        'prompt': prompt,
        'stream': False
    })
    return response.json()['response']

# Ejemplo
code = generate_code("Write a Python function to sort a list")
print(code)
```

### Desde el Dashboard

El dashboard del proyecto ya está configurado para usar Ollama:
- **URL configurada**: `http://ollama:11434/api/generate` (dentro de Docker)
- **Modelo**: `qwen2.5-coder:1.5b`

## Comandos Docker

```bash
# Iniciar Ollama
docker-compose -f docker-compose.v2.yml --profile ai up -d ollama

# Detener Ollama
docker-compose -f docker-compose.v2.yml --profile ai stop ollama

# Ver logs
docker logs portalinmobiliario-ollama

# Ejecutar comando ollama
docker exec portalinmobiliario-ollama ollama list

# Verificar health
docker inspect portalinmobiliario-ollama --format='{{.State.Health.Status}}'
```

## Gestión de Modelos

### Instalar un nuevo modelo

```bash
# Modelos recomendados para código
docker exec portalinmobiliario-ollama ollama pull codellama:7b
docker exec portalinmobiliario-ollama ollama pull deepseek-coder:6.7b
docker exec portalinmobiliario-ollama ollama pull qwen2.5-coder:3b

# Modelos generales pequeños
docker exec portalinmobiliario-ollama ollama pull llama3.2:3b
docker exec portalinmobiliario-ollama ollama pull phi3:mini
```

### Eliminar un modelo

```bash
docker exec portalinmobiliario-ollama ollama rm qwen2.5-coder:1.5b
```

### Ver modelos disponibles

Visita: https://ollama.com/library

## Recursos del Contenedor

- **RAM Limit**: 2 GB
- **RAM Reservation**: 1 GB
- **CPUs**: 2
- **Volumen**: `ollama-models` (persiste los modelos descargados)

## Healthcheck

El contenedor usa el siguiente healthcheck:
```yaml
test: ["CMD", "ollama", "list"]
interval: 30s
timeout: 10s
retries: 3
start_period: 30s
```

## Integración con Dashboard

✅ **El dashboard está completamente integrado con Ollama**

El dashboard Flask usa Ollama para:
- Análisis de propiedades con IA
- Generación de descripciones
- Clasificación automática
- Detección de oportunidades

### Configuración

La configuración está en `config_flask.py`:
```python
OLLAMA_URL = "http://ollama:11434"
OLLAMA_MODEL = "qwen2.5-coder:1.5b"
```

**Variables de entorno en Docker**:
```yaml
environment:
  - OLLAMA_URL=http://ollama:11434
```

### Dependencias

El dashboard depende de Ollama para funcionar correctamente:
```yaml
depends_on:
  ollama:
    condition: service_healthy
```

Cuando levantas el dashboard con `--profile dashboard`, Ollama se inicia automáticamente.

## Troubleshooting

### Contenedor unhealthy
```bash
# Verificar logs
docker logs portalinmobiliario-ollama --tail 50

# Verificar que el servicio responde
curl http://localhost:4423/api/tags

# Recrear contenedor
docker-compose -f docker-compose.v2.yml --profile ai up -d --force-recreate ollama
```

### Modelo no responde
```bash
# Verificar que el modelo existe
docker exec portalinmobiliario-ollama ollama list

# Probar generación simple
curl http://localhost:4423/api/generate -d '{"model":"qwen2.5-coder:1.5b","prompt":"test","stream":false}'
```

### Memoria insuficiente
Si el modelo es muy grande, ajusta los límites en `docker-compose.v2.yml`:
```yaml
mem_limit: 4g
mem_reservation: 2g
```

## Puertos del Proyecto

| Servicio   | Puerto | Estado  |
|------------|--------|---------|
| PostgreSQL | 4420   | ✅ Healthy |
| Dashboard  | 4421   | ✅ Healthy |
| Redis      | 4422   | (profile cache) |
| **Ollama** | **4423** | **✅ Healthy** |
| Adminer    | 4424   | (profile admin) |
| pgAdmin    | 4425   | ✅ Running |
