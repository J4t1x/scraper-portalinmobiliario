# PRD: Optimización de Contenedor Docker MVP

**Proyecto:** Portal Inmobiliario Scraper  
**Versión:** 2.0  
**Fecha:** Abril 11, 2026  
**Autor:** Equipo de Infraestructura  
**Estado:** 🚧 Pendiente de Aprobación

---

## 📋 Resumen Ejecutivo

### Problema
El contenedor Docker MVP actual (`Dockerfile.mvp`) consume **2.2 GB de RAM en idle** y **2.8 GB durante scraping**, con una imagen de **2.2 GB** que tarda **8-10 minutos** en construirse. Esto resulta en:

- **Costos elevados:** $12/mes en Railway para 4GB RAM + 2 vCPUs
- **Despliegues lentos:** 10+ minutos por deploy
- **Recursos desperdiciados:** Componentes cargados que no siempre se usan (Ollama)
- **Escalabilidad limitada:** Imposible correr múltiples instancias

### Solución Propuesta
Implementar **11 optimizaciones críticas** que reducirán:

- ✅ **45% el tamaño de la imagen** (2.2 GB → 1.2 GB)
- ✅ **45% el consumo de RAM** (2.2 GB → 1.2 GB idle)
- ✅ **50% el tiempo de build** (10 min → 5 min)
- ✅ **50% los costos de hosting** ($12/mes → $6/mes)

### Impacto en el Negocio
- **Ahorro anual:** $72 USD
- **Tiempo de deploy:** -5 minutos por despliegue
- **Capacidad:** 2x más instancias con el mismo presupuesto
- **Experiencia de usuario:** Respuestas 75% más rápidas (800ms → 200ms)

---

## 🎯 Objetivos y Métricas de Éxito

### Objetivos Principales

| # | Objetivo | Métrica Actual | Meta | Prioridad |
|---|----------|----------------|------|-----------|
| 1 | Reducir tamaño de imagen | 2.2 GB | ≤ 1.2 GB | 🔴 Alta |
| 2 | Reducir RAM en idle | 2.2 GB | ≤ 1.2 GB | 🔴 Alta |
| 3 | Reducir RAM en scraping | 2.8 GB | ≤ 1.8 GB | 🟡 Media |
| 4 | Reducir tiempo de build | 10 min | ≤ 5 min | 🔴 Alta |
| 5 | Reducir tiempo de startup | 40s | ≤ 15s | 🟡 Media |
| 6 | Mejorar response time | 800ms | ≤ 200ms | 🟢 Baja |
| 7 | Reducir costos mensuales | $12 | ≤ $6 | 🔴 Alta |

### KPIs de Éxito

```yaml
Criterios de Aceptación:
  - Imagen Docker < 1.5 GB
  - RAM idle < 1.5 GB
  - Build time < 6 minutos
  - Startup time < 20 segundos
  - Response time promedio < 300ms
  - Costo mensual Railway < $8
  - 100% de tests pasando
  - 0 regresiones funcionales
```

---

## 🏗️ Arquitectura Propuesta

### Arquitectura Actual (Monolítica)

```
┌─────────────────────────────────────────────────────┐
│         CONTENEDOR ÚNICO (2.2 GB)                   │
│                                                     │
│  PostgreSQL (300MB) + Ollama (1.5GB) +             │
│  Chrome (500MB) + Flask (300MB) +                  │
│  Supervisor (50MB) + Python (150MB)                │
│                                                     │
│  SIEMPRE ACTIVOS (incluso si no se usan)           │
└─────────────────────────────────────────────────────┘
```

### Arquitectura Optimizada (Modular)

```
┌─────────────────────────────────────────────────────┐
│         IMAGEN BASE OPTIMIZADA (600 MB)             │
│  Python 3.11-alpine + Chromium + PostgreSQL         │
│  Multi-stage build + Lazy loading                  │
└─────────────────────────────────────────────────────┘
                      ↓
    ┌─────────────────┴─────────────────┐
    ↓                                   ↓
┌─────────────────┐           ┌─────────────────┐
│  CORE SERVICE   │           │ OPTIONAL SERVICES│
│  (1.2 GB RAM)   │           │  (bajo demanda)  │
│                 │           │                  │
│  - Scraper      │           │  - Dashboard     │
│  - PostgreSQL   │           │  - Ollama IA     │
│  - Redis Cache  │           │  - Analytics     │
└─────────────────┘           └─────────────────┘
```

