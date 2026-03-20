# Reglas de Contexto - Portal Inmobiliario Scraper

**Proyecto:** scraper-portalinmobiliario  
**Tipo:** Python Scraper + Docker  
**Última actualización:** 20 de Marzo, 2026

---

## 🎯 Propósito del Proyecto

Scraper automatizado en Python para extraer datos de propiedades desde portalinmobiliario.com con capacidades de:
- Scraping dinámico con Selenium
- Exportación múltiple (TXT, JSON, CSV)
- Dockerización completa
- Deployment en Railway con PostgreSQL

---

## 🏗️ Stack Tecnológico

### Backend/Scraper
- **Python:** 3.11+
- **Web Scraping:** Selenium 4.18.1 + BeautifulSoup 4.12.3
- **HTTP:** requests 2.31.0
- **Parsing:** lxml 5.1.0
- **Config:** python-dotenv 1.0.1
- **WebDriver:** webdriver-manager 4.0.1

### Infraestructura
- **Docker:** Python 3.11-slim + Chrome + ChromeDriver
- **Database:** PostgreSQL 15 (Railway)
- **Deployment:** Railway
- **CI/CD:** GitHub Actions

---

## 📁 Estructura del Proyecto

```
scraper-portalinmobiliario/
├── main.py                 # Script principal (CLI)
├── scraper_selenium.py     # Lógica de scraping con Selenium
├── scraper.py              # Scraper alternativo (requests)
├── exporter.py             # Exportación de datos
├── config.py               # Configuración centralizada
├── utils.py                # Utilidades
├── requirements.txt        # Dependencias Python
├── .env.example            # Template de variables de entorno
├── Dockerfile              # Imagen Docker
├── docker-compose.yml      # Orquestación local
├── entrypoint.sh           # Script de entrada Docker
├── railway.json            # Config Railway
├── test-docker.sh          # Testing automatizado
├── docs/                   # Documentación organizada
│   ├── README.md           # Índice maestro
│   ├── deployment/         # Guías de deployment
│   ├── guides/             # Guías de uso
│   └── specs/              # Especificaciones
├── .github/workflows/      # CI/CD
└── .windsurf/              # Configuración Cascade
    ├── rules/              # Reglas de contexto
    └── workflows/          # Workflows de desarrollo
```

---

## 🎨 Convenciones de Código

### Python Style
- **PEP 8** style guide
- **Type hints** recomendados
- **Docstrings** en funciones públicas
- **Logging** en lugar de prints

### Naming
- **Archivos:** snake_case (ej: `scraper_selenium.py`)
- **Clases:** PascalCase (ej: `PortalInmobiliarioScraper`)
- **Funciones/Variables:** snake_case (ej: `scrape_all_pages`)
- **Constantes:** UPPER_CASE (ej: `MAX_RETRIES`)

### Imports
```python
# Standard library
import os
import sys

# Third party
import requests
from bs4 import BeautifulSoup

# Local
from config import Config
from utils import retry_on_failure
```

---

## 🔧 Configuración

### Variables de Entorno
| Variable | Default | Descripción |
|----------|---------|-------------|
| `DATABASE_URL` | - | Conexión PostgreSQL (Railway) |
| `DELAY_BETWEEN_REQUESTS` | 2 | Segundos entre requests |
| `MAX_RETRIES` | 3 | Intentos máximos |
| `TIMEOUT` | 30 | Timeout en segundos |
| `USER_AGENT` | Mozilla/5.0... | User agent |

### Archivos de Config
- `.env` - Variables locales (no commitear)
- `.env.example` - Template de ejemplo
- `config.py` - Configuración centralizada

---

## 🐳 Docker

### Build
```bash
docker build -t scraper-portalinmobiliario:latest .
```

### Run
```bash
docker run --rm \
  -v $(pwd)/output:/app/output \
  scraper-portalinmobiliario:latest \
  python main.py --operacion venta --tipo departamento
```

### Compose
```bash
docker-compose up -d
docker-compose run --rm scraper python main.py --help
```

---

## 📝 Commits (Conventional Commits)

### Formato
```
<tipo>(<scope>): <descripción>
```

### Tipos
- `feat` - Nueva funcionalidad
- `fix` - Corrección de bug
- `docs` - Documentación
- `style` - Formato (no afecta código)
- `refactor` - Refactorización
- `test` - Tests
- `build` - Build/dependencias
- `ci` - CI/CD
- `chore` - Mantenimiento

### Ejemplos
```bash
feat(scraper): agregar soporte para arriendo-temporada
fix(exporter): corregir encoding UTF-8 en CSV
docs: actualizar guía de deployment Railway
refactor(config): centralizar variables de entorno
```

---

## 🧪 Testing

### Local
```bash
python main.py --operacion venta --tipo departamento --max-pages 1 --verbose
```

### Docker
```bash
./test-docker.sh
```

---

## 📚 Documentación

### Estructura
- `docs/README.md` - Índice maestro
- `docs/deployment/` - Guías de deployment
- `docs/guides/` - Guías de uso
- `docs/specs/` - Especificaciones

### Actualización
Al modificar funcionalidad, actualizar:
1. `README.md` - Si cambia uso general
2. `docs/deployment/DOCKER.md` - Si cambia Docker
3. `docs/specs/prd.md` - Si cambia alcance

---

## 🚀 Deployment

### Railway
1. Push a GitHub
2. Railway detecta Dockerfile
3. Agregar PostgreSQL
4. Configurar variables de entorno
5. Deploy automático

Ver: `docs/deployment/DOCKER.md`

---

## ⚠️ Consideraciones Importantes

### Legales
- Respetar términos de uso de portalinmobiliario.com
- Uso responsable de datos
- Rate limiting obligatorio

### Técnicas
- Sitio puede cambiar estructura HTML
- Implementar delays entre requests
- User-Agent realista
- Manejo robusto de errores

### Seguridad
- No commitear `.env`
- No hardcodear credenciales
- Usuario no-root en Docker

---

## 🔄 Workflow de Desarrollo

1. **Crear rama:** `git checkout -b feat/nueva-funcionalidad`
2. **Desarrollar:** Código + tests
3. **Commit:** Conventional Commits
4. **Push:** `git push origin feat/nueva-funcionalidad`
5. **PR:** Crear Pull Request
6. **Review:** Code review
7. **Merge:** A main
8. **Deploy:** Automático en Railway

---

## 📊 Roadmap

### ✅ Fase 1 - MVP (Completado)
- Scraper básico
- Exportación TXT/JSON/CSV
- Dockerización
- Railway ready

### 🚧 Fase 2 - En Progreso
- Tests automatizados
- CI/CD completo

### 📋 Fase 3 - Próximo
- Scraping de detalle
- PostgreSQL integration
- Dashboard

---

## 🛠️ Regla de Auto-Mantenimiento

**Importante:** Cada vez que Cascade modifique este proyecto, debe:

1. ✅ Verificar que los cambios siguen las convenciones de este archivo
2. ✅ Actualizar documentación relevante en `docs/`
3. ✅ Usar Conventional Commits
4. ✅ Mantener estructura de carpetas
5. ✅ No romper compatibilidad con Docker/Railway

---

**Última revisión:** 20 de Marzo, 2026
