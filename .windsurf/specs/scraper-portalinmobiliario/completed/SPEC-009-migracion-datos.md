# SPEC-009: Migración de datos existentes

**Proyecto:** scraper-portalinmobiliario  
**Fecha:** 2026-04-09  
**Estado:** completed  
**Prioridad:** alta  
**Estimación:** 6 horas  
**Fecha completado:** 2026-04-09

---

## Contexto

Actualmente el scraper exporta datos a archivos TXT (JSONL), JSON y CSV en la carpeta `output/`. Para implementar persistencia en PostgreSQL (SPEC-008), necesitamos migrar los datos existentes a la base de datos.

**¿Por qué es necesario?**
- Evitar pérdida de datos históricos scrapeados
- Mantener continuidad durante la transición a PostgreSQL
- Permitir análisis de datos históricos en la nueva arquitectura

**¿Qué impacto tiene?**
- Usuarios podrán acceder a datos históricos vía API
- Sistema tendrá datos iniciales para testing
- Facilita transición suave a arquitectura basada en DB

---

## Objetivos

### Funcionales
- [ ] Leer archivos exportados (TXT/JSON/CSV) desde `output/`
- [ ] Parsear y validar datos antes de inserción
- [ ] Insertar datos en PostgreSQL usando el modelo definido en SPEC-008
- [ ] Manejar duplicados durante migración
- [ ] Generar reporte de migración (éxitos, errores, estadísticas)

### No Funcionales
- [ ] Performance: Migrar 1000 propiedades en < 2 minutos
- [ ] Confiabilidad: Rollback automático si falla migración
- [ ] Mantenibilidad: Script reutilizable para futuras migraciones

---

## Requirements

### Functional Requirements (FR)

**FR-1: Lectura de archivos exportados**
- **Descripción:** Script debe leer archivos TXT, JSON y CSV desde `output/`
- **Input:** Path a directorio `output/` o archivo específico
- **Output:** Lista de propiedades parseadas
- **Validaciones:**
  - Verificar que archivo existe
  - Validar formato (TXT debe ser JSONL, JSON debe tener estructura correcta)
  - Manejar encoding UTF-8

**FR-2: Validación de datos**
- **Descripción:** Validar cada propiedad antes de insertar en DB
- **Input:** Propiedad individual (dict)
- **Output:** Propiedad validada o error específico
- **Validaciones:**
  - Campos requeridos: id, titulo, precio, ubicacion, url, operacion, tipo
  - Tipos de datos correctos
  - Valores no nulos para campos críticos

**FR-3: Inserción en PostgreSQL**
- **Descripción:** Insertar propiedades validadas usando modelo de SPEC-008
- **Input:** Lista de propiedades validadas
- **Output:** Número de inserciones exitosas
- **Validaciones:**
  - Usar transacción atómica
  - Manejar conflictos de duplicados (ON CONFLICT DO NOTHING o UPDATE)
  - Batch inserts para performance (100 registros por batch)

**FR-4: Manejo de duplicados**
- **Descripción:** Detectar y manejar propiedades duplicadas durante migración
- **Input:** Propiedad a insertar
- **Output:** Decisión de insertar o saltar
- **Validaciones:**
  - Verificar duplicados por `id` (campo único)
  - Opción: sobrescribir o mantener original
  - Log de duplicados encontrados

**FR-5: Reporte de migración**
- **Descripción:** Generar reporte detallado del proceso de migración
- **Input:** Estadísticas de migración
- **Output:** Reporte en consola y archivo JSON
- **Validaciones:**
  - Total de registros procesados
  - Exitosos, fallidos, duplicados
  - Tiempo de ejecución
  - Lista de errores con detalles

### Non-Functional Requirements (NFR)

**NFR-1: Performance**
- Tiempo de migración: < 2 minutos para 1000 propiedades
- Throughput: > 8 propiedades/segundo
- Uso de memoria: < 200 MB

**NFR-2: Confiabilidad**
- Tasa de éxito: > 95%
- Manejo de errores: rollback automático si falla > 5% de registros
- Logging: detallado para debugging

**NFR-3: Mantenibilidad**
- Código modular y reusable
- Configuración vía variables de entorno
- Tests unitarios para funciones críticas

---

## Acceptance Criteria

**AC-1:** Migración exitosa de archivos TXT
- **Given:** Archivo TXT con 50 propiedades en `output/`
- **When:** Ejecutar script de migración
- **Then:** 50 propiedades insertadas en PostgreSQL, reporte muestra 100% éxito

