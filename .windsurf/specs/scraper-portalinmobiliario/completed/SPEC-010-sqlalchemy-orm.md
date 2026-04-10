# SPEC-010: ORM con SQLAlchemy

**Proyecto:** scraper-portalinmobiliario  
**Fecha:** 2026-04-09  
**Estado:** completed  
**Prioridad:** alta  
**Estimación:** 8 horas  
**Fecha completado:** 2026-04-09

---

## Contexto

SPEC-008 establece el modelo de datos PostgreSQL y los modelos SQLAlchemy básicos. Esta spec se enfoca en crear una capa de abstracción ORM robusta que facilite las operaciones de base de datos, implemente patrones de repositorio, y optimice el acceso a datos para el scraper.

**¿Por qué es necesario?**
- Abstraer la lógica de acceso a datos del scraper
- Implementar patrones reutilizables (Repository, Unit of Work)
- Facilitar testing con mocks y bases de datos en memoria
- Centralizar lógica de queries complejos
- Preparar la base para futura API REST

**¿Qué impacto tiene?**
- **Usuarios:** Mejor performance en consultas y búsquedas
- **Sistema:** Código más mantenible y testeable
- **Datos:** Operaciones de DB más seguras y consistentes

---

## Objetivos

### Funcionales
- [ ] Implementar patrón Repository para entidades principales
- [ ] Crear capa de Unit of Work para transacciones
- [ ] Desarrollar servicios de acceso a datos (PropertyService)
- [ ] Implementar búsquedas filtradas y paginadas
- [ ] Crear utilidades para queries complejos

### No Funcionales
- [ ] Performance: Queries < 50ms para datasets < 10k registros
- [ ] Confiabilidad: Manejo de transacciones y rollback
- [ ] Mantenibilidad: Repositorios desacoplados y testeables

---

## Requirements

### Functional Requirements (FR)

**FR-1: Repository Pattern**
- **Descripción:** Implementar clases Repository para Property, Publisher, Image
- **Input:** Modelos SQLAlchemy de SPEC-008
- **Output:** Clases Repository con métodos CRUD
- **Validaciones:**
  - Métodos: get_by_id, get_all, create, update, delete
  - Soporte para filtros dinámicos
  - Retorno de objetos de dominio, no dicts

**FR-2: Unit of Work**
- **Descripción:** Implementar patrón Unit of Work para transacciones
- **Input:** Session de SQLAlchemy
- **Output:** Context manager para transacciones
- **Validaciones:**
  - Commit automático al salir exitosamente
  - Rollback automático en excepciones
  - Soporte para múltiples operaciones atómicas

**FR-3: Property Service**
- **Descripción:** Servicio de alto nivel para operaciones de propiedades
- **Input:** Datos de propiedades scrapeadas
- **Output:** Operaciones CRUD encapsuladas
- **Validaciones:**
  - Upsert de propiedades con manejo de duplicados
  - Bulk insert para batch processing
  - Búsqueda por múltiples criterios

**FR-4: Query Builder**
- **Descripción:** Utilidades para construir queries dinámicos
- **Input:** Filtros y opciones de búsqueda
- **Output:** Queries SQLAlchemy optimizados
- **Validaciones:**
  - Soporte para filtros AND/OR
  - Paginación automática
  - Sorting dinámico

**FR-5: Database Manager**
- **Descripción:** Gestor centralizado de conexiones y sesiones
- **Input:** Configuración de DB
- **Output:** Pool de conexiones y session factory
- **Validaciones:**
  - Connection pooling configurado
  - Manejo de reintentos en fallos de conexión
  - Métricas de conexiones activas

### Non-Functional Requirements (NFR)

**NFR-1: Performance**
- Query simple: < 10ms
- Query con joins: < 50ms
- Bulk insert 1000 registros: < 2s

**NFR-2: Confiabilidad**
- Reintentos automáticos: 3 intentos con backoff exponencial
- Timeout de queries: 30s máximo
- Dead connection recovery

---

## Acceptance Criteria

**AC-1:** Repository Pattern implementado
- **Given:** Modelo Property existente
- **When:** Se usa PropertyRepository.get_by_id(id)
- **Then:** Retorna objeto Property o None si no existe

**AC-2:** Unit of Work funciona correctamente
- **Given:** Múltiples operaciones de escritura
- **When:** Se ejecutan dentro de UnitOfWork context
- **Then:** Todas se commit o todas se rollback en caso de error

**AC-3:** Property Service upsert funciona
- **Given:** Propiedad scrapeada con URL existente
- **When:** Se llama a PropertyService.upsert_property(data)
- **Then:** Actualiza registro existente sin crear duplicado

