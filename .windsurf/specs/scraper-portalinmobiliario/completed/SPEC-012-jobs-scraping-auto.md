# SPEC-012: Jobs de Scraping Automático

**Estado:** completed  
**Fecha creación:** 2026-04-09  
**Fecha completado:** 2026-04-09  
**Prioridad:** Alta  
**Estimación:** 6 horas  
**Fase:** Fase 3 - Pro / Sprint 3: Automatización  
**Dependencias:** SPEC-011 (Scheduler con APScheduler)

---

## Objetivo

Implementar jobs de scraping automático configurados en el scheduler APScheduler para ejecutar scraping de forma periódica sin intervención manual. Los jobs deben cubrir las combinaciones principales de operación y tipo de propiedad, con configuración flexible de schedules y parámetros.

---

## Requisitos Funcionales

### 1. Jobs de Scraping Principales

**FR-1.1: Job: scrape_venta_departamento**
- Schedule: Diario a las 02:00 AM
- Parámetros:
  - `operacion`: venta
  - `tipo`: departamento
  - `max_pages`: 50
  - `scrape_details`: true
  - `max_detail_properties`: 100
- Descripción: Scraping diario de departamentos en venta

**FR-1.2: Job: scrape_arriendo_departamento**
- Schedule: Diario a las 03:00 AM
- Parámetros:
  - `operacion`: arriendo
  - `tipo`: departamento
  - `max_pages`: 50
  - `scrape_details`: true
  - `max_detail_properties`: 100
- Descripción: Scraping diario de departamentos en arriendo

**FR-1.3: Job: scrape_venta_casa**
- Schedule: Diario a las 04:00 AM
- Parámetros:
  - `operacion`: venta
  - `tipo`: casa
  - `max_pages`: 30
  - `scrape_details`: true
  - `max_detail_properties`: 50
- Descripción: Scraping diario de casas en venta

**FR-1.4: Job: scrape_arriendo_casa**
- Schedule: Diario a las 05:00 AM
- Parámetros:
  - `operacion`: arriendo
  - `tipo`: casa
  - `max_pages`: 30
  - `scrape_details`: true
  - `max_detail_properties`: 50
- Descripción: Scraping diario de casas en arriendo

**FR-1.5: Job: scrape_venta_oficina**
- Schedule: Semanal (lunes a las 06:00 AM)
- Parámetros:
  - `operacion`: venta
  - `tipo`: oficina
  - `max_pages`: 20
  - `scrape_details`: true
  - `max_detail_properties`: 30
- Descripción: Scraping semanal de oficinas en venta

### 2. Configuración de Jobs

**FR-2.1: Registro Automático**
- Jobs se registran automáticamente al iniciar el scheduler
- Configuración vía variables de entorno o archivo de config
- Validación de parámetros antes de registrar job

**FR-2.2: Gestión Dinámica**
- API para agregar nuevos jobs de scraping
- API para modificar parámetros de jobs existentes
- API para pausar/reanudar jobs específicos
- API para eliminar jobs

**FR-2.3: Configuración Flexible**
- Soporte para schedules tipo:
  - `interval`: cada X horas/minutos
  - `cron`: expresión cron completa
  - `date`: fecha específica (one-time)
- Parámetros overrideables por job

### 3. Integración con Scheduler

**FR-3.1: Función de Ejecución**
- Wrapper function que llama a `main.run_scraping()`
- Captura y logging de resultados
- Manejo de errores con retry
- Registro de métricas en `scheduler_executions`

**FR-3.2: Logging de Resultados**
- Cantidad de propiedades scrapeadas
- Cantidad de páginas procesadas
- Tiempo de ejecución
- Errores encontrados
- URL de exportación generada (si aplica)

**FR-3.3: Notificaciones**
- Notificación en caso de error crítico
- Notificación de resumen diario (opcional)
- Integración con sistema de notificaciones (SPEC-018)

---

## Requisitos No Funcionales

### NFR-1: Performance
- Overhead de job registration < 100ms
- Ejecución de jobs no bloquea otros jobs
- Soportar hasta 20 jobs de scraping simultáneos

### NFR-2: Confiabilidad
- Jobs no se pierden ante reinicios del scheduler
- Recuperación automática de jobs interrumpidos
- Logging detallado para debugging

### NFR-3: Mantenibilidad
- Configuración centralizada en archivo YAML o JSON
- Validación de configuración al inicio
- Documentación de parámetros disponibles

### NFR-4: Seguridad
- Validación de todos los parámetros de jobs
- Sanitización de inputs
- Rate limiting para evitar sobrecarga del portal

---

## Stack Tecnológico

- **APScheduler:** 3.10.4+ (ya instalado en SPEC-011)
- **Python logging:** Módulo estándar
- **PyYAML:** Para archivos de configuración (opcional)
- **main.py:** Función `run_scraping()` existente