**AC-2:** Migración exitosa de archivos JSON
- **Given:** Archivo JSON con 100 propiedades en `output/`
- **When:** Ejecutar script de migración
- **Then:** 100 propiedades insertadas, reporte muestra estadísticas correctas

**AC-3:** Manejo de duplicados
- **Given:** Archivo con 10 propiedades, 3 ya existen en DB
- **When:** Ejecutar migración con opción `--skip-duplicates`
- **Then:** 7 nuevas propiedades insertadas, 3 duplicados detectados y saltados

**AC-4:** Rollback ante errores críticos**
- **Given:** Archivo con datos corruptos (20% inválidos)
- **When:** Ejecutar migración
- **Then:** Transacción rollback, ningún dato insertado, error reportado

**AC-5:** Reporte detallado**
- **Given:** Migración de 200 propiedades con 5 errores
- **When:** Ejecutar migración
- **Then:** Reporte muestra: 195 exitosos, 5 fallidos, tiempo, lista de errores

---

## Technical Design

### Arquitectura

```
┌─────────────────┐
│  migrate.py     │
│  (CLI Script)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ FileReader     │
│ (TXT/JSON/CSV)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ DataValidator  │
│ (Validación)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  PostgreSQL     │
│  (Modelo SPEC-008)│
└─────────────────┘
```

### Componentes Afectados

- **Archivo nuevo:** `scripts/migrate_to_postgres.py`
  - Cambio: Crear script de migración
  - Razón: Script reutilizable para migración inicial

- **Archivo nuevo:** `scripts/data_reader.py`
  - Cambio: Módulo para leer archivos exportados
  - Razón: Separación de responsabilidades

- **Archivo nuevo:** `scripts/data_validator.py`
  - Cambio: Módulo para validar datos
  - Razón: Validación reutilizable

- **Archivo:** `requirements.txt`
  - Cambio: Agregar dependencias si necesarias
  - Razón: Asegurar disponibilidad de librerías

### Data Model

Usa el modelo definido en SPEC-008:

```python
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Property(Base):
    __tablename__ = 'properties'
    
    id = Column(String, primary_key=True)
    titulo = Column(String, nullable=False)
    headline = Column(String)
    precio = Column(String, nullable=False)
    ubicacion = Column(String, nullable=False)
    atributos = Column(JSON)
    url = Column(String, nullable=False)
    operacion = Column(String, nullable=False)
    tipo = Column(String, nullable=False)
    
    # Campos de detalle (opcionales)
    descripcion = Column(Text)
    caracteristicas = Column(JSON)
    publicador = Column(JSON)
    imagenes = Column(JSON)
    coordenadas = Column(JSON)
    fecha_publicacion = Column(DateTime)
    
    # Metadatos
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### API / Interfaces

**Función principal:**
```python
def migrate_to_postgres(
    source_path: str = "output/",
    db_url: str = None,
    skip_duplicates: bool = True,
    batch_size: int = 100,
    dry_run: bool = False
) -> Dict:
    """
    Migrar datos desde archivos exportados a PostgreSQL.
    
    Args:
        source_path: Path al directorio o archivo a migrar
        db_url: URL de conexión a PostgreSQL (default: desde env)
        skip_duplicates: Saltar propiedades duplicadas (default: True)
        batch_size: Tamaño de batch para inserts (default: 100)
        dry_run: Simular migración sin insertar datos
    
    Returns:
        Dict con estadísticas de migración:
        {
            "total_processed": int,
            "successful": int,
            "failed": int,
            "duplicates": int,
            "errors": List[Dict],
            "execution_time": float
        }
    
    Raises:
        FileNotFoundError: Si source_path no existe
        ValueError: Si formato de archivo es inválido
    """
    pass
```

**Funciones auxiliares:**
```python
def read_exported_file(file_path: str) -> List[Dict]:
    """Leer archivo exportado (TXT/JSON/CSV) y retornar lista de propiedades."""
    pass

def validate_property(prop: Dict) -> Tuple[bool, str]:
    """Validar una propiedad, retorna (valido, error_message)."""
    pass

def insert_batch(session, properties: List[Dict]) -> Tuple[int, int]:
    """Insertar batch de propiedades, retorna (exitosos, fallidos)."""
    pass

def generate_report(stats: Dict, output_path: str = None):
    """Generar reporte de migración en consola y archivo."""
    pass
