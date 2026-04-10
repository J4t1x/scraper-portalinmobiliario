# Convenciones de Código — Portal Inmobiliario Scraper

**Última actualización:** Abril 2026

---

## 🎨 Python Style Guide

### PEP 8 Compliance

Seguimos [PEP 8](https://peps.python.org/pep-0008/) con las siguientes especificaciones:

- **Longitud de línea:** Máximo 100 caracteres (más flexible que 79)
- **Indentación:** 4 espacios (no tabs)
- **Encoding:** UTF-8
- **Imports:** Agrupados y ordenados

### Naming Conventions

| Elemento | Convención | Ejemplo |
|----------|------------|---------|
| **Archivos** | snake_case | `scraper_selenium.py` |
| **Clases** | PascalCase | `PortalInmobiliarioScraper` |
| **Funciones** | snake_case | `scrape_all_pages()` |
| **Variables** | snake_case | `property_data` |
| **Constantes** | UPPER_CASE | `MAX_RETRIES` |
| **Privadas** | _prefijo | `_extract_id()` |

---

## 📦 Estructura de Imports

```python
# 1. Standard library
import os
import sys
import json
from typing import List, Dict, Optional
from datetime import datetime

# 2. Third party
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By

# 3. Local
from config import Config
from utils import retry_on_failure, setup_logger
from exporter import DataExporter
```

---

## 🏗️ Estructura de Clases

### Template de Clase

```python
class PropertyScraper:
    """
    Scraper para extraer datos de propiedades.
    
    Attributes:
        operacion (str): Tipo de operación (venta, arriendo)
        tipo (str): Tipo de propiedad (departamento, casa)
        headless (bool): Modo headless para Selenium
    """
    
    def __init__(self, operacion: str, tipo: str, headless: bool = True):
        """
        Inicializar scraper.
        
        Args:
            operacion: Tipo de operación
            tipo: Tipo de propiedad
            headless: Si usar modo headless
        
        Raises:
            ValueError: Si operacion o tipo son inválidos
        """
        self.operacion = operacion
        self.tipo = tipo
        self.headless = headless
        self._driver = None
    
    def scrape(self) -> List[Dict]:
        """
        Scrapear propiedades.
        
        Returns:
            Lista de diccionarios con datos de propiedades
        
        Raises:
            TimeoutException: Si hay timeout
            WebDriverException: Si hay error de WebDriver
        """
        pass
    
    def _extract_data(self, element) -> Dict:
        """Método privado para extraer datos."""
        pass
    
    def close(self):
        """Liberar recursos."""
        if self._driver:
            self._driver.quit()
```

---

## 📝 Docstrings

### Formato: Google Style

```python
def scrape_property_detail(property_id: str, url: str) -> Dict:
    """
    Scrapear página de detalle de una propiedad.
    
    Navega a la página de detalle y extrae información adicional
    como descripción, características, publicador, imágenes y coordenadas.
    
    Args:
        property_id: ID único de la propiedad (ej: "MLC-3705621748")
        url: URL completa de la página de detalle
    
    Returns:
        Diccionario con datos adicionales:
            - descripcion (str): Descripción completa
            - caracteristicas (dict): Orientación, año, gastos comunes
            - publicador (dict): Nombre y tipo
            - imagenes (list): URLs de imágenes
            - coordenadas (dict): Latitud y longitud
            - fecha_publicacion (str): Fecha en formato ISO
    
    Raises:
        TimeoutException: Si la página no carga en TIMEOUT segundos
        ValueError: Si property_id es inválido
        WebDriverException: Si hay error de navegación
    
    Example:
        >>> scraper = PortalInmobiliarioScraper('venta', 'departamento')
        >>> detail = scraper.scrape_property_detail(
        ...     'MLC-123',
        ...     'https://portalinmobiliario.com/MLC-123'
        ... )
        >>> print(detail['descripcion'])
        'Hermoso departamento...'
    """
    pass
```

---

## 🔧 Type Hints

### Uso Obligatorio

```python
from typing import List, Dict, Optional, Union, Tuple

# Funciones
def extract_properties(driver: webdriver.Chrome) -> List[Dict[str, str]]:
    pass

# Variables
properties: List[Dict] = []
price: Optional[str] = None
result: Union[str, int] = "value"

# Retornos múltiples
def validate_property(prop: Dict) -> Tuple[bool, List[str]]:
    return True, []
```

---

## 🪵 Logging

### Configuración

```python
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Handler
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)
```

### Niveles de Log

```python
# DEBUG: Información detallada para debugging
logger.debug(f"Selector usado: {selector}")

# INFO: Progreso general
logger.info(f"Scrapeando página {page_num}/{total_pages}")

# WARNING: Situaciones inesperadas pero manejables
logger.warning(f"Propiedad {prop_id} sin precio")

# ERROR: Errores que impiden operación
logger.error(f"Error al cargar página: {e}")

# CRITICAL: Errores críticos del sistema
logger.critical("WebDriver falló completamente")
```

---

## ⚠️ Manejo de Errores

### Try-Except Pattern

```python
from utils import retry_on_failure

@retry_on_failure(max_retries=3, delay=2)
def fetch_page(url: str) -> webdriver.Chrome:
    """Cargar página con retry automático."""
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".results"))
        )
        return driver
    except TimeoutException as e:
        logger.error(f"Timeout al cargar {url}: {e}")
        raise
    except WebDriverException as e:
        logger.error(f"Error de WebDriver: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        raise
```

### Errores Específicos

```python
# Validación de inputs
if operacion not in OPERACIONES_VALIDAS:
    raise ValueError(f"Operación inválida: {operacion}")

# Recursos no encontrados
if not element:
    raise ElementNotFoundError(f"Elemento no encontrado: {selector}")

# Timeouts
if time.time() - start_time > TIMEOUT:
    raise TimeoutError(f"Timeout después de {TIMEOUT}s")
```

---

## 🧪 Testing

### Naming de Tests

```python
# Formato: test_<función>_<escenario>_<resultado_esperado>

def test_build_url_venta_departamento_returns_correct_url():
    pass

def test_extract_price_invalid_format_raises_value_error():
    pass

def test_scrape_all_pages_with_max_pages_stops_at_limit():
    pass
```

### Estructura de Test

```python
import pytest
from scraper_selenium import PortalInmobiliarioScraper

class TestScraper:
    """Tests para PortalInmobiliarioScraper."""
    
    @pytest.fixture
    def scraper(self):
        """Fixture para crear scraper."""
        return PortalInmobiliarioScraper('venta', 'departamento')
    
    def test_init_valid_params(self, scraper):
        """Test de inicialización con parámetros válidos."""
        assert scraper.operacion == 'venta'
        assert scraper.tipo == 'departamento'
    
    def test_build_url_includes_operacion(self, scraper):
        """Test que URL incluye operación."""
        url = scraper.build_url()
        assert 'venta' in url
    
    @pytest.mark.parametrize("operacion,tipo", [
        ('venta', 'departamento'),
        ('arriendo', 'casa'),
        ('arriendo-de-temporada', 'oficina')
    ])
    def test_build_url_multiple_combinations(self, operacion, tipo):
        """Test con múltiples combinaciones."""
        scraper = PortalInmobiliarioScraper(operacion, tipo)
        url = scraper.build_url()
        assert operacion in url
        assert tipo in url
```

---

## 📁 Estructura de Archivos

### Organización

```
scraper-portalinmobiliario/
├── main.py                    # Entry point (CLI)
├── scraper_selenium.py        # Scraper principal
├── scraper.py                 # Scraper alternativo
├── exporter.py                # Exportación de datos
├── validator.py               # Validación de datos
├── deduplicator.py            # Deduplicación
├── config.py                  # Configuración centralizada
├── utils.py                   # Utilidades compartidas
├── requirements.txt           # Dependencias
├── .env                       # Variables de entorno (no commitear)
├── .env.example               # Template de .env
├── Dockerfile                 # Imagen Docker
├── docker-compose.yml         # Orquestación
├── tests/                     # Tests
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/                      # Documentación
│   ├── README.md
│   ├── ARCHITECTURE.md
│   ├── STATUS.md
│   └── CONVENTIONS.md
└── output/                    # Archivos generados
```

---

## 🔐 Configuración

### Variables de Entorno

```python
# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuración centralizada."""
    
    # Scraping
    DELAY_BETWEEN_REQUESTS = int(os.getenv('DELAY_BETWEEN_REQUESTS', 2))
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))
    TIMEOUT = int(os.getenv('TIMEOUT', 30))
    
    # User Agent
    USER_AGENT = os.getenv('USER_AGENT', 'Mozilla/5.0...')
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    # Validación
    @classmethod
    def validate(cls):
        """Validar configuración."""
        if cls.DELAY_BETWEEN_REQUESTS < 1:
            raise ValueError("DELAY_BETWEEN_REQUESTS debe ser >= 1")
```

---

## 📊 Formato de Datos

### Nombres de Campos

```python
# Usar snake_case para keys
property_data = {
    'id': 'MLC-123',
    'titulo': 'Departamento',
    'precio': 'UF 3.055',
    'ubicacion': 'Santiago',
    'atributos': '2 dorm, 1 baño',
    'url': 'https://...',
    'operacion': 'venta',
    'tipo': 'departamento',
    'caracteristicas': {
        'orientacion': 'Norte',
        'año_construccion': 2020,
        'gastos_comunes': 50000
    },
    'coordenadas': {
        'lat': -33.4372,
        'lng': -70.6506
    }
}
```

### Nombres de Archivos

```python
# Formato: {operacion}_{tipo}_{timestamp}.{ext}
from datetime import datetime

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
filename = f"{operacion}_{tipo}_{timestamp}.json"
# Ejemplo: venta_departamento_20260407_203045.json
```

---

## 🔄 Git Workflow

### Conventional Commits

```bash
# Formato
<tipo>(<scope>): <descripción>

[cuerpo opcional]

[footer opcional]
```

### Tipos

- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `docs`: Documentación
- `style`: Formato (no afecta código)
- `refactor`: Refactorización
- `test`: Tests
- `build`: Build/dependencias
- `ci`: CI/CD
- `chore`: Mantenimiento

### Ejemplos

```bash
feat(scraper): agregar scraping de imágenes

Implementa extracción de URLs de imágenes desde página de detalle.
Máximo 10 imágenes por propiedad.

Closes #15

---

fix(exporter): corregir encoding UTF-8 en CSV

El encoding no se especificaba correctamente al exportar CSV,
causando caracteres corruptos.

---

docs: actualizar README con nuevos parámetros CLI

---

refactor(config): centralizar variables de entorno en Config class
```

---

## ✅ Checklist Pre-Commit

Antes de hacer commit, verificar:

- [ ] Código sigue PEP 8
- [ ] Type hints agregados
- [ ] Docstrings completos
- [ ] Tests agregados/actualizados
- [ ] Tests pasan (`pytest`)
- [ ] No hay prints (usar logging)
- [ ] No hay credenciales hardcodeadas
- [ ] `.env` no está en commit
- [ ] Documentación actualizada
- [ ] Commit message sigue Conventional Commits

---

**Última revisión:** Abril 2026
