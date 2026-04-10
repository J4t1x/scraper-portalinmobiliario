# 🏠 Portal Inmobiliario Scraper

[![Estado](https://img.shields.io/badge/estado-funcional-brightgreen)](https://github.com)
[![Python](https://img.shields.io/badge/python-3.14.3-blue)](https://www.python.org/)
[![Última actualización](https://img.shields.io/badge/última%20actualización-abril%202026-orange)](https://github.com)

Scraper automatizado en Python para extraer datos de propiedades desde [portalinmobiliario.com](https://www.portalinmobiliario.com)

## � Estado del Proyecto

- ✅ **Última ejecución exitosa:** 7 de abril de 2026
- ✅ **Propiedades scrapeadas:** 144+ propiedades en pruebas recientes
- ✅ **Formatos soportados:** TXT (JSONL), JSON, CSV
- ✅ **Entorno:** Python 3.14.3 + Selenium 4.18.1 + ChromeDriver 146.0.7680.165
- ✅ **Workflow Cascade:** `/portalinmobiliario-dev` disponible

## �📋 Características

### Scraper CLI
- ✅ **Scraping con Selenium:** Navegación real del navegador Chrome (headless)
- ✅ **Extracción completa:** ID, título, headline, precio, ubicación, atributos, URL
- ✅ **Navegación automática:** Paginación inteligente con detección de límites
- ✅ **Configuración dinámica:** 3 operaciones × 8 tipos de propiedad = 24 combinaciones
- ✅ **Exportación múltiple:** TXT (JSONL), JSON estructurado, CSV
- ✅ **Manejo robusto de errores:** Retry automático y logging detallado
- ✅ **Rate limiting configurable:** Delays entre requests personalizables
- ✅ **WebDriver automático:** Gestión automática de ChromeDriver con webdriver-manager
- ✅ **Deduplicación inteligente:** Detección de duplicados entre ejecuciones con O(1) lookup
- ✅ **Workflow Cascade:** Automatización completa con `/portalinmobiliario-dev`

### Dashboard Web (Nuevo)
- ✅ **Interfaz Flask:** Dashboard web moderno con TailwindCSS
- ✅ **Autenticación:** Sistema de login con roles (Admin/Viewer)
- ✅ **Control del Scraper:** Ejecutar scraping desde la interfaz web
- ✅ **Visualización de Datos:** Explorador de archivos JSON/CSV con tablas interactivas
- ✅ **Business Intelligence:** Gráficos, KPIs y estadísticas descriptivas
- ✅ **Logs en Tiempo Real:** WebSocket para monitoreo en vivo
- 🚧 **En desarrollo:** Analytics avanzado y más features

## 🚀 Instalación

### Opción 1: Instalación Local

#### 1. Clonar el repositorio

```bash
cd /Users/ja/Documents/GitHub/scraper-portalinmobiliario
```

#### 2. Crear entorno virtual (recomendado)

```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

#### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

#### 4. Configurar variables de entorno (opcional)

```bash
cp .env.example .env
# Editar .env si deseas cambiar configuraciones
```

### Opción 2: Docker 🐳 (Recomendado para Producción)

#### 1. Build de la imagen

```bash
docker build -t portalinmobiliario:latest .
```

#### 2. Ejecutar con Docker

```bash
docker run --rm \
  -v $(pwd)/output:/app/output \
  portalinmobiliario:latest \
  python main.py --operacion venta --tipo departamento --max-pages 2
```

#### 3. O usar Docker Compose (incluye PostgreSQL)

```bash
docker-compose up -d
docker-compose run --rm scraper python main.py --operacion venta --tipo departamento
```

**📖 Ver [docs/deployment/DOCKER.md](docs/deployment/DOCKER.md) para documentación completa de Docker y Railway.**

## 💻 Uso

### Opción 1: Dashboard Web (Recomendado)

**Iniciar el dashboard:**
```bash
python app.py
```

Luego abrir en el navegador: `http://localhost:5000`

**Credenciales por defecto:**
- Admin: `admin` / `admin123`
- Viewer: `viewer` / `viewer123`

**Funcionalidades:**
- 🎯 Dashboard con KPIs y gráficos
- 🚀 Ejecutar scraper desde la interfaz
- 📊 Visualizar datos en tablas interactivas
- 📈 Analytics y estadísticas
- 📝 Logs en tiempo real

### Opción 2: CLI (Línea de comandos)

**Uso básico:**

```bash
python main.py --operacion venta --tipo departamento
```

**Ejemplos:**

**Scrapear departamentos en venta (todas las páginas):**
```bash
python main.py --operacion venta --tipo departamento
```

**Scrapear casas en arriendo (máximo 5 páginas):**
```bash
python main.py --operacion arriendo --tipo casa --max-pages 5
```

**Exportar a JSON:**
```bash
python main.py --operacion venta --tipo oficina --formato json
```

**Exportar a CSV:**
```bash
python main.py --operacion arriendo --tipo departamento --formato csv
```

**Modo verbose (más detalles):**
```bash
python main.py --operacion venta --tipo terreno --verbose
```

**Scrapear con información de detalle (Fase 2):**
```bash
python main.py --operacion venta --tipo departamento --scrape-details --max-pages 1
```

**Scrapear con detalle limitado a 5 propiedades:**
```bash
python main.py --operacion venta --tipo departamento --scrape-details --max-detail-properties 5 --max-pages 2
```

**Scrapear excluyendo duplicados (solo propiedades nuevas):**
```bash
python main.py --operacion venta --tipo departamento --exclude-duplicates
```

**Ver estadísticas de duplicados:**
```bash
python main.py --dedup-stats
```

**Resetear registro de duplicados:**
```bash
python main.py --operacion venta --tipo departamento --reset-duplicates
```

### Opción 3: Scheduler Automatizado (Nueva)

El scraper incluye un scheduler automatizado con APScheduler para ejecutar tareas de scraping periódicas sin intervención manual. Implementado en SPEC-011 y SPEC-012.

**Iniciar el scheduler:**
```bash
python main.py --scheduler start
```

**Ver estado del scheduler:**
```bash
python main.py --scheduler status
```

**Listar jobs configurados:**
```bash
python main.py --scheduler list-jobs
```

**Configurar jobs default (SPEC-012):**
```bash
python main.py --scheduler setup-default
```

Esto configura 5 jobs predefinidos:
- `scrape_venta_departamento` - Diario a las 02:00 AM (50 páginas, detalle completo)
- `scrape_arriendo_departamento` - Diario a las 03:00 AM (50 páginas, detalle completo)
- `scrape_venta_casa` - Diario a las 04:00 AM (30 páginas, detalle completo)
- `scrape_arriendo_casa` - Diario a las 05:00 AM (30 páginas, detalle completo)
- `scrape_venta_oficina` - Semanal (lunes a las 06:00 AM, 20 páginas, detalle completo)

**Agregar un job personalizado:**
```bash
python main.py --scheduler add-job --operacion venta --tipo departamento --schedule-type interval --hours 6
```

**Agregar job con cron (ej: todos los lunes a las 2 AM):**
```bash
python main.py --scheduler add-job --operacion arriendo --tipo casa --schedule-type cron --day-of-week mon --hour 2 --minute 0
```

**Remover un job:**
```bash
python main.py --scheduler remove-job --job-id scrape_venta_departamento
```

**Ver historial de ejecuciones:**
```bash
python main.py --scheduler executions
```

**Detener el scheduler:**
```bash
python main.py --scheduler stop
```

**Características del Scheduler:**
- ✅ Persistencia en PostgreSQL (jobs y estado)
- ✅ Logging detallado de ejecuciones
- ✅ Concurrency control (max 3 jobs simultáneos)
- ✅ Recuperación automática ante reinicios
- ✅ Heartbeat monitoring
- ✅ API REST para control remoto

### Parámetros disponibles

| Parámetro | Descripción | Requerido | Valores |
|-----------|-------------|-----------|---------|
| `--operacion` | Tipo de operación | ✅ | `venta`, `arriendo`, `arriendo-de-temporada` |
| `--tipo` | Tipo de propiedad | ✅ | `departamento`, `casa`, `oficina`, `terreno`, `local-comercial`, `bodega`, `estacionamiento`, `parcela` |
| `--max-pages` | Máximo de páginas a scrapear | ❌ | Número entero (default: todas) |
| `--formato` | Formato de exportación | ❌ | `txt`, `json`, `csv` (default: `txt`) |
| `--verbose` | Modo detallado | ❌ | Flag booleano |
| `--scrape-details` | Scrapear info adicional de cada propiedad | ❌ | Flag booleano |
| `--max-detail-properties` | Máximo de propiedades con detalle | ❌ | Número entero (default: todas) |
| `--include-duplicates` | Incluir duplicados en exportación | ❌ | Flag booleano (default: `True`) |
| `--exclude-duplicates` | Excluir duplicados de exportación | ❌ | Flag booleano |
| `--reset-duplicates` | Limpiar registro de duplicados | ❌ | Flag booleano |
| `--dedup-stats` | Mostrar estadísticas y salir | ❌ | Flag booleano |
| `--registry-path` | Ruta al archivo de registro | ❌ | Path (default: `data/scraped_ids.json`) |

## 📁 Estructura del proyecto

```
scraper-portalinmobiliario/
├── main.py                    # Script principal (CLI)
├── scraper.py                 # Scraper con requests + BeautifulSoup
├── scraper_selenium.py        # Scraper con Selenium (usado por defecto)
├── exporter.py                # Exportación a TXT/JSON/CSV
├── deduplicator.py            # Deduplicación de propiedades (O(1) lookup)
├── config.py                  # Configuración y constantes
├── utils.py                   # Utilidades y helpers
├── example.py                 # Script de ejemplo
├── requirements.txt           # Dependencias Python
├── .env                       # Configuración local
├── .env.example               # Ejemplo de configuración
├── .gitignore                 # Archivos ignorados
├── Dockerfile                 # Imagen Docker
├── docker-compose.yml         # Orquestación Docker + PostgreSQL
├── entrypoint.sh              # Script de entrada Docker
├── railway.json               # Configuración Railway
├── test-docker.sh             # Script de testing Docker
├── README.md                  # Este archivo
├── .windsurf/                 # Configuración Cascade
│   ├── rules/                 # Reglas del proyecto
│   └── workflows/             # Workflows automatizados
│       ├── portalinmobiliario-dev.md     # Workflow de desarrollo
│       └── portalinmobiliario-github.md  # Workflow de GitHub
├── docs/                      # Documentación completa
│   ├── README.md
│   ├── guides/
│   ├── deployment/
│   └── specs/
├── output/                    # Archivos generados (TXT/JSON/CSV)
└── venv/                      # Entorno virtual Python
```

## 📊 Formato de datos

### Datos extraídos por propiedad

- `id`: ID único de la publicación (ej: "MLC-3705621748")
- `titulo`: Título de la propiedad
- `headline`: Categoría del anuncio (ej: "Departamentos en venta")
- `precio`: Precio en formato original (ej: "UF 3.055", "$ 740.000")
- `ubicacion`: Dirección completa con comuna y sector
- `atributos`: Características (dormitorios, baños, m² útiles)
- `url`: URL completa del detalle con tracking
- `operacion`: Tipo de operación (venta, arriendo, arriendo-de-temporada)
- `tipo`: Tipo de propiedad (departamento, casa, etc.)

### Datos extraídos con `--scrape-details`

Cuando se activa el modo detalle, se extrae información adicional de la página de detalle:

- `descripcion`: Descripción completa del inmueble
- `caracteristicas.orientacion`: Orientación (Norte, Sur, Este, Oeste)
- `caracteristicas.año_construccion`: Año de construcción
- `caracteristicas.gastos_comunes`: Monto de gastos comunes (CLP)
- `caracteristicas.estacionamientos`: Cantidad de estacionamientos
- `caracteristicas.bodegas`: Cantidad de bodegas
- `publicador.nombre`: Nombre del publicador
- `publicador.tipo`: Tipo de publicador (`inmobiliaria` o `particular`)
- `imagenes`: Lista de URLs de imágenes (máx. 10)
- `coordenadas.lat`: Latitud GPS
- `coordenadas.lng`: Longitud GPS
- `fecha_publicacion`: Fecha de publicación (formato ISO: `YYYY-MM-DD`)

### Ejemplo de salida (TXT - formato JSONL)

```json
{"id": "MLC-3705621748", "titulo": "Esmeralda 6540 - Ingevec", "headline": "Departamentos en venta", "precio": "UF 3.055", "ubicacion": "Esmeralda 6540, Santiago, La Cisterna, Lo Ovalle, La Cisterna", "atributos": "1 a 2 dormitorios, 1 a 2 baños, 31 - 50 m² útiles", "url": "https://portalinmobiliario.com/MLC-3705621748-esmeralda-6540-ingevec-_JM#polycard_client=search-desktop&search_layout=grid&position=1&type=item&tracking_id=...", "operacion": "venta", "tipo": "departamento"}
{"id": "MLC-3225188606", "titulo": "Edificio Vicuña Mackenna 6896 - Norte Verde", "headline": "Departamentos en venta", "precio": "UF 3.081", "ubicacion": "Av. Vicuña Mackenna Poniente 6896, La Florida, Plaza Vespucio, La Florida", "atributos": "Estudio a 1 dormitorios, 1 baño, 23 - 33 m² útiles", "url": "https://portalinmobiliario.com/MLC-3225188606-edificio-vicuna-mackenna-6896-norte-verde-_JM#...", "operacion": "venta", "tipo": "departamento"}
```

### Ejemplo de salida (JSON estructurado)

```json
{
  "metadata": {
    "operacion": "arriendo",
    "tipo": "casa",
    "total": 48,
    "fecha_scraping": "2026-04-07T20:32:22.928350"
  },
  "propiedades": [
    {
      "id": "MLC-1474126719",
      "titulo": "Condominio Travesía Del Desierto II",
      "headline": "Casas en arriendo",
      "precio": "$ 740.000",
      "ubicacion": "Av. Circunvalación 1432, Avenida Almirante Grau, Calama",
      "atributos": "3 dormitorios, 3 baños, 64 m² útiles",
      "url": "https://portalinmobiliario.com/MLC-1474126719-condominio-travesia-del-desierto-ii-_JM#...",
      "operacion": "arriendo",
      "tipo": "casa"
    },
    {
      "id": "MLC-3841331684",
      "titulo": "Casa Mediterranea Nueva A Estrenar En Condominio",
      "headline": "Casa en arriendo",
      "precio": "UF 160",
      "ubicacion": "CONDOMINIO LOS BRAVOS, Los Trapenses, Lo Barnechea",
      "atributos": "5 dormitorios, 5 baños, 400 m² útiles",
      "url": "https://portalinmobiliario.com/MLC-3841331684-casa-mediterranea-nueva-a-estrenar-en-condominio-_JM#...",
      "operacion": "arriendo",
      "tipo": "casa"
    }
  ]
}
```

## ⚙️ Configuración

Edita el archivo `.env` para personalizar:

```env
DELAY_BETWEEN_REQUESTS=2    # Segundos entre requests
MAX_RETRIES=3               # Intentos máximos por página
TIMEOUT=30                  # Timeout de requests (segundos)
USER_AGENT=Mozilla/5.0...   # User agent personalizado
```

## 🔧 Desarrollo

### Estructura de clases

**`PortalInmobiliarioSeleniumScraper`** (scraper_selenium.py)
- `__init__(operacion, tipo, headless)`: Inicializa navegador Chrome
- `build_url(offset)`: Construye URL con paginación
- `fetch_page(url)`: Carga página con Selenium y espera contenido
- `extract_properties(driver)`: Extrae datos de propiedades del DOM
- `scrape_all_pages(max_pages, scrape_details, max_detail_properties)`: Scrapea todas las páginas con navegación
- `scrape_property_detail(property_id, property_url)`: Scrapea página de detalle de una propiedad
- `has_next_page(driver)`: Verifica si hay más páginas disponibles
- `close()`: Cierra navegador y libera recursos

**`PortalInmobiliarioScraper`** (scraper.py)
- Implementación alternativa con requests + BeautifulSoup
- Más ligera pero menos robusta para sitios dinámicos

**`DataExporter`** (exporter.py)
- `export_to_txt(properties, operacion, tipo)`: Exporta a TXT (JSONL)
- `export_to_json(properties, operacion, tipo)`: Exporta a JSON estructurado
- `export_to_csv(properties, operacion, tipo, flatten_nested)`: Exporta a CSV con headers (aplana campos anidados)
- `flatten_property(prop)`: Aplana diccionario con campos anidados para CSV

## ⚠️ Consideraciones

### Legales
- Revisa los términos de uso de portalinmobiliario.com
- Usa los datos de manera responsable
- Respeta el rate limiting

### Técnicas
- El sitio puede cambiar su estructura HTML
- Implementa delays entre requests para evitar bloqueos
- Usa un User-Agent realista

## � Deployment en Railway

Este proyecto está listo para desplegarse en Railway con PostgreSQL:

```bash
# 1. Push a GitHub
git add .
git commit -m "feat(docker): configuración Docker y Railway"
git push origin main

# 2. En Railway (https://railway.app):
# - Conectar repositorio GitHub
# - Railway detectará automáticamente el Dockerfile
# - Agregar PostgreSQL desde el dashboard
# - Configurar variables de entorno (DATABASE_URL, etc.)

# 3. Deploy automático
# Railway desplegará automáticamente en cada push a main
```

**📖 Ver [docs/deployment/DOCKER.md](docs/deployment/DOCKER.md) para guía completa de deployment en Railway.**

## �️ Migración de Datos a PostgreSQL

El proyecto incluye scripts para migrar datos scrapeados desde archivos exportados (TXT/JSON/CSV) a PostgreSQL.

### Script de Migración

```bash
# Migrar un archivo específico
python scripts/migrate_to_postgres.py output/venta_departamento_20260407.txt

# Migrar todo el directorio output/
python scripts/migrate_to_postgres.py output/

# Simular migración (dry-run)
python scripts/migrate_to_postgres.py output/ --dry-run

# Migrar con reporte JSON
python scripts/migrate_to_postgres.py output/ --report migration_report.json

# Incluir duplicados (sobrescribir)
python scripts/migrate_to_postgres.py output/ --include-duplicates

# Customizar batch size
python scripts/migrate_to_postgres.py output/ --batch-size 50
```

### Variables de Entorno

```env
DATABASE_URL=postgresql://user:password@localhost:5432/scraper_db
```

### Características

- ✅ Soporte para TXT (JSONL), JSON estructurado y CSV
- ✅ Validación de datos antes de inserción
- ✅ Detección y manejo de duplicados
- ✅ Inserción en batches para performance
- ✅ Modo dry-run para testing
- ✅ Reporte detallado de migración

**📖 Ver [docs/migration/MIGRATION-GUIDE.md](docs/migration/MIGRATION-GUIDE.md) para guía completa de migración.**

## �🗺️ Roadmap

### ✅ Fase 1 - MVP (Completado - Abril 2026)
- ✅ Scraper con Selenium (navegación real)
- ✅ Exportación TXT/JSON/CSV funcional
- ✅ Paginación automática con límites configurables
- ✅ Extracción de 9 campos por propiedad
- ✅ Dockerización completa con PostgreSQL
- ✅ Listo para Railway
- ✅ Workflow Cascade `/portalinmobiliario-dev`
- ✅ WebDriver automático con webdriver-manager
- ✅ Logging detallado con timestamps
- ✅ Manejo robusto de errores

### 📋 Fase 2 - Mejoras (Completada)
- ✅ Extracción de atributos (dormitorios, baños, m²)
- ✅ Scraping de página de detalle (descripción, características, publicador, imágenes, coordenadas GPS, fecha)
- ✅ Tests unitarios con pytest (73% coverage, excluye módulos SQLAlchemy por incompatibilidad Python 3.14)
- [ ] Logging a archivo rotativo
- ✅ Validación de datos extraídos
- ✅ Detección de duplicados

### 🚀 Fase 3 - Pro
- [ ] Uso de API interna (JSON endpoints)
- [x] Almacenamiento en PostgreSQL
- [x] Scheduler (APScheduler) para scraping automático
- [ ] Dashboard de monitoreo con métricas
- [ ] Notificaciones de errores
- [ ] Cache de resultados

### 🌟 Fase 4 - Escalamiento
- [ ] Scraping distribuido con Celery
- [ ] API REST propia (FastAPI)
- [ ] Dashboard analítico con visualizaciones
- [ ] Alertas de oportunidades (precio, ubicación)
- [ ] Machine Learning para predicción de precios
- [ ] Integración con otras plataformas inmobiliarias

## 📝 Licencia

Este proyecto es para fines educativos y de investigación.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## 📚 Documentación

Toda la documentación del proyecto está organizada en la carpeta `docs/`:

- **[docs/README.md](docs/README.md)** - Índice maestro de documentación
- **[docs/guides/QUICKSTART.md](docs/guides/QUICKSTART.md)** - Guía de inicio rápido
- **[docs/deployment/DOCKER.md](docs/deployment/DOCKER.md)** - Guía completa de Docker
- **[docs/deployment/QUICKSTART-DOCKER.md](docs/deployment/QUICKSTART-DOCKER.md)** - Docker rápido
- **[docs/specs/prd.md](docs/specs/prd.md)** - Product Requirements Document

### Workflows Cascade

- **`/portalinmobiliario-dev`** - Workflow completo de desarrollo (setup, scraping, testing)
- **`/portalinmobiliario-github`** - Workflow para subir cambios a GitHub

## 🔧 Stack Tecnológico

- **Python:** 3.14.3
- **Scraping:** Selenium 4.18.1 + BeautifulSoup4 4.12.3
- **WebDriver:** ChromeDriver 146.0.7680.165 (gestión automática)
- **Parsing:** lxml 5.1.0
- **Config:** python-dotenv 1.0.1
- **Alternativa:** requests 2.31.0 (scraper.py)
- **Docker:** Dockerfile + docker-compose con PostgreSQL
- **Deploy:** Railway-ready con railway.json
- **Automatización:** Workflows Cascade en `.windsurf/`

## �📧 Contacto

Para preguntas o sugerencias, abre un issue en el repositorio.

---

**Nota**: Este scraper está diseñado para uso responsable y educativo. Asegúrate de cumplir con los términos de servicio del sitio web.