---

## 🔧 Especificaciones Técnicas

### 1. Multi-stage Build

**Problema:** Imagen incluye dependencias de compilación innecesarias  
**Solución:** Separar build de runtime

```dockerfile
# Stage 1: Builder (temporal)
FROM python:3.11-alpine as builder
RUN apk add --no-cache gcc musl-dev postgresql-dev
COPY requirements.txt .
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install -r requirements.txt

# Stage 2: Runtime (final)
FROM python:3.11-alpine
COPY --from=builder /opt/venv /opt/venv
# Solo runtime dependencies
RUN apk add --no-cache postgresql15 chromium
```

**Impacto:**
- Tamaño: -500 MB
- Build time: -30%
- Seguridad: Menos superficie de ataque

---

### 2. Chromium en vez de Google Chrome

**Problema:** Chrome pesa 500 MB  
**Solución:** Usar Chromium (300 MB) con misma funcionalidad

```dockerfile
# Antes
RUN wget google-chrome-stable  # 500 MB

# Después
RUN apk add --no-cache chromium chromium-chromedriver  # 300 MB
```

**Cambios en código:**
```python
# scraper_selenium.py
options = webdriver.ChromeOptions()
options.binary_location = '/usr/bin/chromium'  # Nueva ubicación
```

**Impacto:**
- Tamaño: -200 MB
- Instalación: 3x más rápida
- Compatibilidad: 100% (mismo motor Blink)

---

### 3. Alpine Linux Base

**Problema:** Debian slim pesa 150 MB  
**Solución:** Alpine Linux pesa 50 MB

```dockerfile
# Antes
FROM python:3.11-slim  # 150 MB base

# Después
FROM python:3.11-alpine  # 50 MB base
```

**Consideraciones:**
- Usar `apk` en vez de `apt-get`
- Algunos paquetes requieren `musl-dev` para compilar
- Binarios más pequeños pero ligeramente más lentos

**Impacto:**
- Tamaño: -100 MB
- Seguridad: Menos vulnerabilidades
- Performance: -5% CPU (aceptable)

---

### 4. Lazy Loading de Ollama

**Problema:** Modelo IA (1.5 GB RAM) siempre cargado  
**Solución:** Cargar solo cuando se use el chat

```python
# dashboard/ai_agent.py
class LazyOllamaAgent:
    def __init__(self):
        self._model_loaded = False
        self._client = None
    
    def _ensure_loaded(self):
        """Carga el modelo solo cuando se necesita"""
        if not self._model_loaded:
            logger.info("🤖 Cargando modelo Ollama (primera vez)...")
            import ollama
            self._client = ollama.Client()
            # Pre-cargar modelo en memoria
            self._client.generate(model="qwen2.5-coder:1.5b", prompt="test")
            self._model_loaded = True
            logger.info("✅ Modelo cargado")
    
    def ask(self, question: str, context: dict) -> str:
        self._ensure_loaded()  # Lazy load
        return self._client.generate(
            model="qwen2.5-coder:1.5b",
            prompt=self._build_prompt(question, context)
        )["response"]

# Singleton global
agent = LazyOllamaAgent()
```

**Impacto:**
- RAM idle: -1.2 GB (si no se usa IA)
- RAM cuando se usa: +1.2 GB (solo entonces)
- Latencia primera consulta: +3-5 segundos (aceptable)

---

### 5. PostgreSQL Tuning

**Problema:** PostgreSQL usa 300 MB con configuración por defecto  
**Solución:** Optimizar para workload pequeño

```conf
# postgresql.conf
max_connections = 20              # Default: 100
shared_buffers = 64MB             # Default: 256MB
effective_cache_size = 128MB      # Default: 512MB
maintenance_work_mem = 16MB       # Default: 64MB
work_mem = 2MB                    # Default: 4MB
wal_buffers = 2MB                 # Default: 16MB
checkpoint_completion_target = 0.9
random_page_cost = 1.1            # SSD optimized
```

**Impacto:**
- RAM: -150 MB
- Performance: +10% en queries simples
- Conexiones: Suficiente para 1-2 workers

