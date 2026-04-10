# SPEC-008: Modelo de datos PostgreSQL

**Proyecto:** scraper-portalinmobiliario  
**Fecha:** 2026-04-09  
**Estado:** completed  
**Prioridad:** crítica  
**Estimación:** 12 horas  
**Fecha completado:** 2026-04-09

---

## Contexto

Actualmente el scraper exporta datos únicamente a archivos planos (TXT, JSON, CSV). Esto limita la capacidad de:
- Consultar datos históricos
- Detectar duplicados cross-session
- Implementar alertas inteligentes
- Construir dashboards en tiempo real
- Escalar a múltiples scrapers

**¿Por qué es necesario?**
- Base para todas las features Pro (API, Dashboard, ML)
- Persistencia de datos históricos
- Soporte para consultas complejas
- Foundation para detección de duplicados

**¿Qué impacto tiene?**
- **Usuarios:** Habilita features avanzadas de búsqueda y filtrado
- **Sistema:** Transforma scraper de batch-only a sistema persistente
- **Datos:** Permite tracking temporal y análisis de tendencias

---

## Objetivos

### Funcionales
- [ ] Diseñar esquema PostgreSQL para propiedades
- [ ] Implementar modelos SQLAlchemy con relaciones
- [ ] Crear sistema de migrations con Alembic
- [ ] Integrar inserción de datos en scraper
- [ ] Implementar upsert para evitar duplicados

### No Funcionales
- [ ] Performance: Inserción < 100ms por propiedad
- [ ] Confiabilidad: Manejo robusto de errores de DB
- [ ] Mantenibilidad: Migrations versionadas y reversibles

---

## Requirements

### Functional Requirements (FR)

**FR-1: Esquema de base de datos**
- **Descripción:** Diseñar tablas para propiedades, características, imágenes, publicadores
- **Input:** Estructura de datos actual del scraper
- **Output:** Schema SQL con relaciones y constraints
- **Validaciones:** 
  - Primary keys en todas las tablas
  - Foreign keys con CASCADE
  - Indexes en campos de búsqueda
  - Unique constraints para evitar duplicados

**FR-2: Modelos SQLAlchemy**
- **Descripción:** Mapear esquema a modelos Python con relaciones
- **Input:** Schema SQL
- **Output:** Clases SQLAlchemy con type hints
- **Validaciones:**
  - Todas las columnas con tipos correctos
  - Relaciones correctamente configuradas
  - Validaciones a nivel de modelo

**FR-3: Sistema de Migrations**
- **Descripción:** Configurar Alembic para versionado de schema
- **Input:** Modelos SQLAlchemy
- **Output:** Directorio migrations/ con scripts versionados
- **Validaciones:**
  - Migration inicial crea todas las tablas
  - Comando `upgrade` funciona
  - Comando `downgrade` funciona (reversible)

**FR-4: Integración con Scraper**
- **Descripción:** Modificar scraper para persistir en PostgreSQL
- **Input:** Datos scrapeados
- **Output:** Datos insertados en DB
- **Validaciones:**
  - Cada propiedad scrapeada se inserta en DB
  - Manejo de errores de conexión
  - Logging de inserciones fallidas

**FR-5: Upsert para evitar duplicados**
- **Descripción:** Implementar lógica upsert (insert or update)
- **Input:** Propiedad scrapeada
- **Output:** Insert si nueva, update si existe
- **Validaciones:**
  - Usa campo único (url o id_portal)
  - Actualiza campos modificados
  - Mantiene histórico de cambios

### Non-Functional Requirements (NFR)

**NFR-1: Performance**
- Tiempo de inserción: < 100ms por propiedad
- Bulk insert: 1000 propiedades < 10 segundos
- Queries de búsqueda: < 500ms

**NFR-2: Confiabilidad**
- Tasa de éxito: > 99% inserciones
- Reintentos automáticos: 3 intentos con backoff
- Logging: Detallado de errores DB

**NFR-3: Mantenibilidad**
- Migrations versionadas con mensajes descriptivos
- Schema documentado en comentarios
- Tests de migrations

