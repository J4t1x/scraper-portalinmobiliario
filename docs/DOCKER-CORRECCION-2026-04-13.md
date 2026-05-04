# 🔧 Corrección Docker - 13 Abril 2026

## ⚠️ Problema Identificado

La limpieza anterior (12 Abril) **eliminó servicios críticos** del proyecto, dejándolo no funcional:

### Servicios Eliminados por Error
- ❌ **Dashboard** (puerto 4421) - Interfaz web principal
- ❌ **Redis** (puerto 4422) - Cache layer
- ❌ **Ollama** (puerto 4423) - Servidor IA para analytics
- ❌ **pgAdmin** (puerto 4425) - Gestión de BD (opcional)

### Causa del Error
Se asumió incorrectamente que el proyecto usaba una configuración simple (solo scraper + postgres), cuando en realidad usa una **arquitectura completa** con múltiples servicios.

---

## ✅ Corrección Aplicada

### 1. Restaurado `docker-compose.yml` Completo

**Fuente:** `archive/docker-compose.v2.yml`  
**Destino:** `docker-compose.yml` (archivo principal)

**Servicios restaurados:**
```yaml
services:
  postgres:       # Puerto 4420 - Base de datos
  redis:          # Puerto 4422 - Cache
  ollama:         # Puerto 4423 - IA
  ollama-setup:   # Setup automático del modelo
  scraper:        # Bajo demanda
  dashboard:      # Puerto 4421 - Web UI
  pgadmin:        # Puerto 4425 - Admin (profile)
```

### 2. Corregidas Referencias de Dockerfile

**Cambio:** `Dockerfile.v2` → `Dockerfile`

**Archivos modificados:**
- `docker-compose.yml` (servicios `scraper` y `dashboard`)

**Razón:** El proyecto solo tiene `Dockerfile` (v2.1), no existe `Dockerfile.v2`

### 3. Actualizada Documentación

**Archivo:** `docs/DOCKER-SETUP.md`

**Cambios:**
- Tabla de servicios completa (6 servicios)
- Comandos actualizados con puertos correctos (base 4420)
- Instrucciones para profiles (admin)
- URLs de acceso a todos los servicios

---

## 🏗️ Arquitectura Actual

### Servicios Core (Siempre Activos)
```
┌─────────────────────────────────────────────┐
│  PostgreSQL (4420)                          │
│  ├─ Base de datos principal                │
│  └─ Persistencia de propiedades            │
├─────────────────────────────────────────────┤
│  Redis (4422)                               │
│  ├─ Cache layer                             │
│  └─ Optimización de queries                │
├─────────────────────────────────────────────┤
│  Ollama (4423)                              │
│  ├─ Servidor IA (qwen2.5-coder:1.5b)       │
│  └─ Chat analytics                          │
├─────────────────────────────────────────────┤
│  Dashboard (4421)                           │
│  ├─ Flask + TailwindCSS                     │
│  ├─ BI + Analytics                          │
│  ├─ AI Studio                               │
│  └─ Control de scraping                     │
└─────────────────────────────────────────────┘
```

### Servicios Bajo Demanda
```
┌─────────────────────────────────────────────┐
│  Scraper                                    │
│  ├─ Python + Selenium + Chromium           │
│  └─ Ejecutar con: docker-compose run       │
└─────────────────────────────────────────────┘
```

### Servicios Opcionales (Profile: admin)
```
┌─────────────────────────────────────────────┐
│  pgAdmin (4425)                             │
│  └─ Gestión visual de PostgreSQL           │
└─────────────────────────────────────────────┘
```

---

## 🚀 Comandos Actualizados

### Levantar Servicios Core
```bash
docker-compose up -d
```

**Servicios levantados:**
- PostgreSQL (4420)
- Redis (4422)
- Ollama (4423) + setup automático
- Dashboard (4421)

### Levantar con pgAdmin
```bash
docker-compose --profile admin up -d
```

### Ejecutar Scraping
```bash
docker-compose run --rm scraper python main.py --operacion venta --tipo departamento --max-pages 5
```

### Acceder al Dashboard
```bash
open http://localhost:4421
```

**Credenciales:**
- Usuario: `admin`
- Password: `admin123`

### Ver Logs
```bash
# Dashboard
docker-compose logs -f dashboard

# Todos
docker-compose logs -f
```

### Detener Todo
```bash
docker-compose down
```

---

## 📊 Verificación

### 1. Verificar Servicios Activos
```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

**Esperado:**
```
NAMES                           STATUS          PORTS
portalinmobiliario-dashboard    Up X minutes    0.0.0.0:4421->5000/tcp
portalinmobiliario-ollama       Up X minutes    0.0.0.0:4423->11434/tcp
portalinmobiliario-redis        Up X minutes    0.0.0.0:4422->6379/tcp
portalinmobiliario-db           Up X minutes    0.0.0.0:4420->5432/tcp
```

### 2. Verificar Dashboard
```bash
curl http://localhost:4421
```

**Esperado:** HTML del login page

### 3. Verificar Ollama
```bash
curl http://localhost:4423/api/tags
```

**Esperado:** JSON con modelos disponibles

### 4. Verificar PostgreSQL
```bash
docker exec portalinmobiliario-db pg_isready -U scraper
```

**Esperado:** `accepting connections`

---

## 📁 Estructura de Archivos Actual

### Archivos Activos (Raíz)
```
Dockerfile              ← v2.1 Optimizado (multi-stage, Chromium)
docker-compose.yml      ← v2.2 Configuración completa (6 servicios)
```

### Archivos Archivados
```
archive/
├── docker-compose.v2.yml           ← Backup del original
├── docker-compose.optimized.yml    ← Versión con profiles complejos
└── dockerfiles/
    ├── Dockerfile.mvp              ← Contenedor único MVP
    ├── Dockerfile.old              ← Versión antigua
    └── Dockerfile.optimized        ← Versión optimizada anterior
```

---

## 🔍 Lecciones Aprendidas

1. **Siempre revisar documentación completa** antes de hacer cambios
2. **Verificar servicios activos** en producción/desarrollo
3. **Consultar SERVICIOS.md** para arquitectura del proyecto
4. **No asumir configuración simple** sin validar

---

## 📚 Referencias

- `docs/SERVICIOS.md` - Lista completa de servicios y URLs
- `README.md` - Documentación principal del proyecto
- `docker-compose.yml` - Configuración de servicios
- `Dockerfile` - Imagen optimizada del scraper

---

**Fecha:** 13 Abril 2026  
**Autor:** Cascade AI  
**Motivo:** Corrección de eliminación errónea de servicios críticos  
**Estado:** ✅ Proyecto restaurado y funcional
