# Migración Dashboard a PostgreSQL

**Fecha:** 12 Abril 2026  
**Versión:** 2.1.0  
**Estado:** ✅ Completado

## 📋 Resumen

Migración completa del dashboard de archivos JSON a PostgreSQL como fuente de datos principal, con sistema de tracking de ejecuciones del scraper y persistencia de logs.

## 🎯 Objetivos Completados

- ✅ Dashboard consume datos desde PostgreSQL en lugar de archivos JSON
- ✅ Historial completo de ejecuciones del scraper almacenado en BD
- ✅ Logs de scraper persistidos en BD con SocketIO para visualización en tiempo real
- ✅ Los JSON se siguen generando pero no se usan en el dashboard
- ✅ Logs de terminal persisten al cambiar de ventana

## 🏗️ Arquitectura

### **Nuevos Modelos**

#### 1. `ScraperExecution` (`models/scraper_execution.py`)
Tracking de ejecuciones del scraper:
- `execution_id`: UUID único
- `operacion`, `tipo`: Parámetros del scraping
- `start_time`, `end_time`, `duration`: Tiempos
- `status`: running, completed, failed, cancelled
- `properties_scraped`, `properties_new`, `properties_updated`: Métricas
- `pages_processed`: Páginas procesadas
- `parameters`: JSON con parámetros adicionales
- `triggered_by`: manual, scheduled, api
- `user_id`: Usuario que ejecutó

#### 2. `ScraperLog` (`models/scraper_execution.py`)
Logs individuales de cada ejecución:
- `execution_id`: FK a ScraperExecution
- `timestamp`: Timestamp del log
- `level`: DEBUG, INFO, WARNING, ERROR, CRITICAL
- `message`: Mensaje del log
- `source`: Origen (scraper, validator, exporter, etc.)
- `metadata`: JSON con metadata adicional

### **Nuevos Módulos**

#### 1. `db_loader.py`
Reemplazo de `JSONDataLoader` para consultas a PostgreSQL:
- `get_properties()`: Propiedades con filtros y paginación
- `get_property_by_id()`: Detalle de propiedad
- `get_stats()`: Estadísticas de propiedades
- `get_filter_options()`: Opciones de filtros disponibles
- `get_scraper_executions()`: Historial de ejecuciones
- `get_execution_by_id()`: Detalle de ejecución con logs
- `get_execution_logs()`: Logs de una ejecución

#### 2. `execution_tracker.py`
Gestión del ciclo de vida de ejecuciones:
- `ExecutionTracker`: Clase para tracking
- `start_execution()`: Iniciar ejecución
- `update_metrics()`: Actualizar métricas
- `complete_execution()`: Completar ejecución
- `log()`, `log_info()`, `log_warning()`, `log_error()`: Logging
- `track_execution()`: Context manager

## 🔄 Cambios en Archivos Existentes

### **dashboard/routes.py**
- ✅ Importa `DatabaseLoader` y `ExecutionTracker`
- ✅ `/data` usa `db_loader.get_stats()`
- ✅ `/property/<int:property_id>` usa `db_loader.get_property_by_id()`
- ✅ `/api/properties` consulta PostgreSQL con filtros
- ✅ `/api/properties/<int:property_id>` desde PostgreSQL
- ✅ `/api/stats` desde PostgreSQL
- ✅ `/api/filters` desde PostgreSQL
- ✅ `/api/scraper/run` usa `ExecutionTracker` y persiste logs
- ✅ **Nuevos endpoints:**
  - `GET /api/scraper/executions` - Historial de ejecuciones
  - `GET /api/scraper/executions/<execution_id>` - Detalle de ejecución
  - `GET /api/scraper/executions/<execution_id>/logs` - Logs de ejecución

### **main.py**
- ✅ Nuevo parámetro `--execution-id`
- ✅ Inicializa `ExecutionTracker` si se proporciona execution_id
- ✅ Actualiza métricas durante el scraping
- ✅ Completa ejecución con status correcto
- ✅ Maneja interrupciones y errores

### **models/__init__.py**
- ✅ Exporta `ScraperExecutionModel` y `ScraperLog`

## 🗄️ Migración de Base de Datos