---

## Acceptance Criteria

**AC-1:** Schema PostgreSQL creado y documentado
- **Given:** Proyecto sin base de datos
- **When:** Se ejecuta migration inicial
- **Then:** Se crean todas las tablas con relaciones correctas

**AC-2:** Modelos SQLAlchemy mapean schema correctamente
- **Given:** Schema PostgreSQL
- **When:** Se instancian modelos Python
- **Then:** Cada modelo corresponde a tabla con tipos correctos

**AC-3:** Scraper persiste datos en PostgreSQL
- **Given:** Scraper ejecutándose con DATABASE_URL configurado
- **When:** Se scrapea una página
- **Then:** Datos se insertan en DB correctamente

**AC-4:** Upsert evita duplicados
- **Given:** Propiedad ya existe en DB
- **When:** Se scrapea misma propiedad nuevamente
- **Then:** Se actualiza registro existente, no se crea duplicado

**AC-5:** Migrations son reversibles
- **Given:** Migration aplicada
- **When:** Se ejecuta downgrade
- **Then:** Schema vuelve a estado anterior sin pérdida de datos

---

## Technical Design

### Arquitectura

```
┌─────────────────┐
│   Scraper       │
│  (Selenium)     │
└────────┬────────┘
         │ datos
         ▼
┌─────────────────┐
│  Data Layer     │
│  (SQLAlchemy)   │
└────────┬────────┘
         │ ORM
         ▼
┌─────────────────┐
│  PostgreSQL     │
│  (Railway)      │
└─────────────────┘
```

### Componentes Afectados

- **Nuevo:** `database.py` - Configuración SQLAlchemy y sesión
- **Nuevo:** `models/` - Directorio con modelos SQLAlchemy
  - `property.py` - Modelo principal Property
  - `feature.py` - Modelo Feature
  - `image.py` - Modelo Image
  - `publisher.py` - Modelo Publisher
- **Nuevo:** `migrations/` - Directorio Alembic
  - `versions/` - Scripts de migration
  - `env.py` - Configuración Alembic
  - `script.py.mako` - Template de migrations
- **Modificado:** `scraper_selenium.py` - Integración con DB
- **Modificado:** `config.py` - Agregar DATABASE_URL
- **Modificado:** `requirements.txt` - Agregar sqlalchemy, alembic, psycopg2-binary
- **Modificado:** `.env.example` - Agregar DATABASE_URL

### Data Model

```python
# models/property.py
class Property(Base):
    __tablename__ = 'properties'
    
    id = Column(Integer, primary_key=True)
    url = Column(String(500), unique=True, nullable=False, index=True)
    portal_id = Column(String(100), index=True)
    
    # Datos básicos
    titulo = Column(String(500))
    precio = Column(Integer)
    precio_moneda = Column(String(10))
    operacion = Column(String(50))
    tipo = Column(String(50))
    
    # Ubicación
    comuna = Column(String(100))
    region = Column(String(100))
    direccion = Column(String(500))
    
    # Metadatos
    publicado_en = Column(DateTime)
    scrapeado_en = Column(DateTime, default=datetime.utcnow)
    actualizado_en = Column(DateTime, onupdate=datetime.utcnow)
    
    # Relaciones
    features = relationship("Feature", back_populates="property", cascade="all, delete-orphan")
    images = relationship("Image", back_populates="property", cascade="all, delete-orphan")
    publisher = relationship("Publisher", back_populates="properties")

class Feature(Base):
    __tablename__ = 'features'
    
    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey('properties.id', ondelete='CASCADE'))
    key = Column(String(100))
    value = Column(String(500))
    
    property = relationship("Property", back_populates="features")

class Image(Base):
    __tablename__ = 'images'
    
    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey('properties.id', ondelete='CASCADE'))
    url = Column(String(500))
    es_principal = Column(Boolean, default=False)
    
    property = relationship("Property", back_populates="images")

class Publisher(Base):
    __tablename__ = 'publishers'
    
    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey('properties.id', ondelete='CASCADE'))
    nombre = Column(String(200))
    telefono = Column(String(50))
    email = Column(String(200))
    tipo = Column(String(50))  # profesional, particular
    
    property = relationship("Property", back_populates="publisher")
```