---

## Archivos a Crear/Modificar

### Nuevos Archivos
1. `scheduler_jobs.py` - Definición y registro de jobs de scraping
2. `config/jobs_config.yaml` - Configuración de jobs (opcional)
3. `tests/test_scheduler_jobs.py` - Tests de jobs de scraping

### Archivos a Modificar
1. `scheduler.py` - Integrar registro de jobs al inicio
2. `main.py` - Asegurar compatibilidad con scheduler
3. `docs/ARCHITECTURE.md` - Actualizar diagrama con jobs
4. `docs/STATUS.md` - Actualizar estado del proyecto

---

## Implementación

### Paso 1: Definición de Jobs

```python
# scheduler_jobs.py
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from scheduler import ScraperScheduler
from main import run_scraping
import logging

logger = logging.getLogger(__name__)

JOB_CONFIGS = {
    'scrape_venta_departamento': {
        'trigger': CronTrigger(hour=2, minute=0),
        'params': {
            'operacion': 'venta',
            'tipo': 'departamento',
            'max_pages': 50,
            'scrape_details': True,
            'max_detail_properties': 100
        }
    },
    'scrape_arriendo_departamento': {
        'trigger': CronTrigger(hour=3, minute=0),
        'params': {
            'operacion': 'arriendo',
            'tipo': 'departamento',
            'max_pages': 50,
            'scrape_details': True,
            'max_detail_properties': 100
        }
    },
    # ... más jobs
}

def register_scraping_jobs(scheduler: ScraperScheduler):
    """Registrar todos los jobs de scraping en el scheduler."""
    for job_id, config in JOB_CONFIGS.items():
        def job_wrapper(**params):
            try:
                logger.info(f"Starting job {job_id} with params: {params}")
                result = run_scraping(**params)
                logger.info(f"Job {job_id} completed successfully")
                return result
            except Exception as e:
                logger.error(f"Job {job_id} failed: {e}", exc_info=True)
                raise
        
        scheduler.scheduler.add_job(
            job_wrapper,
            trigger=config['trigger'],
            id=job_id,
            name=job_id.replace('_', ' ').title(),
            kwargs=config['params'],
            replace_existing=True
        )
        logger.info(f"Registered job: {job_id}")
```

### Paso 2: Integración al Inicio

```python
# scheduler.py (modificación)
from scheduler_jobs import register_scraping_jobs

def start_scheduler(self):
    """Iniciar el scheduler y registrar jobs."""
    self.scheduler.start()
    register_scraping_jobs(self)
    logger.info("Scheduler started with all scraping jobs")
```

### Paso 3: API de Gestión

```python
# scheduler_api.py (extensión)
from scheduler_jobs import JOB_CONFIGS

@scheduler_bp.route('/api/scheduler/jobs/scraping', methods=['GET'])
def list_scraping_jobs():
    """Listar todos los jobs de scraping configurados."""
    return jsonify({
        'jobs': [
            {
                'id': job_id,
                'name': job_id.replace('_', ' ').title(),
                'config': config
            }
            for job_id, config in JOB_CONFIGS.items()
        ]
    })

@scheduler_bp.route('/api/scheduler/jobs/scraping/<job_id>', methods=['POST'])
def update_scraping_job(job_id):
    """Actualizar parámetros de un job de scraping."""
    data = request.json
    # Validar y actualizar
    return jsonify({'status': 'success'})
```

---

## Testing

### Tests Unitarios
- Test de registro de jobs
- Test de validación de parámetros
- Test de wrapper function
- Test de configuración de triggers

### Tests de Integración
- Test de ejecución real de job
- Test de logging de resultados
- Test de manejo de errores
- Test de persistencia tras reinicio

### Tests E2E
- Flujo completo: registrar job → esperar ejecución → verificar resultado
- Verificación de múltiples jobs ejecutándose
- Verificación de API de gestión

---

## Criterios de Aceptación

- [ ] Los 5 jobs principales se registran correctamente al iniciar
- [ ] Jobs se ejecutan según schedule configurado
- [ ] Función wrapper llama a `run_scraping()` con parámetros correctos
- [ ] Resultados se loguean correctamente en `scheduler_executions`
- [ ] API permite listar y modificar jobs de scraping
- [ ] Jobs persisten tras reinicio del scheduler
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

- [SPEC-011: Scheduler con APScheduler](./completed/SPEC-011-scheduler-apscheduler.md)
- [APScheduler Triggers](https://apscheduler.readthedocs.io/en/3.x/modules/triggers.html)
- docs/ARCHITECTURE.md - Arquitectura actual
- docs/STATUS.md - Estado del proyecto
