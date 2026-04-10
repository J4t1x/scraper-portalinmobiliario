# Arquitectura — Portal Inmobiliario Scraper

**Última actualización:** Abril 2026

---

## Visión General

Sistema de scraping automatizado para extraer datos de propiedades inmobiliarias desde portalinmobiliario.com, con capacidades de validación, transformación y exportación múltiple.

---

## Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                    PORTAL INMOBILIARIO SCRAPER                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  1. INPUT LAYER                                         │     │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐             │     │
│  │  │   CLI    │  │Dashboard │  │Scheduler │             │     │
│  │  │  Args    │  │   Web    │  │ APSched  │             │     │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘             │     │
│  │       └─────────────┼─────────────┘                    │     │
│  └─────────────────────┼──────────────────────────────────┘     │
│                        ▼                                         │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  2. SCRAPING ENGINE                                     │     │
│  │  ┌──────────────┐  ┌──────────────┐                    │     │
│  │  │   Selenium   │  │ BeautifulSoup│                    │     │
│  │  │  WebDriver   │  │    Parser    │                    │     │
│  │  └──────┬───────┘  └──────┬───────┘                    │     │
│  │         │                  │                            │     │
│  │         ▼                  ▼                            │     │
│  │  ┌──────────────────────────────┐                      │     │
│  │  │  Pagination & Navigation     │                      │     │
│  │  └──────────────┬───────────────┘                      │     │
│  │                 │                                       │     │
│  │                 ▼                                       │     │
│  │  ┌──────────────────────────────┐                      │     │
│  │  │  Property Extraction         │                      │     │
│  │  │  - Listado (9 campos)        │                      │     │
│  │  │  - Detalle (15+ campos)      │                      │     │
│  │  └──────────────┬───────────────┘                      │     │
│  └─────────────────┼──────────────────────────────────────┘     │
│                    ▼                                             │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  3. DATA PROCESSING                                     │     │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │     │
│  │  │  Validation  │→ │Transformation│→ │Deduplication │ │     │
│  │  └──────────────┘  └──────────────┘  └──────────────┘ │     │
│  └─────────────────────┼──────────────────────────────────┘     │
│                        ▼                                         │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  4. STORAGE & EXPORT                                    │     │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐             │     │
│  │  │   TXT    │  │   JSON   │  │   CSV    │             │     │
│  │  │ (JSONL)  │  │Structured│  │ Tabular  │             │     │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘             │     │
│  │       └─────────────┼─────────────┘                    │     │
│  │                     ▼                                   │     │
│  │  ┌──────────────────────────────┐                      │     │
│  │  │      PostgreSQL (Railway)    │                      │     │
│  │  │  - Properties               │                      │     │
│  │  │  - Scheduler Executions      │                      │     │
│  │  │  - Scheduler State           │                      │     │
│  │  └──────────────────────────────┘                      │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Stack Tecnológico

### Core
- **Python:** 3.11+ (3.14.3 en producción)
- **Selenium:** 4.18.1 (navegación real)
- **ChromeDriver:** 146.0.7680.165 (gestión automática)
- **BeautifulSoup4:** 4.12.3 (parsing HTML)

### Utilidades
- **requests:** 2.31.0 (scraper alternativo)
- **lxml:** 5.1.0 (parser rápido)
- **python-dotenv:** 1.0.1 (configuración)
- **webdriver-manager:** 4.0.1 (gestión de drivers)
- **APScheduler:** 3.10.4 (scheduler de jobs)

### Infraestructura
- **Docker:** Python 3.11-slim + Chrome + ChromeDriver
- **PostgreSQL:** 15 (Railway)
- **Railway:** Deployment y hosting
- **GitHub Actions:** CI/CD

---

## Componentes Principales

### 1. Scraper Engine (`scraper_selenium.py`)

**Clase:** `PortalInmobiliarioSeleniumScraper`

**Responsabilidades:**
- Inicializar WebDriver con configuración headless
- Construir URLs con paginación
- Navegar por páginas de resultados
- Extraer datos de propiedades
- Scrapear páginas de detalle (opcional)
- Manejar errores y retry automático

**Métodos clave:**
```python
def __init__(operacion: str, tipo: str, headless: bool = True)
def build_url(offset: int = 0) -> str
def fetch_page(url: str) -> WebDriver
def extract_properties(driver: WebDriver) -> List[Dict]
def scrape_property_detail(property_id: str, url: str) -> Dict
def scrape_all_pages(max_pages: Optional[int] = None) -> List[Dict]
def has_next_page(driver: WebDriver) -> bool
def close()
```

### 2. Data Exporter (`exporter.py`)

**Clase:** `DataExporter`

**Responsabilidades:**
- Exportar a TXT (formato JSONL)
- Exportar a JSON estructurado con metadata
- Exportar a CSV con headers
- Aplanar campos anidados para CSV

**Métodos clave:**
```python
def export_to_txt(properties: List[Dict], operacion: str, tipo: str)
def export_to_json(properties: List[Dict], operacion: str, tipo: str)
def export_to_csv(properties: List[Dict], operacion: str, tipo: str, flatten_nested: bool)
def flatten_property(prop: Dict) -> Dict
```

