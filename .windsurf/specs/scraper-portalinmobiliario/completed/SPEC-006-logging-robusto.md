# SPEC-006: Sistema de Logging Robusto

**Proyecto:** scraper-portalinmobiliario  
**Fase:** 2 - Mejoras (Sprint 3: Infraestructura)  
**Prioridad:** Media  
**Estimación:** 4 horas  
**Status:** completed  
**Creado:** 2026-04-09  
**Actualizado:** 2026-04-09

---

## 1. Contexto

### Problema
El logging actual usa prints básicos, sin estructura ni rotación:
- Archivos de log crecen indefinidamente
- No hay formato estandarizado
- Difícil analizar logs en producción
- No separación por tipo de operación

### Solución
Implementar logging estructurado JSON con rotación automática.

### Objetivo
100% de operaciones loggeadas con formato estructurado y rotación.

---

## 2. Requirements

### Functional Requirements (FR)

**FR-001:** Formato JSON estructurado para todos los logs
**FR-002:** Rotación diaria con compresión gzip
**FR-003:** Retención de logs por 30 días
**FR-004:** Niveles: DEBUG, INFO, WARNING, ERROR, CRITICAL
**FR-005:** Logs separados: scraping.log, errors.log, performance.log
**FR-006:** Contexto en cada log: timestamp, nivel, módulo, mensaje, metadata
**FR-007:** Logging no bloquea operaciones del scraper

### Non-Functional Requirements (NFR)

**NFR-001:** Logs nunca deben causar falla del scraper
**NFR-002:** Rotación automática sin intervención manual
**NFR-003:** Formato parseable por herramientas de análisis
**NFR-004:** Compatibilidad con monitoreo (preparado para dashboard)

---

## 3. Acceptance Criteria

- [x] Configuración de logging con `logging.handlers.TimedRotatingFileHandler`
- [x] Formato JSON con timestamp ISO8601
- [x] Rotación diaria + compresión gzip
- [x] 3 archivos de log separados (scraping, errors, performance)
- [x] Retención automática de 30 días
- [x] Niveles de log configurables via env var
- [x] Integración en todos los módulos
- [x] Tests de logging
- [x] Documentación de estructura de logs

---

## 4. Technical Design

### Architecture
```
┌─────────────────┐
│  Application    │
│    Code         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│  JSONFormatter  │────▶│ TimedRotating   │
│                 │     │ FileHandler     │
└─────────────────┘     └────────┬────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ logs/scraping/  │    │ logs/errors/    │    │ logs/perf/      │
│   .json.{date}  │    │  .json.{date}   │    │ .json.{date}    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Log Schema

**Formato JSON:**
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

### API/Interface

```python
# logger_config.py
class LoggerConfig:
    def setup_logging(log_level: str = "INFO", log_dir: str = "logs")
    def get_logger(name: str) -> logging.Logger
    def rotate_logs()
    def clean_old_logs(days: int = 30)

# Uso en módulos
from logger_config import get_logger

