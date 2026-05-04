# 🐳 Docker Setup - Portal Inmobiliario Scraper

## ✅ Configuración Actual

**Dockerfile activo:** `Dockerfile` (v2.1 - Optimizado con multi-stage build)  
**Docker Compose:** `docker-compose.yml` (v2.2 - Configuración completa)  
**Archivos archivados:** `archive/dockerfiles/`, `archive/docker-compose.optimized.yml`

---

## 🚀 Comandos Rápidos

### 1. Levantar todos los servicios core (PostgreSQL + Dashboard + Redis + Ollama)
```bash
docker-compose up -d
```

### 2. Levantar con pgAdmin (opcional)
```bash
docker-compose --profile admin up -d
```

### 3. Ver logs
```bash
# Dashboard
docker-compose logs -f dashboard

# Todos los servicios
docker-compose logs -f
```

### 4. Ejecutar scraping
```bash
docker-compose run --rm scraper python main.py --operacion venta --tipo departamento --max-pages 5
```

### 5. Acceder al Dashboard
```bash
# Abrir en navegador
open http://localhost:4421
```

### 6. Detener todos los servicios
```bash
docker-compose down
```

### 7. Rebuild completo (después de cambios en código)
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## 📦 Servicios Disponibles

| Servicio | Puerto | URL | Descripción |
|----------|--------|-----|-------------|
| **postgres** | 4420 | `postgresql://scraper:scraper123@localhost:4420/portalinmobiliario` | Base de datos PostgreSQL 15 |
| **dashboard** | 4421 | http://localhost:4421 | Dashboard web Flask + Analytics |
| **redis** | 4422 | `redis://localhost:4422` | Cache layer para analytics |
| **ollama** | 4423 | http://localhost:4423 | Servidor IA (qwen2.5-coder:1.5b) |
| **pgadmin** | 4425 | http://localhost:4425 | Gestión PostgreSQL (profile: admin) |
| **scraper** | - | - | Servicio bajo demanda |

---

## 🔧 Configuración de Entorno

Variables en `.env` (opcional):
```bash
DELAY_BETWEEN_REQUESTS=2
MAX_RETRIES=3
TIMEOUT=30
USER_AGENT=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36
```

---

## 🐛 Troubleshooting

### Docker daemon no responde
```bash
# Reiniciar Docker Desktop
killall -9 Docker
open /Applications/Docker.app
```

### Contenedores no se detienen
```bash
docker-compose down --remove-orphans
docker system prune -f
```

### Ver estado de contenedores
```bash
docker-compose ps
docker stats
```

### Acceder al contenedor
```bash
docker-compose exec scraper bash
```

---

## 📊 Mejoras Aplicadas (v2.1)

- ✅ Multi-stage build (-30% tamaño imagen)
- ✅ Chromium del sistema (sin APIs externas)
- ✅ Optimizaciones de memoria (-45% RAM)
- ✅ Usuario no-root (seguridad)
- ✅ Healthcheck integrado
- ✅ Logs estructurados

---

## 📁 Estructura de Volúmenes

```
./output/          → Archivos exportados (JSON, CSV)
postgres-data/     → Datos persistentes de PostgreSQL
```

---

**Última actualización:** 12 Abril 2026