### 3. Data Loader (`data_loader.py`)

**Clase:** `JSONDataLoader`

**Responsabilidades:**
- Leer archivos JSON desde carpeta `output/`
- Parsear estructura `{ metadata: {...}, propiedades: [...] }`
- Combinar propiedades de múltiples archivos
- Filtrar por operación, tipo, rango de precio, búsqueda de texto
- Calcular estadísticas (total, distribución)
- Implementar paginación de resultados

**Métodos clave:**
```python
def load_all_json_files() -> List[Dict]
def load_by_filters(operacion, tipo, precio_min, precio_max, search) -> List[Dict]
def get_stats() -> Dict
def paginate(properties, page, per_page) -> Dict
def _extract_price_clp(price_str) -> Optional[float]
```

### 4. Validator (`validator.py`)

**Responsabilidades:**
- Validar integridad de datos
- Verificar formatos (precios, fechas, coordenadas)
- Detectar campos faltantes
- Generar reportes de calidad

### 5. Deduplicator (`deduplicator.py`)

**Responsabilidades:**
- Detectar propiedades duplicadas por ID
- Comparar por características
- Mantener versión más completa
- Generar estadísticas

### 6. CLI (`main.py`)

**Responsabilidades:**
- Parsear argumentos de línea de comandos
- Orquestar flujo de scraping
- Manejar configuración
- Logging y reporting
- Control del scheduler (start, stop, pause, resume, status)

### 7. Scheduler (`scheduler.py`, `scheduler_jobs.py`)

**Responsabilidades:**
- Gestión de jobs periódicos con APScheduler
- Configuración de schedules (interval, cron)
- Manejo de concurrencia (max 3 jobs simultáneos)
- Logging de ejecuciones en PostgreSQL
- Persistencia de estado del scheduler
- Recuperación automática ante reinicios
- Jobs de scraping automático (SPEC-012)

**Métodos clave:**
```python
def start() -> None
def shutdown(wait: bool) -> None
def pause() -> None
def resume() -> None
def add_job(func, job_id, trigger, **trigger_args) -> None
def remove_job(job_id) -> bool
def get_jobs() -> List[Dict]
def get_executions(job_id, limit) -> List[Dict]
```

**Jobs de Scraping Automático (SPEC-012):**
- `scrape_venta_departamento` - Diario a las 02:00 AM (50 páginas, detalle completo)
- `scrape_arriendo_departamento` - Diario a las 03:00 AM (50 páginas, detalle completo)
- `scrape_venta_casa` - Diario a las 04:00 AM (30 páginas, detalle completo)
- `scrape_arriendo_casa` - Diario a las 05:00 AM (30 páginas, detalle completo)
- `scrape_venta_oficina` - Semanal (lunes a las 06:00 AM, 20 páginas, detalle completo)

### 8. Scheduler API (`scheduler_api.py`)

**Responsabilidades:**
- API REST para control del scheduler
- Endpoints para gestión de jobs
- Consulta de ejecuciones históricas
- Configuración de jobs predefinidos

**Implementación (SPEC-011):**
- Flask-RESTX para documentación Swagger
- Integración con ScraperScheduler
- Validación de inputs
- Manejo de errores y logging

**Endpoints:**
- `GET /api/scheduler/status` - Estado del scheduler (running, paused, stopped)
- `POST /api/scheduler/start` - Iniciar scheduler
- `POST /api/scheduler/stop` - Detener scheduler
- `POST /api/scheduler/pause` - Pausar scheduler
- `POST /api/scheduler/resume` - Reanudar scheduler
- `GET /api/scheduler/jobs` - Listar jobs configurados
- `GET /api/scheduler/jobs/<id>` - Obtener detalle de un job
- `POST /api/scheduler/jobs` - Agregar job personalizado
- `DELETE /api/scheduler/jobs/<id>` - Remover job
- `POST /api/scheduler/jobs/<id>/pause` - Pausar job específico
- `POST /api/scheduler/jobs/<id>/resume` - Reanudar job específico
- `GET /api/scheduler/executions` - Historial de ejecuciones (paginado)
- `GET /api/scheduler/executions/<job_id>` - Ejecuciones de un job específico
- `POST /api/scheduler/setup-default` - Configurar jobs predefinidos (SPEC-012)
- `GET /api/scheduler/heartbeat` - Actualizar heartbeat

### 9. Dashboard Web (`app.py`)

**Responsabilidades:**
- Interfaz web con Flask
- Autenticación (Admin/Viewer)
- Control del scraper desde UI
- Visualización de datos
- Logs en tiempo real (WebSocket)

---

## Flujo de Datos

### Scraping Básico

```
1. Usuario ejecuta CLI
   ↓
2. Scraper construye URL inicial
   ↓
3. Selenium carga página
   ↓
4. Extrae propiedades (9 campos)
   ↓
5. Navega a siguiente página (si existe)
   ↓
6. Repite hasta max_pages o fin
   ↓
7. Valida datos extraídos
   ↓
8. Exporta a formato seleccionado
   ↓
9. Guarda en output/
```

