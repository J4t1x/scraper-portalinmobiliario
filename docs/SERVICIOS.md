# 🌐 Servicios Disponibles - Portal Inmobiliario Scraper

**Última actualización:** Abril 13, 2026  
**Docker Compose:** `docker-compose.yml` (v2.2)

---

## 📋 Servicios Activos

### 🎯 Core Services (Siempre activos)

| Servicio | Puerto | URL | Descripción |
|----------|--------|-----|-------------|
| **PostgreSQL** | 4420 | `postgresql://scraper:scraper123@localhost:4420/portalinmobiliario` | Base de datos principal |
| **Dashboard** | 4421 | http://localhost:4421 | Interfaz web Flask + Analytics |

### 🔧 Optional Services (Activar con profiles)

| Servicio | Puerto | URL | Profile | Descripción |
|----------|--------|-----|---------|-------------|
| **Redis** | 4422 | `redis://localhost:4422` | `cache` | Cache layer para analytics |
| **Ollama** | 4423 | http://localhost:4423 | `ai` | Servidor IA para chat analytics |
| **Adminer** | 4424 | http://localhost:4424 | `admin` | Gestión visual de PostgreSQL |

---

## 🚀 Comandos de Inicio

### Core Services (PostgreSQL + Dashboard + Redis + Ollama)
```bash
docker-compose up -d
```

### Con pgAdmin (opcional)
```bash
docker-compose --profile admin up -d
```

---

## 🔗 URLs de Acceso

### Dashboard Web
```
http://localhost:4421
```

**Credenciales por defecto:**
- Usuario: `admin`
- Password: `admin123`

**Endpoints disponibles:**
- `/` - Home (requiere login)
- `/login` - Página de login
- `/dashboard` - Dashboard principal
- `/explorer` - Explorador de archivos
- `/bi` - Business Intelligence
- `/ai` - AI Analytics Studio (requiere Ollama)
- `/scheduler` - Control del scheduler
- `/api/docs` - Documentación de API REST

### PostgreSQL
```bash
# Conexión con psql
psql -h localhost -p 4420 -U scraper -d portalinmobiliario

# Connection string
postgresql://scraper:scraper123@localhost:4420/portalinmobiliario
```

### Redis (si está activo)
```bash
# Conexión con redis-cli
redis-cli -h localhost -p 4422

# Connection string
redis://localhost:4422
```

### Ollama (si está activo)
```bash
# API REST
curl http://localhost:4423/api/tags

# Listar modelos
curl http://localhost:4423/api/tags | jq '.models[].name'

# Descargar modelo (si no está)
docker exec portalinmobiliario-ollama ollama pull qwen2.5-coder:1.5b

# Chat (ejemplo)
curl http://localhost:4423/api/generate -d '{
  "model": "qwen2.5-coder:1.5b",
  "prompt": "Hola, ¿cómo estás?",
  "stream": false
}'
```

**Nota:** La primera consulta puede tardar 30-60 segundos mientras el modelo se carga en memoria.

### Adminer (si está activo)
```
http://localhost:4424
```

**Credenciales:**
- Sistema: `PostgreSQL`
- Servidor: `postgres` (nombre del contenedor)
- Usuario: `scraper`
- Password: `scraper123`
- Base de datos: `portalinmobiliario`

---

## 📊 Verificación de Estado

### Ver contenedores activos
```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### Ver logs
```bash
# Dashboard
docker logs -f portalinmobiliario-dashboard

# PostgreSQL
docker logs -f portalinmobiliario-db

# Todos
docker-compose logs -f
```

### Healthchecks
```bash
# Dashboard
curl http://localhost:4421/

# PostgreSQL
docker exec portalinmobiliario-db pg_isready -U scraper

# Ollama (si está activo)
curl http://localhost:4423/api/tags
```

---

## 🛠️ Comandos Útiles

### Ejecutar Scraping
```bash
docker-compose run --rm scraper \
  python main.py --operacion venta --tipo departamento --max-pages 5
```

### Acceder a PostgreSQL
```bash
docker exec -it portalinmobiliario-db psql -U scraper -d portalinmobiliario
```

### Ver tablas
```bash
docker exec portalinmobiliario-db psql -U scraper -d portalinmobiliario -c "\dt"
```

### Ejecutar migraciones (si es necesario)
```bash
docker-compose run --rm scraper \
  alembic -c migrations/alembic.ini upgrade head
```

### Detener servicios
```bash
# Detener todo
docker-compose down

# Detener y eliminar volúmenes
docker-compose down -v
```

---

## 🔒 Seguridad

### Cambiar Credenciales de PostgreSQL

Editar `docker-compose.yml`:
```yaml
environment:
  - POSTGRES_USER=tu_usuario
  - POSTGRES_PASSWORD=tu_password_seguro
  - POSTGRES_DB=portalinmobiliario
```

### Cambiar Credenciales del Dashboard

Las credenciales se configuran en `app.py` o mediante variables de entorno.

---

## 📚 Documentación Adicional

- [Dockerfile](Dockerfile) - Dockerfile optimizado (v2.1)
- [Docker Compose](docker-compose.yml) - Configuración de servicios (v2.2)
- [Guía de Deployment](docs/deployment/DOCKER-V2.md) - Documentación completa
- [README Principal](README.md) - Documentación del proyecto

---

## 🐛 Troubleshooting

### Puerto 4421 ya en uso
```bash
# Ver qué proceso usa el puerto
lsof -i :4421

# Cambiar puerto en docker-compose.yml
ports:
  - "4425:5000"  # Cambiar 4421 por otro puerto
```

### Dashboard no responde
```bash
# Ver logs
docker logs portalinmobiliario-dashboard

# Reiniciar
docker restart portalinmobiliario-dashboard
```

### Base de datos sin tablas
```bash
# Ejecutar script de creación
docker exec -i portalinmobiliario-db psql -U scraper -d portalinmobiliario < migrations/schema.sql
```

---

**Nota:** Todos los puertos están configurados en la base **4420** para evitar conflictos con servicios del sistema (como AirPlay en macOS que usa el puerto 5000).
