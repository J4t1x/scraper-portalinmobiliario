# SPEC-011: Scheduler con APScheduler

**Estado:** completed  
**Fecha creación:** 2026-04-09  
**Fecha completado:** 2026-04-09  
**Prioridad:** Alta  
**Estimación:** 8 horas  
**Fase:** Fase 3 - Pro / Sprint 3: Automatización  
**Dependencias:** SPEC-010 (ORM con SQLAlchemy)

---

## Objetivo

Implementar un sistema de scheduler automatizado usando APScheduler para ejecutar tareas de scraping de forma periódica sin intervención manual. El scheduler debe soportar configuración de jobs, manejo de concurrencia, logging detallado de ejecuciones y persistencia de estado en PostgreSQL.

---

## Requisitos Funcionales

### 1. Configuración de Jobs

**FR-1.1: Definición de Jobs**
- Soportar múltiples tipos de jobs de scraping:
  - `scrape_venta_departamento`: Scraping de departamentos en venta (diario)
  - `scrape_arriendo_casa`: Scraping de casas en arriendo (diario)
  - `scrape_venta_oficina`: Scraping de oficinas en venta (semanal)
  - `cleanup_old_data`: Limpieza de datos antiguos (mensual)
- Configuración de schedules:
  - Interval-based (ej: cada X horas)
  - Cron-based (ej: todos los días a las 2 AM)
  - Date-based (ej: una fecha específica)
- Parámetros configurables por job:
  - `operacion`: venta, arriendo, arriendo-de-temporada
  - `tipo`: departamento, casa, oficina, etc.
  - `max_pages`: límite de páginas
  - `scrape_details`: boolean para scraping de detalle
  - `max_detail_properties`: límite de propiedades con detalle

**FR-1.2: Gestión de Jobs**
- API para agregar, modificar y remover jobs
- Listar jobs activos e inactivos
- Pausar y reanudar jobs
- Obtener próxima ejecución programada

### 2. Manejo de Concurrencia

**FR-2.1: Límite de Jobs Concurrentes**
- Configurar máximo de jobs ejecutándose simultáneamente (default: 3)
- Cola de espera para jobs que exceden el límite
- Prioridad de ejecución (alta, media, baja)

**FR-2.2: Prevención de Overlap**
- Evitar que el mismo job se ejecute si la instancia anterior aún está corriendo
- Timeout máximo por job (default: 1 hora)
- Mecanismo de "missed fire" para jobs que no se ejecutaron

**FR-2.3: Manejo de Errores**
- Retry automático con exponential backoff (max 3 intentos)
- Coalescing de ejecuciones fallidas (ejecutar solo una vez si se perdieron múltiples)
- Logging detallado de errores con stacktrace

### 3. Logging de Ejecuciones

**FR-3.1: Registro de Ejecuciones**
- Tabla `scheduler_executions` en PostgreSQL con campos:
  - `id`: UUID
  - `job_id`: ID del job
  - `job_name`: Nombre del job
  - `start_time`: Timestamp de inicio
  - `end_time`: Timestamp de término
  - `status`: success, failed, running, missed
  - `properties_scraped`: Cantidad de propiedades scrapeadas
  - `pages_processed`: Cantidad de páginas procesadas
  - `error_message`: Mensaje de error (si falló)
  - `duration`: Duración en segundos
  - `metadata`: JSON con parámetros del job

**FR-3.2: Métricas**
- Tiempo promedio de ejecución por job
- Tasa de éxito por job
- Última ejecución exitosa
- Próxima ejecución programada

### 4. Persistencia de Estado en PostgreSQL

**FR-4.1: Job Store**
- Usar SQLAlchemyJobStore de APScheduler con PostgreSQL
- Persistir estado de jobs (next_run_time, trigger, etc.)
- Recuperar jobs automáticamente al reiniciar el scheduler

**FR-4.2: Estado del Scheduler**
- Tabla `scheduler_state` con campos:
  - `id`: UUID
  - `scheduler_id`: ID único del scheduler
  - `status`: running, paused, stopped
  - `last_heartbeat`: Timestamp del último heartbeat
  - `start_time`: Timestamp de inicio del scheduler
  - `total_jobs_executed`: Contador total de ejecuciones

**FR-4.3: Recuperación ante Fallos**
- Detectar jobs que estaban ejecutándose cuando el scheduler cayó
- Marcarlos como "failed" con timeout
- Re-programar ejecuciones perdidas

---

## Requisitos No Funcionales

### NFR-1: Performance
- Overhead del scheduler < 5% CPU cuando está idle
- Latencia de inicio de jobs < 1 segundo
- Soportar hasta 50 jobs configurados

### NFR-2: Confiabilidad
- Uptime del scheduler > 99.5%
- No perder jobs programados ante reinicios
- Recuperación automática ante caídas

### NFR-3: Mantenibilidad
- Configuración vía variables de entorno
- Logs estructurados en JSON
- API REST para monitoreo y control

### NFR-4: Seguridad
- Validación de parámetros de jobs
- Sanitización de inputs
- Autenticación para API de control

