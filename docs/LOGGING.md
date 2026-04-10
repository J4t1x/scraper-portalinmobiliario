# Sistema de Logging - Portal Inmobiliario Scraper

Sistema de logging estructurado JSON con rotación automática y compresión.

---

## Características

- **Formato JSON estructurado** para análisis automatizado
- **Rotación diaria automática** con compresión gzip
- **3 archivos separados:** scraping, errors, performance
- **Retención automática** de 30 días (configurable)
- **Niveles configurables** via variables de entorno
- **No bloquea** operaciones del scraper (fail-safe)

---

## Estructura de Logs

```
logs/
├── scraping/
│   ├── scraping.json              # Log actual
│   ├── scraping.json.2026-04-08   # Rotado (comprimido)
│   └── scraping.json.2026-04-09.gz  # Comprimido
├── errors/
│   ├── errors.json
│   └── errors.json.2026-04-09.gz
└── performance/
    ├── performance.json
    └── performance.json.2026-04-09.gz
```

---

## Formato JSON

```json
{
  "timestamp": "2026-04-09T10:30:00.123Z",
  "level": "INFO",
  "logger": "scraper.selenium",
  "module": "scraper_selenium",
  "function": "scrape_property_detail",
  "line": 150,
  "message": "Scraped property detail",
  "context": {
    "property_id": "MLC-12345678",
    "url": "https://www.portalinmobiliario.com/...",
    "execution_time_ms": 1250
  },
  "thread": "MainThread",
  "process": 12345
}
```

---

## Uso

### Logger Básico

```python
from logger_config import get_logger

logger = get_logger(__name__)
logger.info("Mensaje informativo")
logger.error("Mensaje de error", exc_info=True)
```

### Con Contexto

```python
logger.info(
    "Propiedad scrapeada",
    extra={
        "context": {
            "property_id": "MLC-12345678",
            "url": "https://...",
            "precio": "UF 5.500"
        }
    }
)
```

### Performance Logging

```python
from logger_config import log_performance

log_performance(
    operation="scrape_property_detail",
    duration_ms=1250.5,
    context={"property_id": "MLC-12345678"}
)
```

---

## Configuración

### Variables de Entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `LOG_LEVEL` | INFO | Nivel mínimo (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `LOG_DIR` | logs/ | Directorio de logs |
| `LOG_RETENTION_DAYS` | 30 | Días de retención |

### Ejemplo .env

```bash
LOG_LEVEL=INFO
LOG_DIR=logs
LOG_RETENTION_DAYS=30
```

---

## Niveles de Log

| Nivel | Archivo | Uso |
|-------|---------|-----|
| DEBUG | scraping | Desarrollo y debugging |
| INFO | scraping | Operaciones normales |
| WARNING | scraping | Advertencias |
| ERROR | errors | Errores y excepciones |
| CRITICAL | errors | Errores críticos |

---

## Análisis de Logs

### Ver logs en tiempo real

```bash
tail -f logs/scraping/scraping.json | jq .
```

### Buscar errores

```bash
cat logs/errors/errors.json | jq 'select(.level == "ERROR")'
```

### Estadísticas de performance

```bash
cat logs/performance/performance.json | jq '.context.duration_ms'
```

### Filtrar por módulo

```bash
cat logs/scraping/scraping.json | jq 'select(.module == "scraper_selenium")'
```

---

## Troubleshooting

### Los logs no aparecen

1. Verificar permisos del directorio `logs/`
2. Verificar `LOG_LEVEL` no sea más alto que los mensajes
3. Revisar que se llamó `setup_logging()` en `main.py`

### Archivos muy grandes

- La rotación es diaria automática
- Los archivos se comprimen en gzip
- Los archivos >30 días se eliminan automáticamente

### Formato no es JSON

- Verificar que el handler está configurado
- Revisar que no hay prints en lugar de logs

---

## Tests

Ejecutar tests del sistema de logging:

```bash
python tests/test_logging.py
```

Cobertura:
- ✅ Formato JSON con todos los campos
- ✅ Contexto extra en logs
- ✅ Niveles de log
- ✅ Separación de archivos
- ✅ Rotación automática
- ✅ Retención de logs
- ✅ Performance logging
- ✅ Seguridad (no falla el scraper)

---

## Dependencias

```
python-json-logger==2.0.7
```

Parte de Python standard library:
- `logging`
- `logging.handlers`
- `gzip`

---

*Documentación generada automáticamente - SPEC-006*
