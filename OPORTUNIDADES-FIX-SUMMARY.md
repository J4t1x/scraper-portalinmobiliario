# Correcciones Módulo "Oportunidades del día"

## Fecha: 14 Abril 2026

## Problemas Identificados y Corregidos

### 1. ✅ Campo incorrecto en queries de BD
**Problema:** El código usaba `superficie_total` pero el modelo Property tiene `superficie_util`

**Archivos modificados:**
- `db_loader.py` - Función `get_investment_opportunities()`

**Cambios:**
- Reemplazado `Property.superficie_total` → `Property.superficie_util` en todas las queries
- Agregado alias `superficie_total` en el dict de retorno para compatibilidad con templates

### 2. ✅ Campos faltantes en serialización
**Problema:** Los campos `dormitorios`, `banos`, `superficie_util` no se incluían en `_property_to_dict()`

**Archivos modificados:**
- `db_loader.py` - Funciones `_property_to_dict()` y `_property_to_dict_detailed()`

**Cambios:**
- Agregados campos de analytics: `superficie_util`, `dormitorios`, `banos`, `precio_m2`
- Agregado alias `superficie_total` para compatibilidad
- Uso de `getattr()` para campos opcionales (evita errores si columna no existe)

### 3. ✅ Errores tipográficos en template
**Problema:** Errores de ortografía en el HTML que afectaban la UX

**Archivos modificados:**
- `templates/dashboard/home.html`

**Cambios:**
- "Precio pro fulia" → "Valor total mercado"
- "Precio por inm²" → "Precio por m²"
- "Más vazcos 🏠 caras" → "Comunas más caras"
- "Comunas bás baratas" → "Comunas más baratas"
- "Precio /m" → "Precio/m²"
- "Variación ⬆" → "Variación"
- Corregido formato de count: `${commune.count}^` → `${commune.count} props`
- Ajustados colores de iconos (arrow-up rojo para caras, arrow-down verde para baratas)

### 4. ✅ Sistema de fallback híbrido (BD + JSON)
**Problema:** Si la BD estaba vacía, el módulo no mostraba datos

**Archivos modificados:**
- `dashboard/routes.py` - Función `api_investment_opportunities()`

**Cambios:**
- Implementado sistema de detección de datos en BD
- Si BD está vacía, carga automática desde archivos JSON
- Funciones auxiliares agregadas:
  - `_get_opportunities_from_json()` - Procesa JSON para generar oportunidades
  - `_extract_superficie_from_atributos()` - Extrae m² de string atributos
  - `_extract_price_clp_from_json()` - Extrae precio CLP (ignora UF)
  - `_extract_comuna_from_ubicacion()` - Extrae comuna de ubicación
  - `_json_prop_to_dict()` - Convierte propiedad JSON a formato estándar
  - `_extract_number_from_atributos()` - Extrae dormitorios/baños
- Agregado campo `data_source` en respuesta ('database', 'json', o 'empty')
- Mensaje de alerta cuando no hay datos disponibles

### 5. ✅ Imports faltantes
**Archivos modificados:**
- `dashboard/routes.py`

**Cambios:**
- Agregado `import re` para expresiones regulares
- Agregado `from typing import Dict, Optional` para type hints

## Estado Actual

### ✅ Completado
- Correcciones de código en `db_loader.py`
- Correcciones de template en `home.html`
- Sistema de fallback híbrido implementado
- Script de prueba creado (`test_opportunities.py`)

### ⚠️ Pendiente
- **Migración de BD:** La base de datos actual no tiene todas las columnas del modelo Property
  - Falta ejecutar migraciones o la BD está desactualizada
  - Columnas faltantes detectadas: `portal_id`, `precio_moneda`, `precio_original`, etc.
  
### 🔧 Solución Recomendada

**Opción 1: Ejecutar migraciones (Recomendado)**
```bash
cd /Users/ja/Documents/GitHub/scraper-portalinmobiliario
source venv/bin/activate
alembic upgrade head
```

**Opción 2: Usar solo JSON (Temporal)**
El sistema ya está preparado para usar JSON como fallback automático si la BD está vacía o tiene errores.

**Opción 3: Recrear BD desde cero**
```bash
# Backup de datos actuales (si existen)
pg_dump -h localhost -U postgres scraper_db > backup.sql

# Recrear esquema
alembic downgrade base
alembic upgrade head

# Migrar datos desde JSON
python scripts/migrate_to_postgres.py output/
```

## Funcionalidad del Módulo

El módulo "Oportunidades del día" ahora:

1. **Carga datos desde BD** (si está disponible y actualizada)
2. **Fallback automático a JSON** (si BD está vacía o con errores)
3. **Calcula oportunidades** basado en precio/m² bajo promedio de mercado
4. **Muestra estadísticas** de mercado y comunas
5. **Genera alertas** automáticas
6. **Presenta datos** en interfaz visual atractiva

## Próximos Pasos

1. Ejecutar migraciones de Alembic para actualizar esquema de BD
2. Ejecutar scraper para poblar BD con datos frescos
3. Verificar que el módulo funciona correctamente con datos reales
4. Opcional: Migrar datos históricos desde JSON a BD

## Testing

Para probar el módulo:

```bash
# Test completo (BD + JSON)
source venv/bin/activate
python test_opportunities.py

# Levantar dashboard
python app.py

# Acceder a: http://localhost:5000/dashboard
```

## Notas Técnicas

- El sistema usa `getattr()` para acceder a campos opcionales, evitando errores si faltan columnas
- El alias `superficie_total` = `superficie_util` mantiene compatibilidad con código existente
- Las expresiones regulares extraen datos de strings no estructurados (atributos, ubicación)
- El scoring de oportunidades usa fórmula: `score = 100 - (precio_m2_propiedad / precio_m2_mercado * 100)`
- Descuento considerado "oportunidad": < 85% del promedio de mercado
