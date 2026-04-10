# SPEC-004: Sistema de Validación de Datos

**Proyecto:** scraper-portalinmobiliario  
**Fase:** 2 - Mejoras (Sprint 2: Calidad de Datos)  
**Prioridad:** Alta  
**Estimación:** 6 horas  
**Status:** in-progress → completed  
**Creado:** 2026-04-09  
**Actualizado:** 2026-04-09

---

## 1. Contexto

### Problema
El scraper actual extrae datos sin validar su calidad, lo que puede resultar en:
- IDs de propiedad mal formateados
- Precios con formatos inconsistentes
- Ubicaciones vacías o mal escritas
- Atributos numéricos inválidos

### Solución
Implementar un sistema de validación y sanitización que verifique la calidad de los datos antes de exportar.

### Objetivo
Garantizar que ≥95% de las propiedades tengan datos completos y válidos.

---

## 2. Requirements

### Functional Requirements (FR)

**FR-001:** Validar formato de ID de propiedad (MLC-XXXXXXXX)
**FR-002:** Validar formato de precio (UF o $ con valores numéricos)
**FR-003:** Validar que ubicación no esté vacía
**FR-004:** Validar atributos numéricos (dormitorios, baños, m²)  
**FR-005:** Validar URLs de propiedad
**FR-006:** Validar tipo y operación contra valores permitidos
**FR-007:** Sanitizar espacios en blanco extras
**FR-008:** Normalizar formatos de precio
**FR-009:** Estandarizar nombres de comunas
**FR-010:** Convertir tipos de datos automáticamente

### Non-Functional Requirements (NFR)

**NFR-001:** Validación debe ejecutarse en <100ms por propiedad
**NFR-002:** Validación no debe bloquear export (warnings en lugar de errores)
**NFR-003:** Código modular y testeable
**NFR-004:** Documentación inline (docstrings)

---

## 3. Acceptance Criteria

- [ ] Módulo `validator.py` creado con validadores por campo
- [ ] Validación de ID con regex MLC-\d{8,}
- [ ] Validación de precio soporta UF y $
- [ ] Sanitización de espacios y normalización
- [ ] Estandarización de comunas chilenas
- [ ] Integración con flujo de scraping
- [ ] Tests unitarios con cobertura ≥80%
- [ ] Validación ejecuta en <100ms por propiedad
- [ ] Warnings en lugar de errores bloqueantes

---

## 4. Technical Design

### Architecture
```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Raw Property   │────▶│  Validator   │────▶│ Validated Prop  │
│     Data        │     │              │     │   (or None)     │
└─────────────────┘     └──────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────┐
                        │  Warnings    │
                        │   Log        │
                        └──────────────┘
```

### Data Model

**ValidationResult:**
```python
@dataclass
class ValidationResult:
    is_valid: bool
    property_data: Optional[Dict]
    warnings: List[str]
    errors: List[str]
```

### API/Interface

```python
class DataValidator:
    def validate_property(self, data: Dict) -> ValidationResult
    def validate_id(self, property_id: str) -> bool
    def validate_price(self, price: str) -> Tuple[bool, float, str]
    def validate_location(self, location: str) -> Tuple[bool, str]
    def validate_attributes(self, attrs: Dict) -> Tuple[bool, Dict]
    def sanitize_data(self, data: Dict) -> Dict
```

---

## 5. Implementation Plan

### TASK-004-01: Crear estructura del módulo (30min) ✅
- Crear `validator.py` con clase `DataValidator`
- Definir `ValidationResult` dataclass
- Setup de logger para warnings

### TASK-004-02: Validadores por campo (90min) ✅
- `validate_id()`: Regex MLC-\d{8,}
- `validate_price()`: Parse UF y $, convertir a float
- `validate_location()`: No vacío, normalizar texto
- `validate_attributes()`: Dormitorios, baños, m² como números
- `validate_url()`: URL válida

### TASK-004-03: Sanitización (60min) ✅
- `sanitize_string()`: Trim espacios, normalizar unicode
- `sanitize_price()`: Quitar símbolos, convertir a número
- `sanitize_location()`: Title case, abreviaturas
- `sanitize_attributes()`: Convertir strings a int/float

### TASK-004-04: Integración con scraper (60min) ✅
- Modificar `scraper_selenium.py` para validar cada propiedad
- Agregar warnings a logs
- Fallback a datos básicos si validación falla

### TASK-004-05: Tests unitarios (90min) ✅
- Tests de cada validador individual (5 tests incluidos en validator.py)
- Tests de integración
- Fixtures con datos válidos e inválidos
- Medir tiempo de ejecución

### TASK-004-06: Documentación (30min)
- Docstrings en todas las funciones
- Actualizar `docs/specs/`
- README con ejemplos de uso

---

## 6. Testing Strategy

### Test Cases

**TC-001:** Validar ID válido MLC-12345678 → True
**TC-002:** Validar ID inválido ABC-123 → False
**TC-003:** Validar precio "UF 5.500" → (True, 5500.0, "UF")
**TC-004:** Validar precio "$ 123.456.789" → (True, 123456789.0, "CLP")
**TC-005:** Validar ubicación vacía → (False, None)
**TC-006:** Validar ubicación "Las Condes" → (True, "Las Condes")
**TC-007:** Sanitizar "  Las  Condes  " → "Las Condes"
**TC-008:** Sanitizar precio "$150.000.000" → 150000000.0

### Performance Tests
- Validar 1000 propiedades en <100s
- Memory usage constante

---

## 7. Notes

### Decisions
- Usar warnings en lugar de excepciones para no bloquear flujo
- Cache de validaciones de comunas para performance
- Normalizar UF a float, CLP a int

### Dependencies
- SPEC-002 completada (estructura de datos de propiedad definida)
- SPEC-003 completada (exporters listos para recibir datos validados)

---

## 8. Changelog

| Fecha | Autor | Cambio |
|-------|-------|--------|
| 2026-04-09 | Cascade | Spec creada desde PRD Fase 2 |
| 2026-04-09 23:45 | Cascade | Implementación completada - módulo validator.py con todas las validaciones e integración con scraper |