```

### Configuración

Variables de entorno:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/scraper_db
MIGRATION_SOURCE=output/
MIGRATION_BATCH_SIZE=100
MIGRATION_SKIP_DUPLICATES=true
```

---

## Implementation Plan

### Fase 1: Setup (1 hora)
- [ ] Crear estructura de directorios `scripts/`
- [ ] Crear `scripts/data_reader.py` con lectores para TXT/JSON/CSV
- [ ] Crear `scripts/data_validator.py` con validaciones
- [ ] Agregar dependencias a `requirements.txt` si necesario

### Fase 2: Core Implementation (3 horas)
- [ ] Implementar `read_exported_file()` para cada formato
- [ ] Implementar `validate_property()` con reglas de validación
- [ ] Implementar `migrate_to_postgres()` con lógica principal
- [ ] Implementar `insert_batch()` con transacciones atómicas
- [ ] Implementar detección y manejo de duplicados

### Fase 3: Testing (1 hora)
- [ ] Tests unitarios para `data_reader.py`
- [ ] Tests unitarios para `data_validator.py`
- [ ] Test de integración con SQLite local
- [ ] Test con datos reales de `output/`

### Fase 4: Documentation (1 hora)
- [ ] Documentar uso del script en README.md
- [ ] Crear guía `docs/migration/MIGRATION-GUIDE.md`
- [ ] Agregar ejemplos de uso
- [ ] Comentarios en código

---

## Testing Strategy

### Unit Tests
```python
def test_read_txt_file():
    """Test lectura de archivo TXT (JSONL)."""
    pass

def test_read_json_file():
    """Test lectura de archivo JSON estructurado."""
    pass

def test_validate_property_success():
    """Test validación de propiedad correcta."""
    pass

def test_validate_property_missing_field():
    """Test validación falla por campo faltante."""
    pass

def test_insert_batch_success():
    """Test inserción de batch exitosa."""
    pass
```

### Integration Tests
```python
def test_migration_full_flow():
    """Test flujo completo de migración con SQLite."""
    pass

def test_migration_with_duplicates():
    """Test manejo de duplicados."""
    pass

def test_migration_rollback_on_error():
    """Test rollback cuando hay errores críticos."""
    pass
```

### E2E Tests
- Migrar archivo real de `output/` a PostgreSQL local
- Verificar datos en DB
- Verificar reporte generado

---

## Rollout Plan

### Desarrollo
1. Implementar en rama `feat/SPEC-009`
2. Tests locales con SQLite
3. Code review

### Testing
1. Ejecutar con datos de prueba
2. Ejecutar con datos reales de `output/`
3. Verificar integridad de datos en PostgreSQL

### Deployment
1. Merge a `main`
2. Ejecutar migración en staging
3. Ejecutar migración en producción (con backup previo)

### Rollback
Si algo falla:
1. Restaurar backup de PostgreSQL
2. Investigar error
3. Fix y re-ejecutar migración

---

## Dependencies

### Specs Relacionadas
- SPEC-008: Modelo de datos PostgreSQL (debe completarse antes)

### Dependencias Externas
- SQLAlchemy (ya en requirements.txt)
- psycopg2-binary (ya en requirements.txt)

---

## Risks & Mitigations

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Datos corruptos en archivos | Media | Medio | Validación estricta, reporte de errores |
| Duplicados masivos | Baja | Bajo | Opción de sobrescribir o skip |
| Performance con archivos grandes | Baja | Medio | Batch inserts, índices en DB |
| Cambio en formato de exportación | Baja | Alto | Versionar lectores por formato |

---

## Metrics & Monitoring

### Métricas de Éxito
- Tasa de éxito: > 95%
- Tiempo de migración: < 2 min / 1000 propiedades
- Duplicados detectados correctamente: 100%

### Monitoreo
- Logs de migración detallados
- Reporte JSON con estadísticas
- Conteo de registros en DB pre/post migración

---

## Notes

- Considerar usar `COPY` de PostgreSQL para mejor performance con archivos grandes
- Implementar `dry_run` para testing sin afectar datos
- Mantener backup de archivos originales antes de migración
- Considerar migración incremental para datasets muy grandes

---

## Changelog

| Fecha | Cambio | Autor |
|-------|--------|-------|
| 2026-04-09 | Spec creada | Cascade |
| 2026-04-09 | Implementación completada - scripts, tests, documentación | Cascade |
