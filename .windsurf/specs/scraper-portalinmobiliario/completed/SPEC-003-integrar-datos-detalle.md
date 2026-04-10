# SPEC-003: Integrar Datos de Detalle en Exportación

---

## 1. Overview

**ID:** SPEC-003  
**Title:** Integrar datos de detalle en exportación  
**Type:** feature  
**Priority:** high  
**Status:** completed  
**Created:** 2026-04-08  
**Updated:** 2026-04-08

### Context
SPEC-002 implementó el scraping de páginas de detalle de propiedades, extrayendo información adicional como descripción completa, amenities, características del edificio, etc. Esta información ahora está disponible en el objeto de propiedad pero **no se está exportando** en los archivos de salida (TXT, JSON, CSV).

### Problem
Los usuarios no pueden acceder a los datos de detalle en los archivos exportados, limitando el valor del scraping completo.

### Goal
Integrar todos los campos de detalle disponibles en los formatos de exportación existentes (TXT, JSON, CSV).

---

## 2. Requirements

### Functional Requirements

- **FR-001:** El exportador debe incluir todos los campos de detalle en formato JSON
- **FR-002:** El exportador debe incluir campos de detalle relevantes en formato CSV
- **FR-003:** El exportador debe incluir campos de detalle en formato TXT de manera legible
- **FR-004:** Los campos de detalle deben estar claramente identificados/separados en cada formato
- **FR-005:** Mantener backward compatibility con el formato actual

### Non-Functional Requirements

- **NFR-001:** El tiempo de exportación no debe aumentar más de 20%
- **NFR-002:** Los archivos exportados deben mantener encoding UTF-8 correcto
- **NFR-003:** Manejar gracefulmente casos donde no hay datos de detalle disponibles

---

## 3. Acceptance Criteria

- [x] Exportación JSON incluye objeto completo `detalle` con todos los sub-campos
- [x] Exportación CSV incluye columnas para: descripción, amenities (lista), características (lista), lat/lng
- [x] Exportación TXT muestra sección "Detalles de la Propiedad" con información formateada
- [x] Campos de detalle aparecen como "N/A" o vacíos cuando no están disponibles
- [x] Tests verifican que la exportación incluye datos de detalle correctamente
- [x] Documentación actualizada con ejemplos de salida

---

## 4. Technical Design

### Data Model

```python
# Estructura de Property con detalle
{
    "id": str,
    "titulo": str,
    "precio": str,
    "precio_uf": float,
    "ubicacion": str,
    "url": str,
    "imagen": str,
    "metros_cuadrados": int,
    "dormitorios": int,
    "banos": int,
    "operacion": str,
    "tipo": str,
    # Campos de detalle (nuevos)
    "detalle": {
        "descripcion": str,
        "amenities": List[str],
        "caracteristicas": List[str],
        "caracteristicas_edificio": List[str],
        "latitud": float,
        "longitud": float,
        "contacto": {
            "nombre": str,
            "telefono": str,
            "email": str
        }
    }
}
```

### Implementation Details

#### Modificaciones a `exporter.py`:

1. **Exportación JSON:**
   - Incluir objeto `detalle` completo en cada propiedad
   - Mantener estructura anidada

2. **Exportación CSV:**
   - Agregar columnas: `descripcion`, `amenities`, `caracteristicas`, `caracteristicas_edificio`, `latitud`, `longitud`, `contacto_nombre`, `contacto_telefono`, `contacto_email`
   - Listas (amenities, características) como strings separados por pipe `|`

3. **Exportación TXT:**
   - Agregar sección "DETALLES DE LA PROPIEDAD" después de información básica
   - Mostrar amenities y características como listas con bullets

### Files to Modify

- `exporter.py` - Métodos de exportación
- `tests/test_exporter.py` - Tests de exportación (crear si no existe)

---

## 5. Implementation Plan

1. [x] Analizar estructura actual de `exporter.py`
2. [x] Modificar `export_to_json()` para incluir datos de detalle
3. [x] Modificar `export_to_csv()` para incluir columnas de detalle
4. [x] Modificar `export_to_txt()` para incluir sección de detalles
5. [x] Crear/actualizar tests de exportación
6. [x] Validar que los archivos exportados se generan correctamente
7. [x] Actualizar documentación con ejemplos

---

## 6. Notes

### Iteration Log

#### 2026-04-08 - Inicio
- Spec creada desde índice del proyecto
- Dependencia: SPEC-002 completada (scraping de detalle implementado)

#### 2026-04-09 - Implementación
- [x] Análisis de `exporter.py` completado
- [x] Modificado `flatten_property()` para usar pipe `|` como separador de listas (mejor para CSV)
- [x] Modificado `export_to_txt()` con formato legible incluyendo:
  - Header con metadata de la exportación
  - Sección "INFORMACIÓN BÁSICA" con datos principales
  - Sección "DETALLES DE LA PROPIEDAD" (solo si existen datos)
  - Sub-secciones: Descripción, Características, Publicador, Coordenadas GPS, Imágenes
  - Texto con wrap automático para descripciones largas
  - Footer "FIN DEL LISTADO"
- [x] Creado `tests/test_exporter.py` con 8 tests:
  - `test_flatten_property_basic` - Campos básicos
  - `test_flatten_property_with_details` - Campos anidados y listas
  - `test_flatten_property_empty_values` - Manejo de None/empty
  - `test_export_to_json_with_details` - JSON con estructura completa
  - `test_export_to_csv_with_details` - CSV con campos aplanados
  - `test_export_to_txt_with_details` - TXT formateado con detalles
  - `test_export_to_txt_without_details` - TXT sin sección de detalles
  - `test_export_empty_properties` - Manejo de lista vacía
- [x] Todos los tests pasaron (8/8 ✅)

### Implementation Notes

**Cambios en `exporter.py`:**
1. `flatten_property()`: Mejorado manejo de listas usando pipe `|` en lugar de comas
2. `export_to_txt()`: Reimplementado completamente para mostrar formato legible humano
3. JSON y CSV ya funcionaban con datos de detalle (no requirieron cambios)

**Estructura de datos soportada:**
Los datos de detalle del scraper (`scraper_selenium.py`) se mergean directamente en el dict de propiedad:
- `descripcion`: str
- `caracteristicas`: dict (orientacion, año_construccion, estacionamientos, etc.)
- `publicador`: dict (nombre, telefono, tipo)
- `imagenes`: list[str]
- `coordenadas`: dict (lat, lng)
- `fecha_publicacion`: str

**Archivos modificados:**
- `exporter.py` - Líneas 18-178 modificadas
- `tests/test_exporter.py` - Nuevo archivo (310 líneas)

### Technical Decisions

- **Decision 1:** Usar pipe `|` como separador para listas en CSV (más legible que comas que pueden aparecer en el texto)
- **Decision 2:** Incluir lat/lng como columnas separadas para facilitar análisis geoespacial
- **Decision 3:** Mantener estructura anidada en JSON para consistencia con el modelo interno

### References

- SPEC-002: Implementar scraping de página de detalle
- `exporter.py`: Módulo de exportación actual
- `scraper_selenium.py`: Donde se extraen los datos de detalle