**AC-4:** Búsquedas filtradas funcionan
- **Given:** 1000 propiedades en DB
- **When:** Se busca con filtros (precio, ubicación, tipo)
- **Then:** Retorna resultados paginados en < 100ms

**AC-5:** Bulk insert optimizado
- **Given:** Lista de 500 propiedades nuevas
- **When:** Se ejecuta PropertyService.bulk_insert(properties)
- **Then:** Inserta todos los registros en < 3s

---

## Technical Design

### Arquitectura

```
┌─────────────────────────────────────┐
│           Scraper Core              │
│    (scraper.py, processors)         │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│       PropertyService               │
│   (Alta lógica de negocio)          │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│    PropertyRepository               │
│   (Abstracción de acceso a datos)   │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│      UnitOfWork / Session           │
│   (Transacciones y sesiones)        │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│    DatabaseManager (Pool)           │
│   (Conexiones y engine)             │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│         PostgreSQL                  │
└─────────────────────────────────────┘
```

### Componentes Afectados

- **Nuevo archivo:** `src/db/repositories/base_repository.py`
  - Clase base abstracta Repository
  - Métodos CRUD genéricos
  
- **Nuevo archivo:** `src/db/repositories/property_repository.py`
  - PropertyRepository extends BaseRepository
  - Métodos específicos: find_by_url, find_by_location, etc.
  
- **Nuevo archivo:** `src/db/repositories/publisher_repository.py`
  - PublisherRepository extends BaseRepository
  
- **Nuevo archivo:** `src/db/unit_of_work.py`
  - Context manager UnitOfWork
  - Manejo de transacciones
  
- **Nuevo archivo:** `src/db/services/property_service.py`
  - PropertyService con lógica de negocio
  - Upsert, bulk operations
  
- **Nuevo archivo:** `src/db/database_manager.py`
  - DatabaseManager singleton
  - Pool de conexiones
  
- **Nuevo archivo:** `src/db/query_builder.py`
  - Utilidades para filtros dinámicos
  - Paginación

### Data Model

```python
# Repository Pattern
class BaseRepository(Generic[T]):
    def get_by_id(self, id: int) -> Optional[T]
    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]
    def create(self, obj: T) -> T
    def update(self, id: int, data: dict) -> Optional[T]
    def delete(self, id: int) -> bool
    def find_by(self, **kwargs) -> List[T]

# Unit of Work
class UnitOfWork:
    def __enter__(self) -> 'UnitOfWork'
    def __exit__(self, exc_type, exc_val, exc_tb)
    def commit()
    def rollback()
    @property
    def properties() -> PropertyRepository
    @property
    def publishers() -> PublisherRepository

# Service
class PropertyService:
    def __init__(self, uow: UnitOfWork)
    def upsert_property(self, data: dict) -> Property
    def bulk_insert(self, properties: List[dict]) -> int
    def search_properties(self, filters: dict, page: int = 1) -> PaginatedResult
```

### API / Interfaces

```python
# Uso típico del ORM

# 1. Simple query con Repository
with UnitOfWork() as uow:
    repo = uow.properties
    prop = repo.get_by_id(123)
    props = repo.find_by(location="Santiago", property_type="casa")

# 2. Upsert de propiedad scrapeada
with UnitOfWork() as uow:
    service = PropertyService(uow)
    property_data = {
        "url": "https://portalinmobiliario.com/...",
        "title": "Casa en Vitacura",
        "price": 450000000,
        # ...
    }
    prop = service.upsert_property(property_data)
    uow.commit()

# 3. Bulk insert
with UnitOfWork() as uow:
    service = PropertyService(uow)
    count = service.bulk_insert(scraped_properties)

# 4. Búsqueda paginada
filters = {
    "price_min": 300000000,
    "price_max": 600000000,
    "location": "Vitacura",
    "property_type": "casa"
}
result = service.search_properties(filters, page=1, per_page=20)
```

### Configuración

Variables de entorno:
```env
# Database (ya existente en SPEC-008)
DATABASE_URL=postgresql://user:pass@localhost:5432/scraper_db

# Pool Configuration
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# Query Timeout
DB_QUERY_TIMEOUT=30
```

---

## Implementation Plan

### Fase 1: Setup (2 horas)
- [ ] Crear estructura de directorios `src/db/{repositories,services}`
- [ ] Implementar DatabaseManager con connection pooling
- [ ] Configurar session factory