### API / Interfaces

**Función: setup_database()**
```python
def setup_database(database_url: str) -> Engine:
    """
    Configurar conexión a PostgreSQL y crear engine.
    
    Args:
        database_url: URL de conexión PostgreSQL
        
    Returns:
        SQLAlchemy Engine
        
    Raises:
        OperationalError: Si no puede conectar
    """
    pass
```

**Función: create_tables()**
```python
def create_tables(engine: Engine) -> None:
    """
    Crear todas las tablas desde modelos.
    
    Args:
        engine: SQLAlchemy Engine
    """
    pass
```

**Función: upsert_property()**
```python
def upsert_property(session: Session, property_data: Dict) -> Property:
    """
    Insertar o actualizar propiedad (upsert).
    
    Args:
        session: SQLAlchemy Session
        property_data: Dict con datos de propiedad
        
    Returns:
        Instancia de Property (creada o actualizada)
    """
    pass
```

### Configuración

Variables de entorno:
```env
DATABASE_URL=postgresql://user:pass@host:port/dbname
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
```

Dependencias nuevas:
```txt
sqlalchemy==2.0.25
alembic==1.13.1
psycopg2-binary==2.9.9
```

---

## Implementation Plan

### Fase 1: Setup (2 horas)
- [ ] Instalar dependencias (sqlalchemy, alembic, psycopg2-binary)
- [ ] Crear archivo `database.py` con configuración SQLAlchemy
- [ ] Configurar variable DATABASE_URL en config.py
- [ ] Actualizar .env.example con DATABASE_URL

### Fase 2: Modelos (3 horas)
- [ ] Crear directorio `models/`
- [ ] Implementar modelo Property
- [ ] Implementar modelo Feature
- [ ] Implementar modelo Image
- [ ] Implementar modelo Publisher
- [ ] Configurar relaciones entre modelos

### Fase 3: Migrations (3 horas)
- [ ] Inicializar Alembic (`alembic init`)
- [ ] Configurar `alembic/env.py` con modelos
- [ ] Generar migration inicial (`alembic revision --autogenerate`)
- [ ] Revisar y ajustar migration generada
- [ ] Probar upgrade y downgrade

### Fase 4: Integración (3 horas)
- [ ] Implementar función upsert_property()
- [ ] Modificar scraper_selenium.py para persistir datos
- [ ] Agregar manejo de errores DB
- [ ] Agregar logging de operaciones DB
- [ ] Probar inserción con datos reales

### Fase 5: Testing (1 hora)
- [ ] Test de conexión a DB
- [ ] Test de inserción de propiedad
- [ ] Test de upsert (no duplicados)
- [ ] Test de migrations (upgrade/downgrade)

---

## Testing Strategy

### Unit Tests
```python
def test_property_model_creation():
    """Test creación de modelo Property."""
    prop = Property(
        url="https://example.com/prop1",
        titulo="Departamento Santiago",
        precio=100000000
    )
    assert prop.url == "https://example.com/prop1"
    assert prop.precio == 100000000

def test_upsert_new_property():
    """Test upsert crea nueva propiedad."""
    data = {"url": "https://example.com/new", "titulo": "Nuevo"}
    prop = upsert_property(session, data)
    assert prop.id is not None

def test_upsert_existing_property():
    """Test upsert actualiza propiedad existente."""
    # Crear propiedad
    data1 = {"url": "https://example.com/existing", "titulo": "Original"}
    prop1 = upsert_property(session, data1)
    
    # Actualizar
    data2 = {"url": "https://example.com/existing", "titulo": "Actualizado"}
    prop2 = upsert_property(session, data2)
    
    assert prop1.id == prop2.id
    assert prop2.titulo == "Actualizado"
```

