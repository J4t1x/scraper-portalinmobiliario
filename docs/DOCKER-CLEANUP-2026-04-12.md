# 🧹 Limpieza Docker - 12 Abril 2026

## Problema Identificado

El proyecto tenía múltiples versiones de archivos Docker desactualizados y servicios obsoletos:

- ❌ `docker-compose.yml` contenía servicio **adminer** (obsoleto)
- ❌ `docker-compose.optimized.yml` con configuración compleja no utilizada
- ❌ Documentación desactualizada con referencias a adminer
- ❌ Múltiples Dockerfiles archivados sin organización clara

## Cambios Realizados

### 1. ✅ Corregido `docker-compose.yml`
**Archivo:** `/docker-compose.yml`

**Cambios:**
- Eliminado servicio `adminer` (puerto 8080)
- Configuración simplificada con solo 2 servicios:
  - `scraper` - Scraper principal con Chromium
  - `postgres` - Base de datos PostgreSQL 15

**Servicios activos:**
```yaml
services:
  scraper:
    build: .
    depends_on: postgres
    
  postgres:
    image: postgres:15-alpine
    ports: ["5432:5432"]
```

### 2. ✅ Archivado `docker-compose.optimized.yml`
**Acción:** Movido a `archive/docker-compose.optimized.yml`

**Razón:** Configuración con profiles (dashboard, ai, redis-standalone) no se usa en desarrollo actual.

### 3. ✅ Actualizado `docs/DOCKER-SETUP.md`
**Cambios:**
- Eliminada referencia a adminer del listado de servicios
- Tabla de servicios actualizada (solo scraper + postgres)

### 4. ✅ Estructura de Archivos Docker Organizada

**Archivos activos (raíz del proyecto):**
```
Dockerfile              ← v2.1 Optimizado (multi-stage, Chromium del sistema)
docker-compose.yml      ← Configuración simple (scraper + postgres)
```

**Archivos archivados:**
```
archive/
├── docker-compose.v2.yml           ← Versión anterior con todos los servicios
├── docker-compose.optimized.yml    ← Versión con profiles (movido hoy)
└── dockerfiles/
    ├── Dockerfile.mvp              ← Contenedor único MVP
    ├── Dockerfile.old              ← Versión antigua
    └── Dockerfile.optimized        ← Versión optimizada anterior
```

## Configuración Actual (Simplificada)

### Servicios Activos
1. **scraper** - Python 3.11 + Selenium + Chromium
2. **postgres** - PostgreSQL 15-alpine

### Comandos Principales
```bash
# Levantar servicios
docker-compose up -d

# Ejecutar scraping
docker-compose run --rm scraper python main.py --full

# Ver logs
docker-compose logs -f scraper

# Detener servicios
docker-compose down
```

### Puertos Expuestos
- `5432` - PostgreSQL

### Variables de Entorno
```bash
DATABASE_URL=postgresql://scraper:scraper123@postgres:5432/portalinmobiliario
DELAY_BETWEEN_REQUESTS=2
MAX_RETRIES=3
TIMEOUT=30
```

## Próximos Pasos

- [ ] Validar que `docker-compose up` funcione correctamente
- [ ] Ejecutar prueba de scraping con la configuración limpia
- [ ] Considerar eliminar archivos en `archive/dockerfiles/` si no se usan

## Notas

- **Dockerfile activo:** v2.1 con multi-stage build y Chromium del sistema
- **Configuración:** Simplificada para desarrollo local
- **Adminer eliminado:** Se puede usar `psql` o herramientas externas (DBeaver, pgAdmin desktop)
- **Versiones archivadas:** Mantenidas en `archive/` por referencia histórica

---

**Fecha:** 12 Abril 2026  
**Autor:** Cascade AI  
**Motivo:** Limpieza de archivos Docker obsoletos y servicios no utilizados