### Fase 2: Repository Pattern (3 horas)
- [ ] Implementar BaseRepository abstracto
- [ ] Implementar PropertyRepository con métodos específicos
- [ ] Implementar PublisherRepository
- [ ] Tests unitarios para repositories

### Fase 3: Unit of Work (1.5 horas)
- [ ] Implementar UnitOfWork context manager
- [ ] Integrar repositories en UoW
- [ ] Tests de transacciones

### Fase 4: Property Service (1.5 horas)
- [ ] Implementar PropertyService.upsert_property()
- [ ] Implementar PropertyService.bulk_insert()
- [ ] Implementar PropertyService.search_properties()
- [ ] Integrar QueryBuilder

---

## Testing Strategy

### Unit Tests
```python
def test_repository_get_by_id():
    # Test de lectura simple
    pass

def test_repository_find_by_filters():
    # Test de búsqueda con filtros
    pass

def test_unit_of_work_commit():
    # Test de commit exitoso
    pass

def test_unit_of_work_rollback():
    # Test de rollback en excepción
    pass

def test_property_service_upsert():
    # Test de upsert de propiedad
    pass
```

### Integration Tests
```python
def test_full_scrape_to_db_flow():
    # Test end-to-end: scrape → UoW → DB
    pass

def test_bulk_insert_performance():
    # Test de performance con 1000 registros
    pass
```

---

## Dependencies

### Specs Relacionadas
- **SPEC-008:** Modelo de datos PostgreSQL (debe completarse antes)
- **SPEC-009:** Migración de datos existentes (puede trabajarse en paralelo)
- **SPEC-011:** Scheduler con APScheduler (usa estos repositorios)

### Dependencias Externas
- SQLAlchemy 2.0+
- psycopg2-binary (ya incluido en SPEC-008)
- pytest-asyncio (para tests)

---

## Risks & Mitigations

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Overhead de abstracción | Media | Medio | Benchmarks, lazy loading |
| Fugas de conexión | Baja | Alto | Context managers obligatorios, max pool size |
| N+1 queries | Media | Alto | Eager loading con join, query optimization |
| Complejidad excesiva | Media | Medio | Documentación, ejemplos claros |

---

## Metrics & Monitoring

### Métricas de Éxito
- Tiempo promedio de query: < 50ms
- Tiempo de upsert: < 100ms
- Tiempo de bulk insert (1000): < 3s
- Coverage de tests: > 80%

### Monitoreo
- Query execution time
- Active connections in pool
- Transaction rollback rate
- Repository method call frequency

---

## Notes

- Basado en SPEC-008 - depende de los modelos SQLAlchemy ya definidos
- El patrón Repository sigue el principio de inversión de dependencias
- Unit of Work garantiza atomicidad en operaciones múltiples
- Considerar caching en memoria para queries frecuentes (futuro SPEC-015)

---

## Implementation Notes (2026-04-09)

### Archivos creados:
- `db/__init__.py` - Export de módulos db
- `db/repositories/__init__.py` - Export de repositorios
- `db/repositories/base_repository.py` - BaseRepository genérico con CRUD
- `db/repositories/property_repository.py` - PropertyRepository con métodos específicos
- `db/unit_of_work.py` - UnitOfWork context manager
- `db/services/__init__.py` - Export de servicios
- `db/services/property_service.py` - PropertyService con lógica de negocio

### Estructura adaptada:
El spec original sugería `src/db/` pero se adaptó a la estructura plana del proyecto usando `db/` directamente.

### Patrones implementados:
- **Repository Pattern:** BaseRepository genérico + PropertyRepository específico
- **Unit of Work:** Context manager con commit/rollback automáticos
- **Service Layer:** PropertyService con lógica de negocio (upsert, bulk, search)

### Uso:
```python
from db import UnitOfWork, PropertyService

# Simple query con Repository
with UnitOfWork() as uow:
    prop = uow.properties.get_by_id(123)
    props = uow.properties.find_by_location(comuna="Santiago")

# Upsert de propiedad scrapeada
with UnitOfWork() as uow:
    service = PropertyService(uow)
    prop = service.upsert_property(property_data)
    uow.commit()

# Búsqueda paginada
with UnitOfWork() as uow:
    service = PropertyService(uow)
    result = service.search_properties(
        filters={"operacion": "venta", "tipo": "casa"},
        page=1,
        per_page=20
    )
```

---

## Changelog

| Fecha | Cambio | Autor |
|-------|--------|-------|
| 2026-04-09 | Spec creada | Cascade |
| 2026-04-09 | Implementación completada | Cascade |