### Integration Tests
```python
def test_scraper_persistence():
    """Test scraper persiste datos en DB."""
    # Ejecutar scraper con DATABASE_URL
    # Verificar que datos están en DB
    results = session.query(Property).all()
    assert len(results) > 0
```

### E2E Tests
- Ejecutar scraper completo con persistencia
- Verificar datos en Railway PostgreSQL
- Verificar que no hay duplicados

---

## Rollout Plan

### Desarrollo
1. Implementar en rama `feat/SPEC-008-postgres-model`
2. Tests locales con PostgreSQL local (docker-compose)
3. Code review

### Testing
1. Ejecutar migrations en Railway staging
2. Probar inserción con datos de prueba
3. Verificar performance de inserciones
4. Probar rollback de migrations

### Deployment
1. Merge a `main`
2. Deploy automático a Railway
3. Ejecutar migrations en producción
4. Monitorear logs de inserciones

### Rollback
Si algo falla:
1. Revertir commit
2. Ejecutar `alembic downgrade base`
3. Investigar error
4. Fix y re-deploy

---

## Dependencies

### Specs Relacionadas
- SPEC-009: Migración de datos existentes (depende de esta)
- SPEC-010: ORM con SQLAlchemy (esta spec es el setup base)

### Dependencias Externas
- PostgreSQL 15 (Railway)
- SQLAlchemy 2.0.25
- Alembic 1.13.1
- psycopg2-binary 2.9.9

---

## Risks & Mitigations

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Cambio en estructura de datos scrapeados | Media | Alto | Schema flexible con columnas JSON adicionales |
| Performance de inserciones masivas | Media | Medio | Implementar bulk insert, connection pooling |
| Migrations fallidas en producción | Baja | Alto | Probar migrations en staging primero, backup antes |
| Conexión DB inestable | Baja | Medio | Retry con backoff, connection pooling |

---

## Metrics & Monitoring

### Métricas de Éxito
- Tasa de inserción: > 99%
- Tiempo promedio inserción: < 100ms
- Duplicados detectados: 0%

### Monitoreo
- Logs de errores de conexión
- Conteo de propiedades insertadas por sesión
- Tiempo de ejecución de inserciones
- Tamaño de base de datos

---

## Notes

- Considerar usar columnas JSON para características flexibles
- Implementar soft deletes en lugar de hard deletes
- Agregar indexes en campos de búsqueda frecuentes (comuna, precio, tipo)
- Documentar schema en comments de modelos
- Considerar particionamiento por fecha para datasets grandes

---

## Implementation Notes (2026-04-09)

### Archivos creados:
- `database.py` - Configuración SQLAlchemy y sesión
- `models/__init__.py` - Export de modelos
- `models/property.py` - Modelo Property
- `models/feature.py` - Modelo Feature
- `models/image.py` - Modelo Image
- `models/publisher.py` - Modelo Publisher
- `scraper_db_integration.py` - Funciones de persistencia (upsert_property, persist_properties)
- `migrations/env.py` - Configuración Alembic
- `migrations/script.py.mako` - Template de migrations
- `migrations/alembic.ini` - Configuración Alembic
- `migrations/versions/20260409_0100_001_initial_schema.py` - Migration inicial

### Archivos modificados:
- `scraper_selenium.py` - Agregado parámetro persist_to_db a __init__ y llamada a persist_properties en scrape_all_pages
- `main.py` - Agregado argumento --persist-to-db

### Dependencias:
Ya están en requirements.txt:
- sqlalchemy==2.0.25
- alembic==1.13.1
- psycopg2-binary==2.9.9

### Uso:
```bash
# Ejecutar scraper con persistencia en PostgreSQL
python main.py --operacion venta --tipo departamento --persist-to-db --max-pages 1

# Ejecutar migrations (cuando DATABASE_URL esté configurado)
alembic upgrade head
```

---

## Changelog

| Fecha | Cambio | Autor |
|-------|--------|-------|
| 2026-04-09 | Spec creada | Cascade |
| 2026-04-09 | Implementación completada | Cascade |