---

### 6. Chrome Headless Optimizado

**Problema:** Chrome consume 500 MB RAM  
**Solución:** Flags de optimización agresivos

```python
# scraper_selenium.py
def get_optimized_chrome_options():
    """Chrome options optimizadas para bajo consumo"""
    options = webdriver.ChromeOptions()
    
    # Headless mode
    options.add_argument('--headless=new')  # Nuevo modo (más eficiente)
    
    # Memory optimizations
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-software-rasterizer')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-background-networking')
    options.add_argument('--disable-default-apps')
    options.add_argument('--disable-sync')
    options.add_argument('--disable-translate')
    options.add_argument('--metrics-recording-only')
    options.add_argument('--mute-audio')
    options.add_argument('--no-first-run')
    options.add_argument('--safebrowsing-disable-auto-update')
    
    # Performance
    options.add_argument('--disable-setuid-sandbox')
    options.add_argument('--memory-pressure-off')
    options.add_argument('--max-old-space-size=512')
    options.add_argument('--js-flags=--max-old-space-size=512')
    
    # User agent
    options.add_argument(f'user-agent={config.USER_AGENT}')
    
    return options
```

**Impacto:**
- RAM: -200 MB
- CPU: -15%
- Estabilidad: +20% (menos crashes)

---

### 7. Gunicorn Production Server

**Problema:** Flask dev server es lento y single-threaded  
**Solución:** Gunicorn con workers gevent

```dockerfile
# requirements.txt
gunicorn==21.2.0
gevent==23.9.1
```

```python
# supervisord.conf
[program:flask]
command=gunicorn \
    --workers 2 \
    --worker-class gevent \
    --worker-connections 100 \
    --bind 0.0.0.0:5000 \
    --timeout 120 \
    --access-logfile /var/log/gunicorn-access.log \
    --error-logfile /var/log/gunicorn-error.log \
    app:app
```

**Impacto:**
- Throughput: 3x más requests/segundo
- Latencia: -60% (800ms → 320ms)
- Concurrencia: 200 usuarios simultáneos
- Auto-restart: Workers se reinician si fallan

---

### 8. Redis Cache Layer

**Problema:** Métricas se recalculan en cada request  
**Solución:** Cache en Redis (5 MB RAM)

```dockerfile
# Dockerfile
RUN apk add --no-cache redis
```

```python
# analytics.py
import redis
import json
from functools import wraps

redis_client = redis.Redis(
    host='localhost',
    port=6379,
    decode_responses=True,
    max_connections=10
)

def cache_result(ttl=3600):
    """Decorator para cachear resultados en Redis"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Intentar obtener de cache
            cached = redis_client.get(cache_key)
            if cached:
                logger.debug(f"✅ Cache HIT: {cache_key}")
                return json.loads(cached)
            
            # Calcular y guardar en cache
            logger.debug(f"❌ Cache MISS: {cache_key}")
            result = func(*args, **kwargs)
            redis_client.setex(cache_key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator

@cache_result(ttl=3600)  # Cache por 1 hora
def get_avg_by_comuna():
    """Precio promedio por comuna (cacheado)"""
    df = pd.read_sql("SELECT comuna, AVG(precio_m2) as avg FROM properties GROUP BY comuna", engine)
    return df.to_dict('records')

@cache_result(ttl=1800)  # Cache por 30 min
def detect_opportunities():
    """Oportunidades detectadas (cacheado)"""
    # ... lógica compleja ...
    return opportunities
```

**Impacto:**
- Response time: -75% en endpoints cacheados
- CPU: -40% (menos cálculos)
- RAM: +5 MB (Redis overhead)
- Cache hit rate esperado: 80-90%

---

### 9. HTTP Compression

**Problema:** JSON responses grandes (500 KB - 2 MB)  
**Solución:** Compresión gzip automática

```python
# app.py
from flask_compress import Compress

app = Flask(__name__)
app.config['COMPRESS_MIMETYPES'] = [
    'text/html',
    'text/css',
    'text/javascript',
    'application/json',
    'application/javascript'
]
app.config['COMPRESS_LEVEL'] = 6  # Balance velocidad/compresión
app.config['COMPRESS_MIN_SIZE'] = 500  # Solo comprimir > 500 bytes

Compress(app)
```