### **Archivo:** `migrations/versions/20260412_1930_004_add_scraper_executions.py`

**Tablas creadas:**
1. `scraper_executions` - Ejecuciones del scraper
2. `scraper_logs` - Logs de ejecuciones

**Índices creados:**
- `scraper_executions`: execution_id (unique), operacion, tipo, start_time, status
- `scraper_logs`: execution_id, timestamp, level

**Ejecutar migración:**
```bash
# Dentro del contenedor o con DATABASE_URL configurado
alembic upgrade head
```

## 📡 API Endpoints

### **Propiedades (PostgreSQL)**

#### `GET /api/properties`
Lista propiedades desde PostgreSQL con filtros y paginación.

**Query params:**
- `operacion`: venta, arriendo, etc.
- `tipo`: departamento, casa, etc.
- `comuna`: Nombre de comuna
- `precio_min`, `precio_max`: Rango de precio (entero)
- `search`: Búsqueda en título/dirección
- `page`: Número de página (default: 1)
- `per_page`: Items por página (default: 20)

**Response:**
```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 150,
    "pages": 8
  }
}
```

#### `GET /api/properties/<int:property_id>`
Detalle de propiedad desde PostgreSQL.

#### `GET /api/stats`
Estadísticas de propiedades desde PostgreSQL.

#### `GET /api/filters`
Opciones de filtros disponibles (operaciones, tipos, comunas).

### **Ejecuciones del Scraper**

#### `GET /api/scraper/executions`
Historial de ejecuciones del scraper.

**Query params:**
- `status`: running, completed, failed, cancelled
- `operacion`: venta, arriendo, etc.
- `tipo`: departamento, casa, etc.
- `page`, `per_page`: Paginación

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "execution_id": "uuid-here",
      "operacion": "venta",
      "tipo": "departamento",
      "start_time": "2026-04-12T19:30:00",
      "end_time": "2026-04-12T19:45:00",
      "duration": 900,
      "status": "completed",
      "properties_scraped": 150,
      "properties_new": 10,
      "properties_updated": 140,
      "pages_processed": 5,
      "triggered_by": "manual",
      "user_id": "admin"
    }
  ],
  "pagination": {...}
}
```

#### `GET /api/scraper/executions/<execution_id>`
Detalle de una ejecución con todos sus logs.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "execution_id": "uuid-here",
    ...,
    "logs": [
      {
        "id": 1,
        "timestamp": "2026-04-12T19:30:01",
        "level": "INFO",
        "message": "Iniciando scraping...",
        "source": "scraper"
      },
      ...
    ]
  }
}
```

#### `GET /api/scraper/executions/<execution_id>/logs`
Logs de una ejecución específica con paginación.

**Query params:**
- `level`: DEBUG, INFO, WARNING, ERROR, CRITICAL
- `page`, `per_page`: Paginación

#### `POST /api/scraper/run`
Ejecutar scraping manual con tracking.

**Request body:**
```json
{
  "operacion": "venta",
  "tipo": "departamento",
  "max_pages": 10,
  "formato": "json",
  "scrape_details": true,
  "verbose": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Scraping manual iniciado...",
  "data": {
    "execution_id": "uuid-here",
    "operacion": "venta",
    "tipo": "departamento",
    ...
  }
}
```

## 🔌 SocketIO Events

### **Emitidos por el servidor:**

#### `scraping_log`
Log en tiempo real durante el scraping.
```json
{
  "execution_id": "uuid-here",
  "log": "Procesando página 1...",
  "timestamp": "2026-04-12T19:30:01"
}
```

#### `scraping_complete`
Scraping completado.
```json
{
  "execution_id": "uuid-here",
  "return_code": 0,
  "timestamp": "2026-04-12T19:45:00"
}
```

#### `scraping_error`
Error durante el scraping.
```json
{
  "execution_id": "uuid-here",
  "error": "Error message",
  "timestamp": "2026-04-12T19:35:00"
}
```

## 🚀 Uso

### **1. Ejecutar migración**
```bash
docker-compose -f docker-compose.v2.yml run --rm scraper alembic upgrade head
```