### Scraping con Detalle

```
1-6. (igual que scraping básico)
   ↓
7. Para cada propiedad (hasta max_detail_properties):
   ↓
8. Navega a página de detalle
   ↓
9. Extrae campos adicionales (15+ campos)
   ↓
10. Merge con datos de listado
   ↓
11. Valida datos completos
   ↓
12. Exporta a formato seleccionado
```

---

## Modelo de Datos

### Datos de Listado (9 campos)

```python
{
    "id": str,              # ID único (ej: "MLC-3705621748")
    "titulo": str,          # Título de la propiedad
    "headline": str,        # Categoría (ej: "Departamentos en venta")
    "precio": str,          # Precio (ej: "UF 3.055", "$ 740.000")
    "ubicacion": str,       # Dirección completa
    "atributos": str,       # Características (ej: "2 dorm, 1 baño, 50 m²")
    "url": str,             # URL completa con tracking
    "operacion": str,       # venta | arriendo | arriendo-de-temporada
    "tipo": str             # departamento | casa | oficina | etc.
}
```

### Datos de Detalle (15+ campos adicionales)

```python
{
    # ... campos de listado ...
    "descripcion": str,                    # Descripción completa
    "caracteristicas": {
        "orientacion": str,                # Norte, Sur, Este, Oeste
        "año_construccion": int,           # Año
        "gastos_comunes": int,             # CLP
        "estacionamientos": int,           # Cantidad
        "bodegas": int                     # Cantidad
    },
    "publicador": {
        "nombre": str,                     # Nombre
        "tipo": str                        # inmobiliaria | particular
    },
    "imagenes": List[str],                 # URLs (máx. 10)
    "coordenadas": {
        "lat": float,                      # Latitud GPS
        "lng": float                       # Longitud GPS
    },
    "fecha_publicacion": str               # ISO 8601 (YYYY-MM-DD)
}
```

---

## Configuración

### Variables de Entorno (`.env`)

```env
# Scraping
DELAY_BETWEEN_REQUESTS=2    # Segundos entre requests
MAX_RETRIES=3               # Intentos máximos por página
TIMEOUT=30                  # Timeout de requests (segundos)

# User Agent
USER_AGENT=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36

# Database (Railway)
DATABASE_URL=postgresql://user:pass@host:port/db

# Dashboard
FLASK_SECRET_KEY=your-secret-key
FLASK_DEBUG=false
```

---

## Deployment

### Railway

**Configuración:**
- `Dockerfile` — Imagen Python 3.11-slim + Chrome
- `railway.json` — Configuración de servicio
- `docker-compose.yml` — Orquestación local

**Proceso:**
1. Push a GitHub
2. Railway detecta Dockerfile
3. Build automático
4. Deploy a producción
5. PostgreSQL provisionado automáticamente

**Variables de entorno en Railway:**
- `DATABASE_URL` (auto-provisionada)
- `DELAY_BETWEEN_REQUESTS`
- `MAX_RETRIES`
- `TIMEOUT`

---

## Seguridad

### Consideraciones

1. **Rate Limiting:**
   - Delays configurables entre requests
   - Retry con exponential backoff
   - User-Agent realista

2. **Datos Sensibles:**
   - `.env` no commiteado
   - Credenciales en variables de entorno
   - Usuario no-root en Docker

3. **Validación:**
   - Sanitización de inputs
   - Validación de URLs
   - Manejo seguro de archivos

---

## Performance

### Métricas

- **Throughput:** ~50 propiedades/hora (con delays)
- **Latencia:** ~12 segundos/página
- **Tasa de éxito:** >95%
- **Uso de memoria:** <512MB

### Optimizaciones

1. **Selectores eficientes:** CSS sobre XPath
2. **Headless mode:** Sin UI gráfica
3. **Lazy loading:** Solo cargar lo necesario
4. **Paginación inteligente:** Detección de límites

---

## Monitoreo

### Logs

- **Nivel INFO:** Progreso general
- **Nivel WARNING:** Propiedades con datos incompletos
- **Nivel ERROR:** Errores críticos

### Métricas

- Propiedades scrapeadas
- Páginas procesadas
- Errores por tipo
- Tiempo de ejecución

---

## Roadmap

### ✅ Fase 1 - MVP (Completado)
- Scraper con Selenium
- Exportación TXT/JSON/CSV
- Dockerización
- Railway deployment

### 🚧 Fase 2 - En Progreso
- Tests automatizados (pytest)
- Dashboard web (Flask)
- Scraping de detalle
- Validación de datos

### 📋 Fase 3 - Próximo
- PostgreSQL integration completa
- API REST (FastAPI)
- Scheduler (cron jobs)
- Cache de resultados

### 🌟 Fase 4 - Futuro
- Scraping distribuido (Celery)
- Dashboard analítico
- Machine Learning (predicción de precios)
- Multi-plataforma (otros sitios)

---

**Última revisión:** Abril 2026
