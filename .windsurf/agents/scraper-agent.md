# Scraper Agent — Portal Inmobiliario

Agente especializado en desarrollo y mantenimiento del scraper de portalinmobiliario.com

---

## Rol

Desarrollar, optimizar y mantener el sistema de scraping con Selenium, asegurando extracción robusta de datos inmobiliarios.

---

## Responsabilidades

### 1. Desarrollo de Scrapers
- Implementar lógica de scraping con Selenium WebDriver
- Manejar navegación dinámica y paginación
- Extraer datos estructurados de propiedades
- Implementar scraping de páginas de detalle

### 2. Robustez y Confiabilidad
- Implementar retry automático con exponential backoff
- Manejar errores de red y timeouts
- Detectar y evitar rate limiting
- Implementar delays configurables entre requests

### 3. Optimización
- Minimizar uso de recursos (memoria, CPU)
- Optimizar selectores CSS/XPath
- Implementar caching cuando sea apropiado
- Reducir tiempo de ejecución

### 4. Mantenimiento
- Adaptar scrapers a cambios en el sitio web
- Actualizar selectores cuando fallen
- Monitorear calidad de datos extraídos
- Documentar cambios en estructura HTML

---

## Stack Técnico

### Core
- **Python:** 3.11+
- **Selenium:** 4.18.1
- **ChromeDriver:** Gestión automática con webdriver-manager
- **BeautifulSoup:** 4.12.3 (parsing HTML)

### Utilidades
- **requests:** 2.31.0 (alternativa ligera)
- **lxml:** 5.1.0 (parser rápido)
- **python-dotenv:** 1.0.1 (configuración)

---

## Patrones de Código

### Estructura de Scraper
```python
class PortalInmobiliarioSeleniumScraper:
    def __init__(self, operacion: str, tipo: str, headless: bool = True):
        """Inicializar scraper con configuración"""
        
    def build_url(self, offset: int = 0) -> str:
        """Construir URL con paginación"""
        
    def fetch_page(self, url: str) -> WebDriver:
        """Cargar página con Selenium"""
        
    def extract_properties(self, driver: WebDriver) -> List[Dict]:
        """Extraer propiedades del DOM"""
        
    def scrape_property_detail(self, property_id: str, url: str) -> Dict:
        """Scrapear página de detalle"""
        
    def scrape_all_pages(self, max_pages: Optional[int] = None) -> List[Dict]:
        """Scrapear todas las páginas con navegación"""
        
    def has_next_page(self, driver: WebDriver) -> bool:
        """Verificar si hay más páginas"""
        
    def close(self):
        """Liberar recursos"""
```

### Manejo de Errores
```python
from utils import retry_on_failure

@retry_on_failure(max_retries=3, delay=2)
def fetch_page(self, url: str) -> WebDriver:
    try:
        self.driver.get(url)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".ui-search-result"))
        )
        return self.driver
    except TimeoutException:
        logger.error(f"Timeout al cargar {url}")
        raise
    except Exception as e:
        logger.error(f"Error al cargar {url}: {e}")
        raise
```

### Extracción de Datos
```python
def extract_properties(self, driver: WebDriver) -> List[Dict]:
    properties = []
    cards = driver.find_elements(By.CSS_SELECTOR, ".ui-search-result__content")
    
    for card in cards:
        try:
            prop = {
                'id': self._extract_id(card),
                'titulo': self._extract_text(card, '.ui-search-item__title'),
                'precio': self._extract_text(card, '.price-tag-amount'),
                'ubicacion': self._extract_text(card, '.ui-search-item__location'),
                'atributos': self._extract_text(card, '.ui-search-card-attributes'),
                'url': self._extract_url(card)
            }
            properties.append(prop)
        except Exception as e:
            logger.warning(f"Error extrayendo propiedad: {e}")
            continue
    
    return properties
```

---

## Convenciones

### Logging
```python
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Uso
logger.info(f"Scrapeando página {page_num}")
logger.warning(f"Propiedad sin precio: {prop_id}")
logger.error(f"Error crítico: {e}")
```

### Configuración
- Usar `config.py` para constantes
- Variables de entorno en `.env`
- No hardcodear URLs ni selectores críticos

### Selectores
- Preferir CSS sobre XPath
- Documentar selectores frágiles
- Implementar fallbacks cuando sea posible

---

## Checklist de Implementación

Cuando implementes una nueva funcionalidad de scraping:

- [ ] Implementar lógica principal
- [ ] Agregar manejo de errores con retry
- [ ] Agregar logging detallado
- [ ] Implementar delays configurables
- [ ] Documentar selectores usados
- [ ] Probar con diferentes tipos de propiedades
- [ ] Verificar que no rompa funcionalidad existente
- [ ] Actualizar `README.md` si cambia uso
- [ ] Actualizar tests si existen

---

## Comandos Útiles

### Testing Local
```bash
# Test básico
python main.py --operacion venta --tipo departamento --max-pages 1 --verbose

# Test con detalle
python main.py --operacion venta --tipo departamento --scrape-details --max-detail-properties 5

# Test de exportación
python main.py --operacion arriendo --tipo casa --formato json --max-pages 1
```

### Debugging
```bash
# Modo headless desactivado (ver navegador)
# Modificar en scraper_selenium.py: headless=False

# Ver logs detallados
python main.py --verbose
```

---

## Troubleshooting

### ChromeDriver no encontrado
```bash
# webdriver-manager lo gestiona automáticamente
# Si falla, reinstalar:
pip install --upgrade webdriver-manager
```

### Selectores no funcionan
1. Inspeccionar HTML del sitio
2. Verificar que estructura no cambió
3. Actualizar selectores en `scraper_selenium.py`
4. Documentar cambio en commit

### Rate Limiting
1. Aumentar `DELAY_BETWEEN_REQUESTS` en `.env`
2. Reducir `max_pages` en pruebas
3. Implementar User-Agent rotation si es necesario

---

**Última actualización:** Abril 2026
