# Módulo de Control del Scraper

**URL:** http://localhost:4421/scraper

## Descripción

Panel de control completo para gestionar el scraper de Portal Inmobiliario con visualización en tiempo real de ejecuciones, jobs programados y sincronización automática de datos.

---

## Características Principales

### 1. Estado del Scheduler
- **Estado en tiempo real:** Running, Paused, Stopped
- **Métricas:**
  - Jobs configurados
  - Total de ejecuciones
  - Último heartbeat
- **Controles:**
  - Iniciar/Detener scheduler
  - Pausar/Reanudar
  - Actualizar estado

### 2. Ejecuciones Activas
- **Monitoreo en vivo** de scrapers en ejecución
- **Métricas por ejecución:**
  - Operación y tipo de propiedad
  - Hora de inicio
  - Propiedades scrapeadas
  - Páginas procesadas
- **Barra de progreso animada**
- **Auto-refresh cada 10 segundos**

### 3. Jobs Predefinidos
- **Catálogo de configuraciones** listas para usar
- **Información por job:**
  - Nombre descriptivo
  - Operación y tipo
  - Descripción del schedule
  - Páginas a scrapear
  - Si incluye detalles
- **Activación con un click**
- **Indicador de estado** (Activo/Inactivo)

**Jobs predefinidos disponibles:**
- `venta_departamento_daily` - Venta de departamentos (diario 02:00)
- `arriendo_departamento_daily` - Arriendo de departamentos (diario 03:00)
- `venta_casa_daily` - Venta de casas (diario 04:00)
- `arriendo_casa_daily` - Arriendo de casas (diario 05:00)
- `venta_oficina_weekly` - Venta de oficinas (lunes 06:00)
- Y más...

### 4. Ejecución Manual
- **Configuración personalizada:**
  - Operación (venta, arriendo, arriendo-temporada)
  - Tipo de propiedad (departamento, casa, oficina, etc.)
  - Páginas máximas
  - Formato de exportación (TXT, JSON, CSV)
  - Scrapear detalles (opcional)
  - Modo verbose
- **Logs en tiempo real** vía WebSocket
- **Seguimiento de progreso**

### 5. Jobs Activos en Scheduler
- **Listado completo** de jobs programados
- **Información detallada:**
  - ID único
  - Nombre y metadata
  - Tipo de trigger (cron, interval)
  - Próxima ejecución
  - Tiempo restante
- **Controles por job:**
  - Pausar
  - Reanudar
  - Eliminar
- **Agregar jobs custom** con formulario

### 6. Historial de Ejecuciones
- **Registro completo** de todas las ejecuciones
- **Filtros:**
  - Por job ID
  - Por estado (success, failed, running)
  - Por operación
  - Por tipo
- **Paginación**
- **Métricas:**
  - Propiedades scrapeadas
  - Páginas procesadas
  - Estado final

---

## API Endpoints

### Scheduler

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/scheduler/status` | GET | Estado del scheduler |
| `/api/scheduler/start` | POST | Iniciar scheduler |
| `/api/scheduler/stop` | POST | Detener scheduler |
| `/api/scheduler/pause` | POST | Pausar scheduler |
| `/api/scheduler/resume` | POST | Reanudar scheduler |
| `/api/scheduler/jobs` | GET | Listar jobs |
| `/api/scheduler/jobs` | POST | Agregar job |
| `/api/scheduler/jobs/{id}` | DELETE | Eliminar job |
| `/api/scheduler/jobs/{id}/pause` | POST | Pausar job |
| `/api/scheduler/jobs/{id}/resume` | POST | Reanudar job |
| `/api/scheduler/jobs/predefined` | GET | Listar jobs predefinidos |
| `/api/scheduler/jobs/predefined/{name}` | POST | Activar job predefinido |
| `/api/scheduler/jobs/default` | POST | Setup jobs por defecto |
| `/api/scheduler/executions` | GET | Historial de ejecuciones |

### Scraper

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/scraper/run` | POST | Ejecutar scraping manual |
| `/api/scraper/executions` | GET | Listar ejecuciones |
| `/api/scraper/executions?status=running` | GET | Ejecuciones activas |
| `/api/scraper/executions/{id}` | GET | Detalle de ejecución |
| `/api/scraper/executions/{id}/logs` | GET | Logs de ejecución |