---

## Stack Tecnológico

- **APScheduler:** 3.10.4+
- **SQLAlchemy:** Ya existente en el proyecto
- **PostgreSQL:** Ya existente en el proyecto
- **Python logging:** Módulo estándar

---

## Archivos a Crear/Modificar

### Nuevos Archivos
1. `scheduler.py` - Configuración principal del scheduler
2. `scheduler_jobs.py` - Definición de jobs de scraping
3. `scheduler_api.py` - API REST para control del scheduler
4. `models/scheduler.py` - Modelos SQLAlchemy para scheduler
5. `tests/test_scheduler.py` - Tests del scheduler

### Archivos a Modificar
1. `requirements.txt` - Agregar APScheduler
2. `main.py` - Integrar scheduler como opción CLI
3. `app.py` - Integrar scheduler en dashboard Flask
4. `database.py` - Agregar tablas de scheduler
5. `docs/ARCHITECTURE.md` - Actualizar diagrama con scheduler
6. `docs/STATUS.md` - Actualizar estado del proyecto

---

## Implementación

### Paso 1: Configuración de APScheduler

```python
# scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ProcessPoolExecutor, ThreadPoolExecutor

class ScraperScheduler:
    def __init__(self, database_url: str):
        jobstores = {
            'default': SQLAlchemyJobStore(url=database_url)
        }
        
        executors = {
            'default': ThreadPoolExecutor(20),
            'processpool': ProcessPoolExecutor(5)
        }
        
        job_defaults = {
            'coalesce': True,
            'max_instances': 1,
            'misfire_grace_time': 300  # 5 minutos
        }
        
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults
        )
```

### Paso 2: Definición de Jobs

```python
# scheduler_jobs.py
def create_scraping_job(
    scheduler: ScraperScheduler,
    operacion: str,
    tipo: str,
    schedule: str,
    **kwargs
):
    """Crear un job de scraping con schedule específico."""
    
    def job_function():
        from main import run_scraping
        return run_scraping(
            operacion=operacion,
            tipo=tipo,
            **kwargs
        )
    
    scheduler.add_job(
        job_function,
        trigger=schedule,
        id=f'scrape_{operacion}_{tipo}',
        name=f'Scrape {operacion} {tipo}',
        replace_existing=True
    )
```

### Paso 3: Logging y Persistencia

```python
# scheduler.py (continuación)
def log_execution(self, job_id: str, status: str, **metadata):
    """Registrar ejecución en PostgreSQL."""
    execution = SchedulerExecution(
        job_id=job_id,
        status=status,
        **metadata
    )
    self.db.add(execution)
    self.db.commit()
```

### Paso 4: API de Control

```python
# scheduler_api.py
from flask import Blueprint, request, jsonify

scheduler_bp = Blueprint('scheduler', __name__)

@scheduler_bp.route('/api/scheduler/jobs', methods=['GET'])
def list_jobs():
    """Listar todos los jobs configurados."""
    jobs = scheduler.get_jobs()
    return jsonify([serialize_job(job) for job in jobs])

@scheduler_bp.route('/api/scheduler/jobs', methods=['POST'])
def add_job():
    """Agregar un nuevo job."""
    data = request.json
    # Validar y crear job
    return jsonify({'status': 'success'}), 201
```

---

## Testing

### Tests Unitarios
- Test de configuración del scheduler
- Test de creación de jobs
- Test de ejecución de jobs
- Test de logging de ejecuciones
- Test de persistencia de estado

### Tests de Integración
- Test de ejecución real de scraping vía scheduler
- Test de recuperación ante reinicios
- Test de manejo de concurrencia
- Test de timeout y missed fires

### Tests E2E
- Flujo completo: crear job → ejecutar → verificar resultado
- Verificación de persistencia tras reinicio
- Verificación de API de control

---

## Criterios de Aceptación

- [ ] Scheduler se inicia correctamente con PostgreSQL
- [ ] Jobs se crean, modifican y eliminan correctamente
- [ ] Jobs se ejecutan según schedule configurado
- [ ] Concurrencia se maneja correctamente (max 3 jobs simultáneos)
- [ ] Logging de ejecuciones se persiste en PostgreSQL
- [ ] Estado del scheduler persiste tras reinicios
- [ ] API REST funciona para control del scheduler
- [ ] Tests unitarios pasan (coverage > 80%)
- [ ] Tests de integración pasan
- [ ] Documentación actualizada

---

## Changelog

| Fecha | Cambio | Autor |
|-------|--------|-------|
| 2026-04-09 | Spec creada | Cascade |
| 2026-04-09 | Implementación completada | Cascade |

---

## Referencias

- [APScheduler Documentation](https://apscheduler.readthedocs.io/)
- [SQLAlchemyJobStore](https://apscheduler.readthedocs.io/en/3.x/modules/jobstores.html#sqlalchemyjobstore)
- docs/ARCHITECTURE.md - Arquitectura actual
- docs/STATUS.md - Estado del proyecto
