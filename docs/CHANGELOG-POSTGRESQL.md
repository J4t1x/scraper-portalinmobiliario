# Changelog - Migración PostgreSQL

## [2.1.0] - 2026-04-12

### 🎯 Migración Dashboard a PostgreSQL

**Objetivo:** Migrar el dashboard de archivos JSON a PostgreSQL como fuente de datos principal, con sistema completo de tracking de ejecuciones del scraper.

### ✅ Agregado

#### **Nuevos Modelos**
- `ScraperExecution` - Tracking de ejecuciones del scraper
  - Métricas: properties_scraped, properties_new, properties_updated, pages_processed
  - Estados: running, completed, failed, cancelled
  - Metadata: triggered_by, user_id, parameters
- `ScraperLog` - Logs individuales de cada ejecución
  - Niveles: DEBUG, INFO, WARNING, ERROR, CRITICAL
  - Persistencia completa en BD

#### **Nuevos Módulos**
- `db_loader.py` - Loader para consultas a PostgreSQL
  - Reemplaza `JSONDataLoader` en el dashboard
  - Métodos: get_properties, get_stats, get_scraper_executions, etc.
- `execution_tracker.py` - Gestión de ejecuciones
  - Context manager `track_execution()`
  - Métodos: start_execution, update_metrics, complete_execution, log

#### **Nuevos Endpoints API**
- `GET /api/scraper/executions` - Historial de ejecuciones
- `GET /api/scraper/executions/<execution_id>` - Detalle de ejecución
- `GET /api/scraper/executions/<execution_id>/logs` - Logs de ejecución

#### **Nuevos Scripts**
- `scripts/migrate_to_postgresql.sh` - Script de migración automatizada

#### **Documentación**
- `docs/MIGRACION-POSTGRESQL.md` - Documentación completa de la migración
- `CHANGELOG-POSTGRESQL.md` - Este archivo

### 🔄 Modificado

#### **dashboard/routes.py**
- `/data` - Usa `DatabaseLoader` en lugar de `JSONDataLoader`
- `/property/<int:property_id>` - Consulta PostgreSQL
- `/api/properties` - Filtros y paginación desde PostgreSQL
- `/api/properties/<int:property_id>` - Detalle desde PostgreSQL
- `/api/stats` - Estadísticas desde PostgreSQL
- `/api/filters` - Opciones de filtros desde PostgreSQL
- `/api/scraper/run` - Usa `ExecutionTracker` y persiste logs en BD

#### **main.py**
- Nuevo parámetro `--execution-id`
- Integración con `ExecutionTracker`
- Actualización de métricas durante scraping
- Manejo de estados (completed, failed, cancelled)

#### **models/__init__.py**
- Exporta `ScraperExecutionModel` y `ScraperLog`

### 🗄️ Migración de Base de Datos

**Archivo:** `migrations/versions/20260412_1930_004_add_scraper_executions.py`

**Tablas creadas:**
- `scraper_executions` (11 columnas + índices)
- `scraper_logs` (6 columnas + índices)

**Índices:**
- `scraper_executions`: execution_id (unique), operacion, tipo, start_time, status
- `scraper_logs`: execution_id, timestamp, level

### 🔌 SocketIO

**Eventos actualizados:**
- `scraping_log` - Ahora incluye `execution_id` en lugar de `scraping_id`
- `scraping_complete` - Incluye `execution_id`
- `scraping_error` - Incluye `execution_id`

**Persistencia:**
- Los logs emitidos por SocketIO también se guardan en BD
- Los logs persisten al cambiar de ventana o cerrar terminal

### 📊 Flujo de Datos

**Antes:**
```
Scraper → JSON files → JSONDataLoader → Dashboard
```

**Ahora:**
```
Scraper → PostgreSQL → DatabaseLoader → Dashboard
         ↓
    ExecutionTracker → scraper_executions + scraper_logs
         ↓
    SocketIO (real-time) + BD (persistencia)
```

### 🎨 Características

1. **Dashboard consume PostgreSQL**
   - Todas las consultas de propiedades desde BD
   - Filtros y paginación optimizados con SQL
   - Estadísticas calculadas con agregaciones SQL

2. **Tracking completo de ejecuciones**
   - Cada scraping genera un registro en `scraper_executions`
   - Métricas detalladas: propiedades nuevas, actualizadas, páginas procesadas
   - Estados: running, completed, failed, cancelled

3. **Logs persistidos**
   - Todos los logs del scraper se guardan en `scraper_logs`
   - Niveles: DEBUG, INFO, WARNING, ERROR, CRITICAL
   - No se pierden al cambiar de ventana

4. **Real-time + Persistencia**
   - SocketIO para visualización en tiempo real
   - BD para persistencia y consulta histórica
   - Mejor de ambos mundos

5. **Backward compatible**
   - Los JSON se siguen generando (backup)
   - `JSONDataLoader` sigue existiendo pero no se usa
   - Migración transparente

### ⚠️ Breaking Changes

**Ninguno** - La migración es backward compatible.

### 🐛 Fixes

- Los logs ya no se pierden al cambiar de ventana
- Historial completo de ejecuciones disponible
- Métricas precisas de cada scraping

### 📝 Notas

1. **Los JSON se siguen generando** para compatibilidad y backup
2. **Ejecutar migración:** `./scripts/migrate_to_postgresql.sh`
3. **Ver documentación completa:** `docs/MIGRACION-POSTGRESQL.md`

### 🚀 Cómo usar

```bash
# 1. Ejecutar migración
./scripts/migrate_to_postgresql.sh

# 2. Levantar dashboard
docker-compose -f docker-compose.v2.yml --profile dashboard up

# 3. Ejecutar scraping con tracking
docker-compose -f docker-compose.v2.yml run --rm scraper \
  python main.py --operacion venta --tipo departamento \
  --max-pages 5 --persist-to-db

# 4. Ver historial
curl http://localhost:4421/api/scraper/executions
```

### 📚 Referencias

- [Documentación completa](docs/MIGRACION-POSTGRESQL.md)
- [Modelos](models/scraper_execution.py)
- [Loader](db_loader.py)
- [Tracker](execution_tracker.py)
- [Migración](migrations/versions/20260412_1930_004_add_scraper_executions.py)

---

## [2.0.0] - 2026-04-09

### MVP Analytics Completado
- Analítica con pandas
- Detección de oportunidades
- Agente IA con Ollama
- Contenedor único MVP

Ver [CHANGELOG-OLLAMA.md](CHANGELOG-OLLAMA.md) para detalles.