logger = get_logger(__name__)
logger.info("Message", extra={"context": {...}})
```

---

## 5. Implementation Plan

### TASK-006-01: Configurar handlers (60min)
- Crear `logger_config.py`
- Configurar `TimedRotatingFileHandler`
- Implementar `JSONFormatter` custom
- Setup de directorios de logs
- Configurar compresión gzip

### TASK-006-02: Formato JSON (45min)
- Crear formatter que serialice a JSON
- Incluir timestamp ISO8601
- Incluir contexto extra
- Manejar excepciones en serialización

### TASK-006-03: Logs separados (45min)
- `logs/scraping/` - Operaciones normales
- `logs/errors/` - Errores y excepciones
- `logs/performance/` - Métricas de tiempo
- Filtros por nivel y tipo

### TASK-006-04: Integración en módulos (60min)
- Reemplazar prints en `scraper_selenium.py`
- Reemplazar prints en `scraper.py`
- Reemplazar prints en `exporter.py`
- Agregar logging en `main.py`
- Contexto en cada operación importante

### TASK-006-05: Tests de logging (30min)
- Tests de formato JSON
- Tests de rotación
- Tests de retención
- Tests de que no falla el scraper

### TASK-006-06: Documentación (30min)
- Estructura de logs documentada
- Guía de troubleshooting
- Ejemplos de análisis de logs

---

## 6. Testing Strategy

### Test Cases

**TC-001:** Log JSON tiene todos los campos requeridos
**TC-002:** Rotación crea archivo nuevo cada día
**TC-003:** Archivos antiguos se comprimen en gzip
**TC-004:** Logs >30 días se eliminan automáticamente
**TC-005:** Error en logging no detiene scraper
**TC-006:** Nivel DEBUG no loggea en producción
**TC-007:** Contexto extra aparece en JSON

### Integration Tests
- Ejecutar scraper completo y verificar logs
- Simular rotación forzada
- Verificar formato parseable

---

## 7. Notes

### Decisions
- Usar `TimedRotatingFileHandler` en lugar de `RotatingFileHandler` (por tiempo no tamaño)
- Compresión gzip para ahorrar espacio (logs de scraping pueden ser grandes)
- 3 archivos separados para facilitar análisis
- Nivel de log configurable via `LOG_LEVEL` env var

### Dependencies
- Python standard library `logging`
- `logging.handlers` para rotación
- `gzip` para compresión
- `python-json-logger==2.0.7` para formato JSON

### Environment Variables
- `LOG_LEVEL`: DEBUG|INFO|WARNING|ERROR|CRITICAL (default: INFO)
- `LOG_DIR`: Directorio de logs (default: logs/)
- `LOG_RETENTION_DAYS`: Días de retención (default: 30)

### Implementation Summary
**TASK-006-01:** ✅ Configurar handlers - Creado `logger_config.py` con `TimedRotatingFileHandler`, `JSONFormatter` custom y compresión gzip

**TASK-006-02:** ✅ Formato JSON - Implementado `CustomJSONFormatter` con todos los campos requeridos (timestamp, level, logger, module, function, line, message, context, thread, process)

**TASK-006-03:** ✅ Logs separados - Configurados 3 handlers: `logs/scraping/`, `logs/errors/`, `logs/performance/`

**TASK-006-04:** ✅ Integración en módulos - Actualizados: `main.py`, `scraper_selenium.py`, `scraper.py`, `exporter.py`, `validator.py`, `deduplicator.py`, `utils.py`

**TASK-006-05:** ✅ Tests de logging - Creado `tests/test_logging.py` con 9 tests cubriendo todos los TC

**Archivos creados/modificados:**
- `/Users/ja/Documents/GitHub/scraper-portalinmobiliario/logger_config.py` (nuevo)
- `/Users/ja/Documents/GitHub/scraper-portalinmobiliario/tests/test_logging.py` (nuevo)
- `/Users/ja/Documents/GitHub/scraper-portalinmobiliario/requirements.txt` (agregado python-json-logger)
- `/Users/ja/Documents/GitHub/scraper-portalinmobiliario/.env.example` (agregadas vars de logging)
- `/Users/ja/Documents/GitHub/scraper-portalinmobiliario/main.py` (actualizado)
- `/Users/ja/Documents/GitHub/scraper-portalinmobiliario/scraper_selenium.py` (actualizado)
- `/Users/ja/Documents/GitHub/scraper-portalinmobiliario/scraper.py` (actualizado)
- `/Users/ja/Documents/GitHub/scraper-portalinmobiliario/exporter.py` (actualizado)
- `/Users/ja/Documents/GitHub/scraper-portalinmobiliario/validator.py` (actualizado)
- `/Users/ja/Documents/GitHub/scraper-portalinmobiliario/deduplicator.py` (actualizado)
- `/Users/ja/Documents/GitHub/scraper-portalinmobiliario/utils.py` (actualizado)

---

## 8. Changelog

| Fecha | Autor | Cambio |
|-------|-------|--------|
| 2026-04-09 | Cascade | Spec creada desde PRD Fase 2 |
