# 🏠 Portal Inmobiliario Scraper

Scraper automatizado en Python para extraer datos de propiedades desde [portalinmobiliario.com](https://www.portalinmobiliario.com)

## 📋 Características

- ✅ Scraping de listados de propiedades
- ✅ Navegación automática por paginación
- ✅ Configuración dinámica de operación y tipo de propiedad
- ✅ Exportación a múltiples formatos (TXT, JSON, CSV)
- ✅ Manejo robusto de errores
- ✅ Rate limiting configurable
- ✅ Logging detallado
- ✅ Retry automático en caso de fallos

## 🚀 Instalación

### Opción 1: Instalación Local

#### 1. Clonar el repositorio

```bash
cd portalinmobiliario
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

### Uso básico

```bash
python main.py --operacion venta --tipo departamento
```

### Ejemplos

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

### Parámetros disponibles

| Parámetro | Descripción | Requerido | Valores |
|-----------|-------------|-----------|---------|
| `--operacion` | Tipo de operación | ✅ | `venta`, `arriendo`, `arriendo-de-temporada` |
| `--tipo` | Tipo de propiedad | ✅ | `departamento`, `casa`, `oficina`, `terreno`, `local-comercial`, `bodega`, `estacionamiento`, `parcela` |
| `--max-pages` | Máximo de páginas a scrapear | ❌ | Número entero (default: todas) |
| `--formato` | Formato de exportación | ❌ | `txt`, `json`, `csv` (default: `txt`) |
| `--verbose` | Modo detallado | ❌ | Flag booleano |

## 📁 Estructura del proyecto

```
portalinmobiliario/
├── main.py              # Script principal
├── scraper.py           # Lógica de scraping
├── exporter.py          # Exportación de datos
├── config.py            # Configuración
├── utils.py             # Utilidades
├── requirements.txt     # Dependencias
├── .env.example         # Ejemplo de configuración
├── .gitignore          # Archivos ignorados
├── prd.md              # Product Requirements Document
├── README.md           # Este archivo
└── output/             # Directorio de salidas (se crea automáticamente)
```

## 📊 Formato de datos

### Datos extraídos por propiedad

- `id`: ID de la publicación
- `titulo`: Título de la propiedad
- `precio`: Precio (en formato texto)
- `ubicacion`: Ubicación/dirección
- `url`: URL del detalle
- `operacion`: Tipo de operación
- `tipo`: Tipo de propiedad

### Ejemplo de salida (TXT)

```json
{"id": "MLC123456", "titulo": "Departamento 2D 2B en Las Condes", "precio": "150000000", "ubicacion": "Las Condes, Santiago", "url": "https://...", "operacion": "venta", "tipo": "departamento"}
{"id": "MLC123457", "titulo": "Casa 3D 2B en Providencia", "precio": "200000000", "ubicacion": "Providencia, Santiago", "url": "https://...", "operacion": "venta", "tipo": "casa"}
```

### Ejemplo de salida (JSON)

```json
{
  "metadata": {
    "operacion": "venta",
    "tipo": "departamento",
    "total": 150,
    "fecha_scraping": "2026-03-18T10:30:00"
  },
  "propiedades": [
    {
      "id": "MLC123456",
      "titulo": "Departamento 2D 2B en Las Condes",
      "precio": "150000000",
      "ubicacion": "Las Condes, Santiago",
      "url": "https://...",
      "operacion": "venta",
      "tipo": "departamento"
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

**`PortalInmobiliarioScraper`**
- `build_url(offset)`: Construye URL con paginación
- `fetch_page(url)`: Obtiene y parsea página
- `extract_properties(soup)`: Extrae datos de propiedades
- `scrape_all_pages(max_pages)`: Scrapea todas las páginas
- `has_next_page(soup)`: Verifica si hay más páginas

**`DataExporter`**
- `export_to_txt()`: Exporta a TXT
- `export_to_json()`: Exporta a JSON
- `export_to_csv()`: Exporta a CSV

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

## �🗺️ Roadmap

### ✅ Fase 1 - MVP (Actual)
- Scraper básico
- Exportación TXT/JSON/CSV
- Paginación funcional
- Dockerización completa
- Listo para Railway

### 📋 Fase 2 - Mejoras
- [ ] Scraping de página de detalle
- [ ] Extracción de más campos (m², dormitorios, baños)
- [ ] Logging a archivo
- [ ] Tests unitarios

### 🚀 Fase 3 - Pro
- [ ] Uso de API interna (JSON endpoints)
- [x] Almacenamiento en base de datos
- [ ] Scheduler (cron jobs)
- [ ] Dashboard de monitoreo

### 🌟 Fase 4 - Escalamiento
- [ ] Scraping distribuido
- [ ] API REST propia
- [ ] Dashboard analítico
- [ ] Alertas de oportunidades

## 📝 Licencia

Este proyecto es para fines educativos y de investigación.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## � Documentación

Toda la documentación del proyecto está organizada en la carpeta `docs/`:

- **[docs/README.md](docs/README.md)** - Índice maestro de documentación
- **[docs/guides/QUICKSTART.md](docs/guides/QUICKSTART.md)** - Guía de inicio rápido
- **[docs/deployment/DOCKER.md](docs/deployment/DOCKER.md)** - Guía completa de Docker
- **[docs/deployment/QUICKSTART-DOCKER.md](docs/deployment/QUICKSTART-DOCKER.md)** - Docker rápido
- **[docs/specs/prd.md](docs/specs/prd.md)** - Product Requirements Document

## �📧 Contacto

Para preguntas o sugerencias, abre un issue en el repositorio.

---

**Nota**: Este scraper está diseñado para uso responsable y educativo. Asegúrate de cumplir con los términos de servicio del sitio web.
