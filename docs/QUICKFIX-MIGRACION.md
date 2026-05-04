# Quick Fix - Migración PostgreSQL

## 🔴 Problemas Encontrados y Solucionados

### 1. ❌ `No 'script_location' key found in configuration`

**Causa:** Faltaba el archivo `alembic.ini`

**Solución:** ✅ Creado `alembic.ini` con configuración correcta

### 2. ❌ `operator does not exist: character varying = integer`

**Causa:** El campo `opportunities.property_id` era `VARCHAR(255)` pero debía ser `INTEGER` para hacer JOIN con `properties.id`

**Solución:** ✅ Creada migración `005_fix_opportunity_property_id.py` para corregir el tipo

### 3. ❌ `FATAL: database "scraper" does not exist`

**Causa:** El healthcheck de PostgreSQL en `docker-compose.v2.yml` usaba `pg_isready -U scraper` sin especificar la base de datos. Por defecto intenta conectarse a una BD con el mismo nombre del usuario (`scraper`), pero la BD se llama `portalinmobiliario`.

**Solución:** ✅ Corregido healthcheck en `docker-compose.yml` y `docker-compose.v2.yml`:
```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U scraper -d portalinmobiliario"]
```

## 🚀 Ejecutar Migración Corregida

```bash
# Detener contenedores actuales
docker-compose -f docker-compose.v2.yml down

# Ejecutar migración corregida
./scripts/migrate_to_postgresql.sh
```

## 📋 Archivos Creados/Modificados

### Nuevos:
- ✅ `alembic.ini` - Configuración de Alembic
- ✅ `migrations/versions/20260412_1945_005_fix_opportunity_property_id.py` - Fix tipo de dato
- ✅ `scripts/restart_containers.sh` - Script para reiniciar contenedores

### Modificados:
- ✅ `models/opportunity.py` - Cambio de `String(255)` a `Integer` en `property_id`
- ✅ `scripts/migrate_to_postgresql.sh` - Verificación de `alembic.ini`
- ✅ `docker-compose.yml` - Healthcheck corregido con `-d portalinmobiliario`
- ✅ `docker-compose.v2.yml` - Healthcheck corregido con `-d portalinmobiliario`

## ✅ Verificación

Después de ejecutar la migración, verificar:

```bash
# 1. Ver estado de Alembic
docker-compose -f docker-compose.v2.yml run --rm scraper alembic current

# 2. Ver tablas creadas
docker-compose -f docker-compose.v2.yml exec postgres \
  psql -U scraper -d portalinmobiliario -c "\dt"

# 3. Verificar estructura de opportunities
docker-compose -f docker-compose.v2.yml exec postgres \
  psql -U scraper -d portalinmobiliario -c "\d opportunities"
```

## 🎯 Resultado Esperado

```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade 003_add_opportunities -> 004_add_scraper_executions
INFO  [alembic.runtime.migration] Running upgrade 004_add_scraper_executions -> 005_fix_opportunity_property_id
```

Tablas esperadas:
- `properties`
- `features`
- `images`
- `publishers`
- `opportunities` ← `property_id` ahora es INTEGER
- `analytics_cache`
- `scheduler_executions`
- `scheduler_state`
- `scraper_executions` ← NUEVA
- `scraper_logs` ← NUEVA
- `alembic_version`

## 🔄 Si Hay Problemas

### Resetear base de datos completamente:

```bash
# ADVERTENCIA: Esto borra TODOS los datos

# 1. Detener contenedores
docker-compose -f docker-compose.v2.yml down

# 2. Eliminar volumen de PostgreSQL
docker volume rm scraper-portalinmobiliario_postgres-data

# 3. Volver a ejecutar migración
./scripts/migrate_to_postgresql.sh
```

## 📝 Notas

- El error de `database "scraper" does not exist` es normal, el contenedor usa `portalinmobiliario` como nombre de BD
- La migración 005 usa `postgresql_using='property_id::integer'` para convertir valores existentes
- Si hay datos en `opportunities`, asegúrate que `property_id` contenga solo números antes de migrar