### **2. Levantar dashboard**
```bash
docker-compose -f docker-compose.v2.yml --profile dashboard up
```

### **3. Ejecutar scraping con tracking**
```bash
# Manual (desde dashboard UI)
# O desde línea de comandos:
docker-compose -f docker-compose.v2.yml run --rm scraper \
  python main.py \
  --operacion venta \
  --tipo departamento \
  --max-pages 5 \
  --persist-to-db
```

### **4. Ver historial de ejecuciones**
- Dashboard: `/scraper` (pendiente implementar UI)
- API: `GET /api/scraper/executions`

### **5. Ver logs de una ejecución**
- API: `GET /api/scraper/executions/<execution_id>`
- Los logs persisten en BD, no se pierden al cambiar de ventana

## 📊 Flujo de Datos

```
┌─────────────────┐
│  Scraper Run    │
│  (manual/API)   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│  ExecutionTracker       │
│  - Crea registro en BD  │
│  - execution_id: UUID   │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  main.py                │
│  - Recibe execution_id  │
│  - Ejecuta scraping     │
│  - Actualiza métricas   │
└────────┬────────────────┘
         │
         ├─────────────────────┐
         │                     │
         ▼                     ▼
┌─────────────────┐   ┌──────────────────┐
│  PostgreSQL     │   │  SocketIO        │
│  - Properties   │   │  - Real-time     │
│  - Executions   │   │  - scraping_log  │
│  - Logs         │   │  - scraping_*    │
└─────────────────┘   └──────────────────┘
         │                     │
         ▼                     ▼
┌─────────────────────────────────┐
│  Dashboard                      │
│  - Consume PostgreSQL           │
│  - Muestra logs en tiempo real  │
│  - Historial de ejecuciones     │
└─────────────────────────────────┘
```

## 🔍 Diferencias con Versión Anterior

| Aspecto | Antes (JSON) | Ahora (PostgreSQL) |
|---------|--------------|-------------------|
| **Fuente de datos** | Archivos JSON | PostgreSQL |
| **Filtros** | En memoria (Python) | SQL queries |
| **Paginación** | En memoria | SQL LIMIT/OFFSET |
| **Estadísticas** | Calculadas on-demand | SQL aggregations |
| **Tracking** | No existe | Tabla scraper_executions |
| **Logs** | Solo en terminal | BD + SocketIO |
| **Persistencia logs** | Se pierden al cerrar | Persisten en BD |
| **Historial** | No existe | Completo en BD |

## ⚠️ Notas Importantes

1. **Los JSON se siguen generando** para compatibilidad y backup, pero el dashboard NO los usa
2. **Logs persisten en BD** - No se pierden al cambiar de ventana o cerrar terminal
3. **SocketIO sigue funcionando** para logs en tiempo real, pero ahora también se guardan en BD
4. **Backward compatible** - `JSONDataLoader` sigue existiendo pero no se usa en dashboard
5. **Migración automática** - Alembic maneja la creación de tablas

## 🐛 Troubleshooting

### **Error: "Table scraper_executions does not exist"**
```bash
# Ejecutar migración
docker-compose -f docker-compose.v2.yml run --rm scraper alembic upgrade head
```

### **No se ven logs en tiempo real**
- Verificar que SocketIO esté conectado
- Los logs se guardan en BD de todas formas

### **Ejecuciones no aparecen en historial**
- Verificar que se esté pasando `--execution-id` al scraper
- Desde dashboard siempre se pasa automáticamente

## 📝 TODO / Mejoras Futuras

- [ ] UI para visualizar historial de ejecuciones en dashboard
- [ ] Gráficos de métricas por ejecución
- [ ] Filtros avanzados en historial
- [ ] Exportar logs de ejecución
- [ ] Notificaciones cuando scraping completa
- [ ] Retry automático de ejecuciones fallidas
- [ ] Limpieza automática de logs antiguos

## 📚 Referencias

- **Modelos:** `models/scraper_execution.py`
- **Loader:** `db_loader.py`
- **Tracker:** `execution_tracker.py`
- **Migración:** `migrations/versions/20260412_1930_004_add_scraper_executions.py`
- **Routes:** `dashboard/routes.py`
- **Main:** `main.py`