**Impacto:**
- Tráfico de red: -60% (JSON comprime muy bien)
- Latencia percibida: -40% (menos datos a transferir)
- CPU: +5% (compresión)

---

### 10. Log Rotation

**Problema:** Logs crecen indefinidamente  
**Solución:** Rotación automática con logrotate

```dockerfile
# Dockerfile
RUN apk add --no-cache logrotate

COPY <<EOF /etc/logrotate.d/scraper
/var/log/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    maxsize 50M
    create 0644 scraper scraper
    postrotate
        supervisorctl restart all > /dev/null 2>&1 || true
    endscript
}
EOF
```

```bash
# Cron job para ejecutar logrotate
echo "0 0 * * * /usr/sbin/logrotate /etc/logrotate.d/scraper" | crontab -
```

**Impacto:**
- Disco: Máximo 350 MB logs (7 días × 50 MB)
- Previene: Contenedor lleno de logs
- Debugging: Últimos 7 días disponibles

---

### 11. Servicios Modulares (Docker Compose)

**Problema:** Todos los servicios siempre activos  
**Solución:** Profiles para activar bajo demanda

```yaml
# docker-compose.optimized.yml
version: '3.8'

services:
  # CORE: Siempre activo (scraper + DB)
  scraper-core:
    build:
      context: .
      dockerfile: Dockerfile.optimized
      target: core
    container_name: scraper-core
    environment:
      - DATABASE_URL=postgresql://scraper:scraper123@localhost:5432/portalinmobiliario
      - ENABLE_DASHBOARD=false
      - ENABLE_AI=false
    mem_limit: 1.5g
    cpus: 1.5
    restart: unless-stopped
    volumes:
      - ./output:/app/output
      - postgres-data:/var/lib/postgresql/data

  # DASHBOARD: Activar con --profile dashboard
  dashboard:
    build:
      context: .
      dockerfile: Dockerfile.optimized
      target: dashboard
    container_name: scraper-dashboard
    depends_on:
      - scraper-core
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://scraper:scraper123@scraper-core:5432/portalinmobiliario
      - REDIS_URL=redis://scraper-core:6379
    mem_limit: 1g
    cpus: 1
    profiles: ["dashboard"]
    restart: unless-stopped

  # IA: Activar con --profile ai
  ollama:
    image: ollama/ollama:latest
    container_name: scraper-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama-models:/root/.ollama
    mem_limit: 2g
    cpus: 2
    profiles: ["ai"]
    restart: unless-stopped
    command: serve

volumes:
  postgres-data:
  ollama-models:
```

**Uso:**
```bash
# Solo scraping (1.5 GB RAM)
docker-compose up scraper-core

# Con dashboard (2.5 GB RAM)
docker-compose --profile dashboard up

# Con IA (4.5 GB RAM)
docker-compose --profile dashboard --profile ai up
```

**Impacto:**
- Flexibilidad: Activar solo lo necesario
- Costos: Pagar solo por lo que usas
- Escalabilidad: Escalar servicios independientemente

---

## 📁 Estructura de Archivos

### Nuevos Archivos a Crear

```
scraper-portalinmobiliario/
├── Dockerfile.optimized          # Dockerfile multi-stage optimizado
├── docker-compose.optimized.yml  # Compose con profiles
├── config/
│   ├── postgresql.conf           # PostgreSQL tuning
│   ├── redis.conf                # Redis config
│   └── supervisord-optimized.conf
├── scripts/
│   ├── setup-logrotate.sh        # Script de rotación de logs
│   └── benchmark.sh              # Script de benchmarking
└── docs/
    └── specs/
        └── PRD-OPTIMIZACION-CONTENEDOR.md  # Este documento
```

### Archivos a Modificar

```
scraper-portalinmobiliario/
├── scraper_selenium.py           # Agregar get_optimized_chrome_options()
├── analytics.py                  # Agregar Redis cache decorators
├── app.py                        # Agregar Flask-Compress
├── dashboard/
│   ├── ai_agent.py               # Implementar LazyOllamaAgent
│   └── routes.py                 # Usar cache en endpoints
├── requirements.txt              # Agregar: gunicorn, gevent, redis, flask-compress
└── .dockerignore                 # Optimizar exclusiones
```

