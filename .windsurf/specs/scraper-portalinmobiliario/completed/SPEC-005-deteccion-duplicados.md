# SPEC-005: Detección de Duplicados

**Proyecto:** scraper-portalinmobiliario  
**Fase:** 2 - Mejoras (Sprint 2: Calidad de Datos)  
**Prioridad:** Media  
**Estimación:** 4 horas  
**Status:** completed  
**Creado:** 2026-04-09  
**Actualizado:** 2026-04-09
**Completado:** 2026-04-09

---

## 1. Contexto

### Problema
El scraper no detecta propiedades duplicadas entre ejecuciones, generando:
- Datos redundantes en exportaciones
- Procesamiento innecesario
- Análisis incorrecto de mercado

### Solución
Implementar sistema de detección de duplicados usando ID de propiedad como clave única.

### Objetivo
Detectar y marcar duplicados con <1% de falsos negativos.

---

## 2. Requirements

### Functional Requirements (FR)

**FR-001:** Mantener registro persistente de IDs scrapeados
**FR-002:** Comparar propiedades con ejecuciones anteriores
**FR-003:** Marcar duplicados con flag `is_duplicate: true`
**FR-004:** Opción CLI para incluir/excluir duplicados en export
**FR-005:** Actualizar registro tras cada ejecución exitosa
**FR-006:** Soportar reset de registro de duplicados

### Non-Functional Requirements (NFR)

**NFR-001:** Detección de duplicados en <500ms para 10,000 registros
**NFR-002:** O(1) lookup time usando set/dict
**NFR-003:** Persistencia en JSON (preparado para PostgreSQL en Fase 3)
**NFR-004:** Backward compatible (funciona sin historial)

---

## 3. Acceptance Criteria

- [x] Módulo `deduplicator.py` creado
- [x] Registro persistente de IDs en `data/scraped_ids.json`
- [x] Detección O(1) usando set/dict
- [x] Flag `is_duplicate` en propiedades
- [x] Opciones CLI: `--include-duplicates`, `--exclude-duplicates`, `--reset-duplicates`
- [x] Tests unitarios con cobertura ≥80%
- [x] Performance <500ms para 10k registros
- [x] Documentación actualizada

---

## 4. Technical Design

### Architecture
```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Property Data  │────▶│  Deduplicator    │────▶│  Marked Data   │
│                 │     │                  │     │  (is_duplicate) │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────┐
                        │ scraped_ids  │
                        │   .json      │
                        └──────────────┘
```

### Data Model

**DeduplicationRegistry:**
```python
@dataclass
class DeduplicationRegistry:
    ids: Set[str]                          # Set para O(1) lookup
    first_seen: Dict[str, str]             # ID -> fecha primera vez
    last_seen: Dict[str, str]              # ID -> fecha última vez
    metadata: Dict                         # Info de ejecuciones
```

**Persistencia JSON:**
```json
{
  "ids": ["MLC-12345678", "MLC-87654321"],
  "first_seen": {
    "MLC-12345678": "2026-04-09T10:00:00"
  },
  "last_seen": {
    "MLC-12345678": "2026-04-09T15:30:00"
  },
  "execution_count": 5,
  "total_unique": 15000
}
```

### API/Interface

```python
class Deduplicator:
    def __init__(self, registry_path: str = "data/scraped_ids.json")
    def load_registry(self) -> DeduplicationRegistry
    def save_registry(self) -> None
    def is_duplicate(self, property_id: str) -> bool
    def mark_property(self, data: Dict) -> Dict
    def add_to_registry(self, property_id: str) -> None
    def reset_registry(self) -> None
    def get_stats(self) -> Dict
```

---

## 5. Implementation Plan

### TASK-005-01: Crear estructura del módulo (30min)
- Crear `deduplicator.py` con clase `Deduplicator`
- Definir estructura de datos
- Setup de paths y persistencia

### TASK-005-02: Persistencia de IDs (45min)
- Cargar/guardar JSON en `data/scraped_ids.json`
- Manejo de archivo no existente
- Backup automático del registro
- Validación de integridad

### TASK-005-03: Lógica de detección (45min)
- Implementar `is_duplicate()` con O(1) lookup
- Marcar propiedades con flag
- Actualizar fechas first_seen/last_seen
- Optimizar memory usage con Set

### TASK-005-04: Opciones CLI (45min)
- `--include-duplicates`: Incluir en export (default)
- `--exclude-duplicates`: Filtrar antes de exportar
- `--reset-duplicates`: Limpiar registro
- `--dedup-stats`: Mostrar estadísticas

### TASK-005-05: Tests unitarios (60min)
- Tests de detección básica
- Tests de persistencia
- Tests de CLI flags
- Tests de performance (10k registros)
- Fixtures con diferentes escenarios

### TASK-005-06: Documentación (15min)
- Docstrings
- Actualizar README
- Ejemplos de uso

---

## 6. Testing Strategy

### Test Cases

**TC-001:** ID nuevo no está en registro → is_duplicate=False
**TC-002:** ID existente está en registro → is_duplicate=True
**TC-003:** Persistencia guarda y carga correctamente
**TC-004:** Reset limpia el registro completamente
**TC-005:** `--exclude-duplicates` filtra antes de exportar
**TC-006:** Performance con 10k IDs <500ms
**TC-007:** File corrupto se maneja gracefully

### Performance Tests
- Crear 10,000 IDs aleatorios
- Medir tiempo de lookup
- Verificar O(1) behavior

---

## 7. Evidence

### Implementation Completed
```
✅ TASK-005-01: Módulo deduplicator.py creado
✅ TASK-005-02: Persistencia JSON implementada
✅ TASK-005-03: Lógica O(1) con Set implementada
✅ TASK-005-04: Opciones CLI integradas en main.py
✅ TASK-005-05: Tests unitarios (25 tests, 100% pasados)
✅ TASK-005-06: README.md actualizado
```

### Test Results
```
Ran 25 tests in 0.023s
OK
```

### Performance Benchmark
- 10,000 IDs lookup: <50ms (vs requerimiento de <500ms)
- O(1) behavior verified: ~0.00001s per lookup

### Files Created/Modified
- `deduplicator.py` (nuevo, 284 líneas)
- `main.py` (modificado, integración CLI)
- `tests/test_deduplicator.py` (nuevo, 25 tests)
- `README.md` (documentación actualizada)

## 8. Notes

### Decisions
- Usar Set en lugar de List para O(1) lookup
- JSON para persistencia simple (preparado para PostgreSQL)
- Flag `is_duplicate` permite análisis posterior
- Default: incluir duplicados (no perder datos)
- Backup automático del registro antes de guardar
- Manejo graceful de archivo corrupto (.corrupt backup)

### Implementation Highlights
- DeduplicationRegistry dataclass con metadatos completos
- Extracción de ID desde campo 'id' o URL
- CLI flags: --include-duplicates (default), --exclude-duplicates, --reset-duplicates
- Stats: --dedup-stats para ver registro sin ejecutar scraper
- 25 tests unitarios + performance tests

### Dependencies
- SPEC-004 completada (validación de ID previo a deduplicación)
- SPEC-003 completada (exporters manejan flag is_duplicate)

---

## 8. Changelog

| Fecha | Autor | Cambio |
|-------|-------|--------|
| 2026-04-09 | Cascade | Spec creada desde PRD Fase 2 |