---

## Tecnologías

- **Frontend:** Alpine.js + TailwindCSS
- **Backend:** Flask + APScheduler
- **Real-time:** Socket.IO (WebSocket)
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy

---

## Modelos de Datos

### ScraperExecution
```python
- id: int (PK)
- execution_id: str (UUID)
- operacion: str
- tipo: str
- start_time: datetime
- end_time: datetime
- status: str (running, completed, failed, cancelled)
- properties_scraped: int
- properties_new: int
- properties_updated: int
- pages_processed: int
- error_message: str
- duration: int (seconds)
- parameters: JSON
- triggered_by: str (manual, scheduled, api)
```

### ScraperLog
```python
- id: int (PK)
- execution_id: str (FK)
- timestamp: datetime
- level: str (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- message: str
- source: str
- log_metadata: JSON
```

---

## Flujo de Sincronización Automática

1. **Scheduler inicia** (manual o automático)
2. **Jobs predefinidos** se cargan desde `scheduler_jobs.py`
3. **Triggers se activan** según configuración (cron/interval)
4. **Scraper ejecuta** con parámetros del job
5. **Datos se persisten** en PostgreSQL
6. **Cache se invalida** automáticamente
7. **Métricas se registran** en `scraper_executions`
8. **Logs se almacenan** en `scraper_logs`
9. **Dashboard se actualiza** en tiempo real

---

## Uso Rápido

### Activar Jobs Predefinidos

1. Ir a http://localhost:4421/scraper
2. Scroll a "Jobs Predefinidos"
3. Click en "Activar" en el job deseado
4. El job aparecerá en "Jobs Activos en Scheduler"

### Ejecutar Scraping Manual

1. Configurar parámetros en "Ejecución Manual"
2. Click en "Ejecutar Scraping Manual"
3. Ver logs en tiempo real
4. Resultado aparece en "Historial de Ejecuciones"

### Monitorear Ejecuciones Activas

- Las ejecuciones activas se muestran automáticamente
- Se actualizan cada 10 segundos
- Muestran progreso en tiempo real

---

## Configuración

### Variables de Entorno

```bash
DATABASE_URL=postgresql://scraper:scraper123@localhost:5432/portalinmobiliario
DELAY_BETWEEN_REQUESTS=2
MAX_RETRIES=3
TIMEOUT=30
```

### Jobs por Defecto

Para cargar todos los jobs predefinidos automáticamente:

```bash
POST /api/scheduler/jobs/default
```

O desde Python:
```python
from scheduler import get_scheduler
from scheduler_jobs import setup_default_jobs

scheduler = get_scheduler()
setup_default_jobs(scheduler)
```

---

## Troubleshooting

### Scheduler no inicia
- Verificar que PostgreSQL esté corriendo
- Revisar logs: `docker compose -f docker-compose.v2.yml logs dashboard`
- Verificar DATABASE_URL en .env

### Jobs no se ejecutan
- Verificar que el scheduler esté "Running"
- Revisar próxima ejecución del job
- Verificar que el job no esté pausado

### Ejecuciones activas no aparecen
- Verificar que el endpoint `/api/scraper/executions?status=running` responda
- Revisar consola del navegador para errores
- Verificar que la ejecución esté en estado "running" en la BD

### Logs en tiempo real no funcionan
- Verificar que Socket.IO esté configurado
- Revisar conexión WebSocket en Network tab
- Verificar que el scraper esté emitiendo eventos

---

## Próximas Mejoras

- [ ] Gráficos de métricas históricas
- [ ] Notificaciones push cuando completa un scraping
- [ ] Exportación de reportes
- [ ] Configuración de alertas
- [ ] Dashboard de analítica de rendimiento
- [ ] Integración con Ollama para insights automáticos

---

**Última actualización:** 12 Abril 2026