---

## 🚀 Plan de Implementación

### Fase 1: Quick Wins (Día 1 - 4 horas)

**Objetivo:** Reducir 30% recursos sin cambios arquitectónicos

| Tarea | Tiempo | Responsable | Impacto |
|-------|--------|-------------|---------|
| 1.1 Implementar Chrome optimizado | 30 min | Backend | -200 MB RAM |
| 1.2 Configurar PostgreSQL tuning | 30 min | DevOps | -150 MB RAM |
| 1.3 Agregar log rotation | 30 min | DevOps | Prevención |
| 1.4 Migrar a Gunicorn | 1 hora | Backend | +200% throughput |
| 1.5 Testing y validación | 1.5 horas | QA | - |

**Entregables:**
- ✅ `scraper_selenium.py` actualizado
- ✅ `postgresql.conf` creado
- ✅ `supervisord.conf` actualizado con Gunicorn
- ✅ Tests pasando

**Criterios de Éxito:**
- RAM idle < 1.8 GB
- Response time < 500ms
- 0 regresiones

---

### Fase 2: Refactoring (Día 2-3 - 8 horas)

**Objetivo:** Reducir 45% tamaño imagen y agregar cache

| Tarea | Tiempo | Responsable | Impacto |
|-------|--------|-------------|---------|
| 2.1 Crear Dockerfile multi-stage | 2 horas | DevOps | -500 MB imagen |
| 2.2 Migrar a Chromium | 1 hora | DevOps | -200 MB imagen |
| 2.3 Implementar Redis cache | 2 horas | Backend | -75% latencia |
| 2.4 Agregar Flask-Compress | 30 min | Backend | -60% tráfico |
| 2.5 Implementar Lazy Ollama | 1.5 horas | Backend | -1.2 GB RAM idle |
| 2.6 Testing integral | 1 hora | QA | - |

**Entregables:**
- ✅ `Dockerfile.optimized` funcional
- ✅ `analytics.py` con Redis cache
- ✅ `ai_agent.py` con lazy loading
- ✅ Benchmarks comparativos

**Criterios de Éxito:**
- Imagen < 1.5 GB
- RAM idle < 1.2 GB
- Cache hit rate > 70%

---

### Fase 3: Arquitectura Modular (Día 4-5 - 8 horas)

**Objetivo:** Servicios independientes y escalables

| Tarea | Tiempo | Responsable | Impacto |
|-------|--------|-------------|---------|
| 3.1 Migrar a Alpine Linux | 3 horas | DevOps | -100 MB imagen |
| 3.2 Crear docker-compose profiles | 2 horas | DevOps | Flexibilidad |
| 3.3 Separar servicios core/optional | 2 horas | DevOps | Modularidad |
| 3.4 Documentación y runbooks | 1 hora | Tech Writer | - |

**Entregables:**
- ✅ `Dockerfile.optimized` con Alpine
- ✅ `docker-compose.optimized.yml`
- ✅ Documentación actualizada
- ✅ Scripts de deployment

**Criterios de Éxito:**
- Imagen < 1.2 GB
- 3 modos de deploy (core/dashboard/ai)
- Build time < 5 min

---

### Fase 4: Testing y Deploy (Día 6 - 4 horas)

**Objetivo:** Validar en producción

| Tarea | Tiempo | Responsable | Impacto |
|-------|--------|-------------|---------|
| 4.1 Load testing | 1 hora | QA | Validación |
| 4.2 Deploy a staging | 1 hora | DevOps | - |
| 4.3 Monitoreo 24h | - | DevOps | - |
| 4.4 Deploy a producción | 1 hora | DevOps | - |
| 4.5 Post-mortem y ajustes | 1 hora | Team | - |

**Entregables:**
- ✅ Reporte de load testing
- ✅ Métricas de producción
- ✅ Rollback plan documentado

**Criterios de Éxito:**
- Todas las métricas cumplidas
- 0 downtime en deploy
- Costos < $8/mes

---

## 📊 Benchmarking y Validación

### Tests de Performance

```bash
# scripts/benchmark.sh
#!/bin/bash

echo "🔬 Benchmarking contenedor optimizado..."

# 1. Tamaño de imagen
echo "📦 Tamaño de imagen:"
docker images | grep portalinmobiliario

# 2. Tiempo de build
echo "⏱️ Tiempo de build:"
time docker build -f Dockerfile.optimized -t portalinmobiliario:optimized .

# 3. Uso de recursos en idle
echo "💾 Recursos en idle (30s):"
docker run -d --name bench-idle portalinmobiliario:optimized
sleep 30
docker stats bench-idle --no-stream
docker rm -f bench-idle

# 4. Uso durante scraping
echo "🕷️ Recursos durante scraping:"
docker run -d --name bench-scraping portalinmobiliario:optimized \
  python main.py --operacion venta --tipo departamento --max-pages 5
sleep 60
docker stats bench-scraping --no-stream
docker rm -f bench-scraping

# 5. Response time del dashboard
echo "🌐 Response time dashboard:"
docker run -d -p 5000:5000 --name bench-dashboard portalinmobiliario:optimized
sleep 20
ab -n 100 -c 10 http://localhost:5000/
docker rm -f bench-dashboard

# 6. Cache hit rate
echo "📊 Cache hit rate (Redis):"
docker exec bench-dashboard redis-cli INFO stats | grep keyspace_hits
```

### Métricas Esperadas

| Métrica | Antes | Después | Mejora | ✅/❌ |
|---------|-------|---------|--------|------|
| Tamaño imagen | 2.2 GB | 1.2 GB | -45% | |
| RAM idle | 2.2 GB | 1.2 GB | -45% | |
| RAM scraping | 2.8 GB | 1.8 GB | -36% | |
| Build time | 10 min | 5 min | -50% | |
| Startup time | 40s | 15s | -62% | |
| Response time | 800ms | 200ms | -75% | |
| Throughput | 10 req/s | 30 req/s | +200% | |
| Costo mensual | $12 | $6 | -50% | |

---

## 🔒 Seguridad y Compliance

### Mejoras de Seguridad

1. **Menor superficie de ataque**
   - Alpine Linux tiene menos paquetes instalados
   - Multi-stage elimina herramientas de compilación

2. **Usuario no-root**
   - Todos los servicios corren como `scraper` (UID 1000)
   - PostgreSQL corre como `postgres`

3. **Secrets management**
   - Variables de entorno para credenciales
   - No hardcodear passwords

4. **Network isolation**
   - Redis solo accesible internamente
   - PostgreSQL solo accesible internamente
   - Solo Flask expuesto al exterior

### Escaneo de Vulnerabilidades

```bash
# Escanear imagen con Trivy
trivy image portalinmobiliario:optimized

# Objetivo: 0 vulnerabilidades CRITICAL
```

---

## 💰 Análisis de Costos

### Costos Actuales (Railway)

```yaml
Configuración Actual:
  RAM: 4 GB
  CPU: 2 vCPUs
  Disco: 10 GB
  
Costo Mensual:
  Compute: $10/mes
  Database: $0 (incluido)
  Bandwidth: $2/mes
  Total: $12/mes
  
Costo Anual: $144/mes
```

### Costos Optimizados (Railway)

```yaml
Configuración Optimizada:
  RAM: 2 GB
  CPU: 1 vCPU
  Disco: 10 GB
  
Costo Mensual:
  Compute: $5/mes
  Database: $0 (incluido)
  Bandwidth: $1/mes (menos tráfico por compresión)
  Total: $6/mes
  
Costo Anual: $72/mes
```

### ROI

```
Ahorro Anual: $72 USD
Inversión (desarrollo): ~$800 (40 horas × $20/hora)
ROI: 11 meses
```

**Beneficios adicionales no monetarios:**
- Deploys 2x más rápidos
- Mejor experiencia de usuario
- Capacidad de escalar 2x más instancias
- Menor huella de carbono

---

## 🚨 Riesgos y Mitigaciones

### Riesgos Identificados

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| **Alpine incompatibilidades** | Media | Alto | Testing exhaustivo, fallback a Debian |
| **Cache stale data** | Media | Medio | TTL cortos (30-60 min), invalidación manual |
| **Lazy loading latencia** | Baja | Bajo | Pre-cargar en horarios de bajo tráfico |
| **Redis single point of failure** | Baja | Medio | Graceful degradation si Redis falla |
| **Chromium bugs** | Baja | Alto | Mantener Chrome como fallback |

### Plan de Rollback

```bash
# Si algo falla, rollback inmediato
docker tag portalinmobiliario:mvp portalinmobiliario:backup
docker tag portalinmobiliario:optimized portalinmobiliario:mvp

# Si falla, revertir
docker tag portalinmobiliario:backup portalinmobiliario:mvp
docker-compose up -d
```

---

## 📚 Documentación y Training

### Documentos a Actualizar

- ✅ `docs/deployment/DOCKER.md` - Agregar sección de optimización
- ✅ `docs/MVP-ARCHITECTURE.md` - Actualizar diagramas
- ✅ `README.md` - Actualizar comandos de deploy
- ✅ `docs/deployment/QUICKSTART-DOCKER.md` - Nuevos comandos

### Training del Equipo

1. **Session 1: Arquitectura optimizada** (1 hora)
   - Explicar cambios arquitectónicos
   - Demo de multi-stage build
   - Q&A

2. **Session 2: Nuevas herramientas** (1 hora)
   - Redis cache patterns
   - Gunicorn configuration
   - Docker profiles

3. **Session 3: Troubleshooting** (30 min)
   - Debugging común
   - Monitoreo de métricas
   - Rollback procedures

---

## ✅ Checklist de Aceptación

### Funcional

- [ ] Scraping funciona igual que antes
- [ ] Dashboard carga correctamente
- [ ] Agente IA responde (con lazy loading)
- [ ] PostgreSQL persiste datos
- [ ] Exports JSON/CSV funcionan
- [ ] Todos los tests unitarios pasan
- [ ] Tests E2E pasan

### Performance

- [ ] Imagen < 1.5 GB
- [ ] RAM idle < 1.5 GB
- [ ] RAM scraping < 2 GB
- [ ] Build time < 6 min
- [ ] Startup time < 20s
- [ ] Response time < 300ms
- [ ] Cache hit rate > 70%

### Operacional

- [ ] Deploy exitoso en staging
- [ ] Monitoreo configurado
- [ ] Logs rotando correctamente
- [ ] Backups funcionando
- [ ] Rollback plan probado
- [ ] Documentación actualizada
- [ ] Equipo entrenado

### Costos

- [ ] Costo Railway < $8/mes
- [ ] Uso de CPU < 60% promedio
- [ ] Uso de RAM < 80% promedio
- [ ] Disco < 50% usado

---

## 📅 Timeline

```mermaid
gantt
    title Plan de Implementación - Optimización Contenedor
    dateFormat  YYYY-MM-DD
    section Fase 1
    Chrome optimizado           :2026-04-12, 1d
    PostgreSQL tuning          :2026-04-12, 1d
    Gunicorn + Logs            :2026-04-12, 1d
    section Fase 2
    Multi-stage build          :2026-04-13, 1d
    Redis cache                :2026-04-13, 1d
    Lazy Ollama                :2026-04-14, 1d
    section Fase 3
    Alpine migration           :2026-04-15, 1d
    Docker profiles            :2026-04-15, 1d
    section Fase 4
    Testing                    :2026-04-16, 1d
    Deploy staging             :2026-04-16, 1d
    Deploy producción          :2026-04-17, 1d
```

**Fecha inicio:** Abril 12, 2026  
**Fecha fin estimada:** Abril 17, 2026  
**Duración total:** 6 días

---

## 🎯 Conclusión

Esta optimización representa una **mejora significativa** en eficiencia de recursos, costos y experiencia de usuario, con un **ROI de 11 meses** y beneficios a largo plazo en escalabilidad y mantenibilidad.

### Próximos Pasos

1. ✅ **Aprobación del PRD** por stakeholders
2. ✅ **Asignación de recursos** (1 DevOps + 1 Backend)
3. ✅ **Kick-off meeting** (Abril 12, 2026)
4. ✅ **Inicio de Fase 1** (Quick Wins)

---

**Aprobadores:**

- [ ] Tech Lead: _________________ Fecha: _______
- [ ] DevOps Lead: ______________ Fecha: _______
- [ ] Product Owner: ____________ Fecha: _______

**Versión:** 1.0  
**Última actualización:** Abril 11, 2026
