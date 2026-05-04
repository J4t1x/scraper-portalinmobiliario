import time
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from config import Config
from validator import DataValidator, validate_properties_batch
from logger_config import get_logger, log_performance
from feature_mapper import normalize_key, map_feature, parse_int, parse_money

logger = get_logger(__name__)


# Amenity keywords used to classify extra specs/services from the PDP.
# Matching is done on the normalized key (lowercase, no accents).
AMENITY_KEYWORDS = {
    'piscina', 'gimnasio', 'quincho', 'sala_de_eventos', 'salon_de_eventos',
    'lavanderia', 'porteria', 'porteria_24_horas', 'areas_verdes', 'seguridad',
    'ascensor', 'ascensores', 'juegos_infantiles', 'sala_multiuso', 'cowork',
    'rooftop', 'bicicletero', 'sala_de_cine', 'spa', 'sauna', 'jacuzzi',
    'cancha_de_tenis', 'cancha_de_futbol', 'conserjeria', 'control_de_acceso',
    'citofono', 'terraza', 'jardin', 'patio', 'balcon', 'logia',
    'calefaccion', 'aire_acondicionado', 'camaras_de_seguridad',
}

SERVICE_KEYWORDS = {
    'agua_caliente', 'gas', 'internet', 'cable', 'television_por_cable',
    'telefono', 'luz', 'electricidad',
}


def get_optimized_chrome_options(headless: bool = True) -> Options:
    """
    Chrome options optimizadas para bajo consumo de recursos
    Reduce RAM en ~200 MB y CPU en ~15%
    
    Args:
        headless: Si True, ejecuta en modo headless
        
    Returns:
        Options configuradas para máxima eficiencia
    """
    options = Options()
    
    # Headless mode (nuevo modo más eficiente)
    if headless:
        options.add_argument('--headless=new')
    
    # Memory optimizations (crítico para reducir RAM)
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
    
    # Performance optimizations
    options.add_argument('--disable-setuid-sandbox')
    options.add_argument('--memory-pressure-off')
    options.add_argument('--max-old-space-size=512')
    options.add_argument('--js-flags=--max-old-space-size=512')
    
    # Anti-detection (mantener funcionalidad)
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument(f'user-agent={Config.USER_AGENT}')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    return options


class PortalInmobiliarioSeleniumScraper:
    """Scraper usando Selenium para manejar JavaScript"""
    
    def __init__(self, operacion: str, tipo_propiedad: str, headless: bool = True, validate: bool = True, persist_to_db: bool = False):
        """
        Inicializa el scraper con Selenium
        
        Args:
            operacion: Tipo de operación
            tipo_propiedad: Tipo de propiedad
            headless: Ejecutar sin interfaz gráfica
            validate: Si es True, valida las propiedades antes de agregarlas
            persist_to_db: Si es True, persiste propiedades en PostgreSQL
        """
        if operacion not in Config.OPERACIONES:
            raise ValueError(f"Operación '{operacion}' no válida")
        
        if tipo_propiedad not in Config.TIPOS_PROPIEDAD:
            raise ValueError(f"Tipo de propiedad '{tipo_propiedad}' no válido")
        
        self.operacion = operacion
        self.tipo_propiedad = tipo_propiedad
        self.propiedades = []
        self.validate = validate
        self.validator = DataValidator() if validate else None
        self.validation_stats = {'valid': 0, 'invalid': 0, 'warnings': 0}
        self.persist_to_db = persist_to_db
        
        # Usar chrome options optimizadas (reduce RAM en ~200MB)
        chrome_options = get_optimized_chrome_options(headless=headless)
        
        # Detectar si estamos usando Chromium (contenedor) o Chrome (local)
        import os
        import shutil
        
        chromium_path = shutil.which('chromium')
        chromedriver_system = shutil.which('chromedriver')
        
        if chromium_path and chromedriver_system:
            # Usar Chromium del sistema (contenedor)
            logger.info("Usando Chromium del sistema...")
            chrome_options.binary_location = chromium_path
            service = Service(chromedriver_system)
        else:
            # Usar Chrome con ChromeDriverManager (local)
            logger.info("Inicializando navegador Chrome...")
            driver_path = ChromeDriverManager().install()
            
            # Corregir path si apunta al archivo incorrecto
            if 'THIRD_PARTY_NOTICES' in driver_path or not driver_path.endswith('chromedriver'):
                driver_dir = os.path.dirname(driver_path)
                chromedriver_path = os.path.join(driver_dir, 'chromedriver')
                if os.path.exists(chromedriver_path):
                    driver_path = chromedriver_path
            
            service = Service(driver_path)
        
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 30)
        
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def build_url(self, offset: int = 0) -> str:
        """Construye la URL"""
        base = f"{Config.BASE_URL}/{self.operacion}/{self.tipo_propiedad}"
        if offset > 0:
            return f"{base}_Desde_{offset}"
        return base
    
    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Carga página con Selenium y espera a que se cargue el contenido
        
        Args:
            url: URL a cargar
            
        Returns:
            BeautifulSoup object o None
        """
        try:
            logger.info(f"Cargando página: {url}")
            self.driver.get(url)
            
            logger.info("Esperando a que se cargue el contenido...")
            time.sleep(5)
            
            try:
                self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "li.ui-search-layout__item, div.ui-search-result, article"))
                )
                logger.info("Contenido cargado")
            except:
                logger.warning("Timeout esperando elementos, continuando de todas formas...")
            
            page_source = self.driver.page_source
            return BeautifulSoup(page_source, 'lxml')
            
        except Exception as e:
            logger.error(f"Error cargando página: {e}")
            return None
    
    def extract_properties(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extrae propiedades de la página"""
        properties = []
        
        try:
            selectors = [
                'li.ui-search-layout__item',
                'div.ui-search-result',
                'article',
                'div[data-id]'
            ]
            
            listings = []
            for selector in selectors:
                listings = soup.select(selector)
                if listings:
                    logger.info(f"Encontrados {len(listings)} listados con selector: {selector}")
                    break
            
            if not listings:
                logger.warning("No se encontraron listados")
                return properties
            
            for listing in listings:
                try:
                    property_data = self._extract_property_data(listing)
                    if property_data:
                        properties.append(property_data)
                except Exception as e:
                    logger.debug(f"Error extrayendo propiedad: {e}")
                    continue
            
            logger.info(f"Extraídas {len(properties)} propiedades")
            
        except Exception as e:
            logger.error(f"Error en extract_properties: {e}")
        
        return properties
    
    # Mapeo de palabras clave en el headline (en plural/singular, sin acentos) → tipo canónico.
    # Usado por _infer_tipo para clasificar cada propiedad por su contenido real, no por el parámetro CLI.
    _HEADLINE_TIPO_KEYWORDS = [
        ('departamento', 'departamento'),
        ('casa', 'casa'),
        ('oficina', 'oficina'),
        ('local comercial', 'local-comercial'),
        ('local', 'local-comercial'),
        ('bodega', 'bodega'),
        ('estacionamiento', 'estacionamiento'),
        ('parcela', 'parcela'),
        ('terreno', 'terreno'),
        ('sitio', 'terreno'),
    ]

    def _infer_tipo(self, headline: str, titulo: str = '', atributos: str = '') -> str:
        """
        Infiere el tipo real de propiedad a partir de su contenido (headline/título/atributos).

        Portal Inmobiliario mezcla resultados destacados de otras categorías en las páginas
        de listado, por lo que no podemos confiar en `self.tipo_propiedad` para etiquetar.

        Args:
            headline: Texto del headline (p.ej. "Departamentos en venta").
            titulo: Título de la propiedad (fallback).
            atributos: Texto de atributos (último fallback).

        Returns:
            Tipo canónico de Config.TIPOS_PROPIEDAD. Si no se detecta nada, devuelve
            self.tipo_propiedad como fallback.
        """
        haystack = ' '.join(filter(None, [headline, titulo, atributos])).lower()
        if not haystack:
            return self.tipo_propiedad
        for keyword, canonical in self._HEADLINE_TIPO_KEYWORDS:
            if keyword in haystack:
                return canonical
        return self.tipo_propiedad

    def _extract_property_data(self, listing) -> Optional[Dict[str, any]]:
        """Extrae datos de una propiedad desde el listado."""
        try:
            import re

            # Título
            titulo = "N/A"
            titulo_elem = listing.select_one('a.poly-component__title')
            if titulo_elem:
                titulo = titulo_elem.get_text(strip=True)

            # Headline
            headline = "N/A"
            headline_elem = listing.select_one('span.poly-component__headline')
            if headline_elem:
                headline = headline_elem.get_text(strip=True)

            # Precio actual
            precio = "N/A"
            precio_elem = listing.select_one('.poly-price__current span.andes-money-amount__fraction')
            if precio_elem:
                precio = precio_elem.get_text(strip=True)

            moneda = ""
            moneda_elem = listing.select_one('.poly-price__current span.andes-money-amount__currency-symbol')
            if moneda_elem:
                moneda = moneda_elem.get_text(strip=True)

            # Precio anterior (si hay descuento)
            precio_anterior = None
            prev_elem = listing.select_one('s.andes-money-amount--previous span.andes-money-amount__fraction, .poly-price__previous span.andes-money-amount__fraction')
            if prev_elem:
                precio_anterior = parse_money(prev_elem.get_text(strip=True))

            # Ubicación
            ubicacion = "N/A"
            ubicacion_elem = listing.select_one('span.poly-component__location')
            if ubicacion_elem:
                ubicacion = ubicacion_elem.get_text(strip=True)

            # Atributos
            atributos = []
            atributos_elems = listing.select('ul.poly-attributes_list li.poly-attributes_list__item')
            for attr in atributos_elems:
                atributos.append(attr.get_text(strip=True))

            # URL
            url = "N/A"
            link_elem = listing.select_one('a.poly-component__title')
            if link_elem:
                url = link_elem.get('href', 'N/A')

            # Tags / highlights (p.ej. "OPORTUNIDAD", "NUEVO")
            tags = []
            for tag_elem in listing.select('.poly-component__highlight, .poly-pill, .ui-search-item__highlight-label'):
                t = tag_elem.get_text(strip=True)
                if t:
                    tags.append(t)

            # Thumbnail
            thumbnail = None
            img_elem = listing.select_one('img.poly-component__picture, img.ui-search-result-image__element')
            if img_elem:
                thumbnail = (
                    img_elem.get('data-src')
                    or img_elem.get('data-lazy')
                    or img_elem.get('src')
                )

            # Número de fotos (badge de galería si está presente)
            num_fotos = None
            photos_elem = listing.select_one('.ui-search-result__image-counter, .poly-component__gallery-counter')
            if photos_elem:
                num_fotos = parse_int(photos_elem.get_text(strip=True))

            # data-id canónico del <li>
            data_id = None
            try:
                data_id = listing.get('data-id') or listing.get('data-item-id')
            except Exception:
                pass

            # ID de la propiedad - preferir data-id, fallback a URL
            property_id = "N/A"
            if data_id and data_id.upper().startswith('MLC'):
                property_id = data_id.upper().replace('MLC', 'MLC-').replace('--', '-')
            elif url != "N/A" and 'MLC-' in url:
                match = re.search(r'MLC-?(\d+)', url)
                if match:
                    property_id = f"MLC-{match.group(1)}"

            if titulo == "N/A" and precio == "N/A":
                return None

            return {
                'id': property_id,
                'titulo': titulo,
                'headline': headline,
                'precio': f"{moneda} {precio}" if moneda else precio,
                'precio_anterior': precio_anterior,
                'ubicacion': ubicacion,
                'atributos': ', '.join(atributos) if atributos else "N/A",
                'url': url,
                'operacion': self.operacion,
                # Inferir el tipo real desde el contenido; evita contaminar la categoría
                # con propiedades destacadas de otras categorías que Portal Inmobiliario
                # intercala en el listado.
                'tipo': self._infer_tipo(
                    headline if headline != "N/A" else '',
                    titulo if titulo != "N/A" else '',
                    ', '.join(atributos) if atributos else ''
                ),
                'tags': tags,
                'thumbnail_url': thumbnail,
                'num_fotos': num_fotos,
            }

        except Exception as e:
            logger.debug(f"Error extrayendo datos: {e}")
            return None
    
    def has_next_page(self) -> bool:
        """Verifica si hay botón de siguiente página"""
        try:
            next_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                'a.andes-pagination__link[title*="Siguiente"], '
                'a.andes-pagination__button--next:not(.andes-pagination__link--disabled)'
            )
            return len(next_buttons) > 0
        except:
            return False
    
    def scrape_all_pages(self, max_pages: Optional[int] = None, scrape_details: bool = False, 
                         max_detail_properties: Optional[int] = None) -> List[Dict[str, any]]:
        """
        Scrapea todas las páginas
        
        Args:
            max_pages: Máximo de páginas a scrapear
            scrape_details: Si es True, scrapea también la página de detalle de cada propiedad
            max_detail_properties: Máximo de propiedades para las cuales scrapear detalle (para testing)
        """
        logger.info(f"Iniciando scraping: {self.operacion} / {self.tipo_propiedad}")
        if scrape_details:
            logger.info("Modo detalle activado: se scrapeará información adicional de cada propiedad")
        
        offset = 0
        page_count = 0
        
        try:
            while True:
                if max_pages and page_count >= max_pages:
                    logger.info(f"Alcanzado límite de {max_pages} páginas")
                    break
                
                url = self.build_url(offset)
                soup = self.fetch_page(url)
                
                if not soup:
                    logger.error("No se pudo obtener la página")
                    break
                
                properties = self.extract_properties(soup)
                
                if not properties:
                    logger.info("No se encontraron más propiedades")
                    break
                
                # Si scrape_details está activado, obtener detalle de cada propiedad
                if scrape_details:
                    detailed_properties = []
                    for i, prop in enumerate(properties):
                        if max_detail_properties and i >= max_detail_properties:
                            logger.info(f"Alcanzado límite de {max_detail_properties} propiedades con detalle")
                            break
                        
                        try:
                            property_id = prop.get('id', 'N/A')
                            property_url = prop.get('url', '')
                            
                            if property_url and property_id != 'N/A':
                                # Scrapear detalle
                                detail_data = self.scrape_property_detail(property_id, property_url)
                                
                                # Mergear datos básicos con datos de detalle
                                prop.update(detail_data)
                                
                                # Rate limiting
                                time.sleep(2)
                            
                            detailed_properties.append(prop)
                            
                        except Exception as e:
                            logger.error(f"Error obteniendo detalle para propiedad {i+1}: {e}")
                            detailed_properties.append(prop)  # Agregar datos básicos de todos modos
                            continue
                    
                    validated_props = self._validate_and_add_properties(detailed_properties)
                    logger.info(f"Validadas {len(validated_props)}/{len(detailed_properties)} propiedades con detalle")
                else:
                    validated_props = self._validate_and_add_properties(properties)
                    logger.info(f"Validadas {len(validated_props)}/{len(properties)} propiedades")
                
                page_count += 1
                
                logger.info(f"Página {page_count}: {len(properties)} propiedades | Total válidas: {len(self.propiedades)}")
                
                if not self.has_next_page():
                    logger.info("No hay más páginas")
                    break
                
                offset += Config.ITEMS_PER_PAGE
                time.sleep(Config.DELAY_BETWEEN_REQUESTS)
            
            logger.info(f"Scraping completado: {len(self.propiedades)} propiedades válidas en {page_count} páginas")
            if self.validate:
                logger.info(f"Estadísticas de validación: {self.validation_stats['valid']} válidas, "
                          f"{self.validation_stats['invalid']} inválidas, "
                          f"{self.validation_stats['warnings']} con advertencias")
            
            # Persist to database if enabled
            if self.persist_to_db and self.propiedades:
                try:
                    from scraper_db_integration import persist_properties
                    logger.info("Persistiendo propiedades en PostgreSQL...")
                    db_stats = persist_properties(self.propiedades)
                    logger.info(f"Persistencia completada: {db_stats}")
                except ImportError:
                    logger.error("No se pudo importar scraper_db_integration. Asegúrate de que las dependencias estén instaladas.")
                except Exception as e:
                    logger.error(f"Error persistiendo a base de datos: {e}")
            
        finally:
            self.close()
        
        return self.propiedades
    
    def _scroll_to_bottom(self, steps: int = 6, pause: float = 0.6) -> None:
        """Scroll incremental para disparar lazy-load de galería, mapa y specs."""
        try:
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            for i in range(steps):
                self.driver.execute_script(
                    f"window.scrollTo(0, document.body.scrollHeight * {(i + 1) / steps});"
                )
                time.sleep(pause)
            # Final full scroll
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(pause)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.2)
        except Exception as e:
            logger.debug(f"scroll_to_bottom error: {e}")

    def _extract_json_state(self) -> Optional[dict]:
        """
        Intenta leer el estado preinicializado que MercadoLibre inyecta en el
        HTML renderizado (window.__PRELOADED_STATE__ / __INITIAL_STATE__).

        Devuelve el dict o None si no está disponible.
        """
        scripts = [
            "return window.__PRELOADED_STATE__ || null;",
            "return window.__INITIAL_STATE__ || null;",
            "return window.__NEXT_DATA__ && window.__NEXT_DATA__.props || null;",
        ]
        for js in scripts:
            try:
                result = self.driver.execute_script(js)
                if result:
                    return result
            except Exception:
                continue
        return None

    def scrape_property_detail(self, property_id: str, property_url: str) -> Dict[str, any]:
        """
        Scrapea la PDP de una propiedad capturando el máximo de campos:
        precio, superficies, dormitorios, baños, orientación, vista, piso,
        gastos comunes, amenities, servicios, publicador, imágenes, coordenadas,
        tags, breadcrumbs, fecha publicación/actualización, estado, visitas, etc.
        """
        import re
        from datetime import datetime, timedelta

        detail_data: Dict[str, any] = {
            'descripcion': None,
            'descripcion_html': None,
            'caracteristicas': {},          # typed fields mapped to Property columns
            'features_raw': [],             # all specs as list[{key, value}]
            'amenities': [],
            'servicios': [],
            'publicador': {},
            'imagenes': [],                 # list[{url, alt, orden}]
            'coordenadas': {},
            'fecha_publicacion': None,
            'fecha_actualizacion': None,
            'visitas': None,
            'estado_publicacion': None,
            'breadcrumbs': [],
            'raw_state': None,
        }

        try:
            logger.info(f"Scrapeando detalle de {property_id}...")
            self.driver.get(property_url)

            try:
                self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR,
                        'div.ui-pdp-container__content, div.ui-pdp-header, h1.ui-pdp-title'))
                )
            except Exception:
                logger.warning(f"Timeout esperando PDP {property_id}")

            # Trigger lazy-load (images, map, specs)
            self._scroll_to_bottom()

            # Estado JSON embebido (fuente rica)
            try:
                state = self._extract_json_state()
                if state:
                    detail_data['raw_state'] = state
                    self._merge_state_into_detail(state, detail_data)
                    logger.debug(f"raw_state capturado para {property_id}")
            except Exception as e:
                logger.debug(f"Error extrayendo raw_state: {e}")

            soup = BeautifulSoup(self.driver.page_source, 'lxml')

            # --- Descripción ---
            if not detail_data.get('descripcion'):
                desc_elem = soup.select_one(
                    'p.ui-pdp-description__content, div.ui-pdp-description__content, '
                    'div.ui-pdp-description, p[data-testid="description"]'
                )
                if desc_elem:
                    detail_data['descripcion'] = desc_elem.get_text('\n', strip=True)
                    detail_data['descripcion_html'] = str(desc_elem)

            # --- Specs exhaustivas (tabla + lista + highlighted) ---
            raw_features, caracteristicas = self._extract_all_specs(soup)
            detail_data['features_raw'].extend(raw_features)
            detail_data['caracteristicas'].update(caracteristicas)

            # --- Amenities / servicios ---
            amenities, servicios = self._extract_amenities_services(soup, raw_features)
            # dedup preserving insertion order
            detail_data['amenities'] = list(dict.fromkeys(detail_data['amenities'] + amenities))
            detail_data['servicios'] = list({s['nombre']: s for s in (detail_data['servicios'] + servicios)}.values())

            # --- Publicador ampliado ---
            publicador = self._extract_publisher(soup)
            # do not override JSON-state fields that are truthy
            for k, v in publicador.items():
                if v and not detail_data['publicador'].get(k):
                    detail_data['publicador'][k] = v

            # --- Imágenes (sin límite, alta resolución) ---
            if not detail_data['imagenes']:
                detail_data['imagenes'] = self._extract_images(soup)

            # --- Coordenadas (fallback si no vino en state) ---
            if not detail_data['coordenadas']:
                detail_data['coordenadas'] = self._extract_coordinates(soup)

            # --- Breadcrumbs ---
            if not detail_data['breadcrumbs']:
                detail_data['breadcrumbs'] = [
                    a.get_text(strip=True)
                    for a in soup.select('nav.andes-breadcrumb a, .ui-pdp-breadcrumb a')
                    if a.get_text(strip=True)
                ]

            # --- Fecha publicación / visitas / estado ---
            for elem in soup.select('div.ui-pdp-header__bottom-line span, .ui-pdp-subtitle, '
                                    '.ui-pdp-header__info, [data-testid="publication-date"]'):
                txt = elem.get_text(' ', strip=True).lower()
                if not txt:
                    continue
                # Fecha publicación
                if detail_data['fecha_publicacion'] is None and ('publicado' in txt or 'hace' in txt):
                    detail_data['fecha_publicacion'] = self._parse_relative_date(txt)
                # Visitas
                if detail_data['visitas'] is None and 'visita' in txt:
                    n = parse_int(txt)
                    if n:
                        detail_data['visitas'] = n
                # Estado
                if detail_data['estado_publicacion'] is None:
                    for st in ('activa', 'pausada', 'finalizada', 'vendido', 'arrendado'):
                        if st in txt:
                            detail_data['estado_publicacion'] = st
                            break

            logger.info(
                f"Detalle OK {property_id}: "
                f"{len(detail_data['features_raw'])} specs, "
                f"{len(detail_data['amenities'])} amenities, "
                f"{len(detail_data['imagenes'])} imgs"
            )

        except Exception as e:
            logger.error(f"Error scrapeando detalle de {property_id}: {e}")

        return detail_data

    # ------------------------------------------------------------------ #
    # Helpers para detalle                                                #
    # ------------------------------------------------------------------ #

    def _extract_all_specs(self, soup: BeautifulSoup):
        """
        Recorre TODOS los bloques de specs del PDP (tabla, listas, highlighted)
        y devuelve (raw_features, caracteristicas_tipadas).

        `raw_features` es lista de dicts {key, value} con todas las specs tal cual.
        `caracteristicas_tipadas` es dict campo_Property -> valor_parseado.
        """
        raw_features = []
        caracteristicas: Dict[str, any] = {}
        seen_keys = set()

        # 1. Tablas de specs
        row_selectors = [
            'div.ui-vpp-striped-specs__table tr',
            'div.ui-vpp-highlighted-specs__striped-specs tr',
            'div.ui-pdp-specs__table table tr',
            'table.andes-table tbody tr',
            '.andes-table__body .andes-table__row',
        ]
        for sel in row_selectors:
            for row in soup.select(sel):
                key_elem = row.select_one('th, .andes-table__header, .ui-pdp-specs__table__column-title')
                val_elem = row.select_one('td, .andes-table__column, .ui-pdp-specs__table__column-value')
                if not key_elem or not val_elem:
                    continue
                key = key_elem.get_text(strip=True)
                value = val_elem.get_text(' ', strip=True)
                if not key or not value:
                    continue
                nk = normalize_key(key)
                if nk in seen_keys:
                    continue
                seen_keys.add(nk)
                raw_features.append({'key': key, 'value': value})
                mapped = map_feature(key, value)
                if mapped:
                    caracteristicas[mapped[0]] = mapped[1]

        # 2. Listas (key-value)
        for dl in soup.select('div.ui-pdp-specs__list dl, .ui-vpp-highlighted-specs__key-value'):
            key_elem = dl.select_one('dt, .ui-vpp-highlighted-specs__key-value__labels, .andes-list__item-primary')
            val_elem = dl.select_one('dd, .ui-vpp-highlighted-specs__key-value__value, .andes-list__item-secondary')
            if not key_elem or not val_elem:
                continue
            key = key_elem.get_text(strip=True)
            value = val_elem.get_text(' ', strip=True)
            if not key or not value:
                continue
            nk = normalize_key(key)
            if nk in seen_keys:
                continue
            seen_keys.add(nk)
            raw_features.append({'key': key, 'value': value})
            mapped = map_feature(key, value)
            if mapped:
                caracteristicas[mapped[0]] = mapped[1]

        # 3. Highlighted specs (iconos con m², dormitorios...)
        for item in soup.select(
            'ul.ui-pdp-highlighted-specs__features-list li, '
            'div.ui-vpp-highlighted-specs__attribute-columns div, '
            'div.ui-pdp-highlighted-specs__main-feature'
        ):
            txt = item.get_text(' ', strip=True)
            if not txt:
                continue
            # Heurística: "3 dormitorios", "80 m² útiles"
            m = re.match(r'^\s*(\d+[\.,]?\d*)\s+(.+)$', txt)
            if not m:
                continue
            value, key = m.group(1), m.group(2)
            nk = normalize_key(key)
            if nk in seen_keys:
                continue
            seen_keys.add(nk)
            raw_features.append({'key': key, 'value': value})
            mapped = map_feature(key, value)
            if mapped:
                caracteristicas[mapped[0]] = mapped[1]

        return raw_features, caracteristicas

    def _extract_amenities_services(self, soup: BeautifulSoup, raw_features):
        """Detecta amenities del edificio y servicios a partir de specs e iconos."""
        amenities = []
        servicios = []

        # Lista explícita de amenities/servicios en la PDP
        for li in soup.select(
            'ul.ui-pdp-specs__list li, '
            'ul.ui-vpp-amenities__list li, '
            'section[data-testid="amenities"] li'
        ):
            name = li.get_text(' ', strip=True)
            if not name:
                continue
            nk = normalize_key(name)
            if nk in SERVICE_KEYWORDS or any(w in nk for w in SERVICE_KEYWORDS):
                servicios.append({'nombre': name, 'incluido': True})
            else:
                amenities.append(name)

        # También escanear specs con values "Sí/Si" que suelen ser amenities booleanos
        for feat in raw_features:
            nk = normalize_key(feat['key'])
            val_norm = normalize_key(str(feat['value']))
            if val_norm in {'si', 'yes', 'true', 'incluido'}:
                if any(w in nk for w in SERVICE_KEYWORDS):
                    servicios.append({'nombre': feat['key'], 'incluido': True})
                elif any(w in nk for w in AMENITY_KEYWORDS):
                    amenities.append(feat['key'])

        return amenities, servicios

    def _extract_publisher(self, soup: BeautifulSoup) -> dict:
        publicador = {}

        name_elem = soup.select_one(
            'div.ui-pdp-seller__header__title, .ui-seller-data__name, '
            'h2.ui-seller-info__header__title, [data-testid="seller-name"]'
        )
        if name_elem:
            publicador['nombre'] = name_elem.get_text(strip=True)

        logo_elem = soup.select_one('img.ui-pdp-seller__header__logo, img.ui-seller-data__logo')
        if logo_elem:
            publicador['logo_url'] = logo_elem.get('src') or logo_elem.get('data-src')

        perfil_elem = soup.select_one(
            'a.ui-pdp-seller__link-trigger, a.ui-seller-info__link, '
            'a[data-testid="seller-link"]'
        )
        if perfil_elem and perfil_elem.get('href'):
            publicador['perfil_url'] = perfil_elem['href']

        rep_elem = soup.select_one('.ui-seller-info__status-info__title, .ui-pdp-seller__status__title')
        if rep_elem:
            publicador['reputacion'] = rep_elem.get_text(strip=True)

        # Tipo
        type_elem = soup.select_one(
            'div.ui-pdp-seller__header__label, .ui-seller-data__label, '
            '[data-testid="seller-type"]'
        )
        tipo_text = type_elem.get_text(strip=True).lower() if type_elem else ''
        if not tipo_text and publicador.get('nombre'):
            tipo_text = publicador['nombre'].lower()
        if any(x in tipo_text for x in ['constructora', 'inmobiliaria', 'propiedades',
                                        'bienes raices', 'bienes raíces', 'corredor',
                                        'agente']):
            if 'constructora' in tipo_text:
                publicador['tipo'] = 'constructora'
            else:
                publicador['tipo'] = 'inmobiliaria'
        elif publicador.get('nombre'):
            publicador['tipo'] = 'particular'

        # Teléfono (si aparece visible)
        tel_elem = soup.select_one('a[href^="tel:"]')
        if tel_elem:
            publicador['telefono'] = tel_elem.get('href', '').replace('tel:', '').strip()

        return publicador

    def _extract_images(self, soup: BeautifulSoup) -> list:
        """Extrae todas las imágenes de la galería con orden y alt."""
        imagenes = []
        seen = set()
        selectors = [
            'figure.ui-pdp-gallery__figure img',
            'div.ui-pdp-gallery__column img',
            'div.ui-pdp-gallery img',
            'img[data-testid="gallery-image"]',
        ]
        for selector in selectors:
            elems = soup.select(selector)
            if not elems:
                continue
            for idx, img in enumerate(elems):
                src = (img.get('data-zoom')
                       or img.get('data-full-src')
                       or img.get('data-src')
                       or img.get('src'))
                if not src or src in seen:
                    continue
                # Forzar alta resolución
                src_hd = src.replace('/D_NQ_NP_', '/D_NQ_NP_2X_')
                seen.add(src)
                imagenes.append({
                    'url': src_hd,
                    'alt': img.get('alt'),
                    'orden': idx,
                    'resolucion': '2X' if 'D_NQ_NP_2X_' in src_hd else None,
                })
            if imagenes:
                break
        return imagenes

    def _extract_coordinates(self, soup: BeautifulSoup) -> dict:
        import re
        coords: Dict[str, float] = {}

        for script in soup.find_all('script'):
            text = script.string or ''
            if not text or ('latitude' not in text and 'lat' not in text):
                continue
            lat_m = re.search(r'["\']lat(?:itude)?["\']\s*:\s*(-?\d+\.?\d*)', text)
            lng_m = re.search(r'["\']l(?:ng|ong(?:itude)?)["\']\s*:\s*(-?\d+\.?\d*)', text)
            if lat_m and lng_m:
                try:
                    coords['lat'] = float(lat_m.group(1))
                    coords['lng'] = float(lng_m.group(1))
                    break
                except ValueError:
                    pass

        if not coords:
            map_elem = soup.select_one('div.ui-pdp-map, [data-testid="map-container"]')
            if map_elem:
                raw = map_elem.get('data-coordinates') or map_elem.get('data-latlng') or ''
                nums = re.findall(r'-?\d+\.\d+', raw)
                if len(nums) >= 2:
                    coords['lat'] = float(nums[0])
                    coords['lng'] = float(nums[1])

        return coords

    def _parse_relative_date(self, text: str):
        import re
        from datetime import datetime, timedelta
        text = text.lower()
        # Días
        m = re.search(r'hace\s+(\d+)\s+d[ií]a', text)
        if m:
            return (datetime.now() - timedelta(days=int(m.group(1)))).strftime('%Y-%m-%d')
        m = re.search(r'hace\s+(\d+)\s+(?:mes|meses)', text)
        if m:
            return (datetime.now() - timedelta(days=int(m.group(1)) * 30)).strftime('%Y-%m-%d')
        m = re.search(r'hace\s+(\d+)\s+(?:hora|horas)', text)
        if m:
            return datetime.now().strftime('%Y-%m-%d')
        # "15 de marzo de 2024"
        meses = {'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
                 'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11,
                 'diciembre': 12}
        m = re.search(r'(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})', text)
        if m:
            mes = meses.get(m.group(2), 0)
            if mes:
                try:
                    return datetime(int(m.group(3)), mes, int(m.group(1))).strftime('%Y-%m-%d')
                except ValueError:
                    return None
        return None

    def _merge_state_into_detail(self, state: dict, detail_data: dict) -> None:
        """Fusiona campos útiles del `__PRELOADED_STATE__` en detail_data.

        MercadoLibre suele anidar los datos en `state['initialState']['components']`
        o `state['pageState']`. Buscamos algunas claves conocidas de forma
        defensiva para no depender de una estructura exacta.
        """
        def walk(obj):
            if isinstance(obj, dict):
                yield obj
                for v in obj.values():
                    yield from walk(v)
            elif isinstance(obj, list):
                for v in obj:
                    yield from walk(v)

        try:
            for node in walk(state):
                # Descripción (plain_text o content)
                if 'description' in node and isinstance(node['description'], dict):
                    txt = node['description'].get('plain_text') or node['description'].get('content')
                    if txt and not detail_data.get('descripcion'):
                        detail_data['descripcion'] = txt

                # Pictures
                if 'pictures' in node and isinstance(node['pictures'], list) and not detail_data['imagenes']:
                    imgs = []
                    for i, p in enumerate(node['pictures']):
                        if isinstance(p, dict):
                            url = p.get('url') or p.get('secure_url') or p.get('src')
                            if url:
                                imgs.append({
                                    'url': url.replace('/D_NQ_NP_', '/D_NQ_NP_2X_'),
                                    'alt': p.get('alt'),
                                    'orden': i,
                                    'resolucion': '2X',
                                })
                    if imgs:
                        detail_data['imagenes'] = imgs

                # Location
                if 'location' in node and isinstance(node['location'], dict):
                    loc = node['location']
                    lat = loc.get('latitude') or loc.get('lat')
                    lng = loc.get('longitude') or loc.get('lng')
                    if lat and lng and not detail_data['coordenadas']:
                        try:
                            detail_data['coordenadas'] = {'lat': float(lat), 'lng': float(lng)}
                        except (TypeError, ValueError):
                            pass
                    for key in ('neighborhood', 'barrio', 'city', 'state', 'address_line'):
                        val = loc.get(key)
                        if isinstance(val, dict):
                            val = val.get('name')
                        if val and key == 'neighborhood' and not detail_data['caracteristicas'].get('barrio'):
                            detail_data['caracteristicas']['barrio'] = val

                # Attributes (list of {id, name, value_name})
                if 'attributes' in node and isinstance(node['attributes'], list):
                    for attr in node['attributes']:
                        if not isinstance(attr, dict):
                            continue
                        name = attr.get('name') or attr.get('id')
                        value = attr.get('value_name') or attr.get('value') or attr.get('values')
                        if isinstance(value, list) and value:
                            value = ', '.join(
                                v.get('name') if isinstance(v, dict) else str(v)
                                for v in value if v
                            )
                        if not name or value in (None, ''):
                            continue
                        detail_data['features_raw'].append({'key': name, 'value': value})
                        mapped = map_feature(name, value)
                        if mapped:
                            detail_data['caracteristicas'][mapped[0]] = mapped[1]

                # Seller
                if 'seller' in node and isinstance(node['seller'], dict):
                    s = node['seller']
                    pub = detail_data['publicador']
                    pub.setdefault('nombre', s.get('nickname') or s.get('name'))
                    if s.get('permalink') and not pub.get('perfil_url'):
                        pub['perfil_url'] = s['permalink']
                    if s.get('logo') and not pub.get('logo_url'):
                        pub['logo_url'] = s['logo']
                    reputation = s.get('seller_reputation') or {}
                    if isinstance(reputation, dict):
                        level = reputation.get('level_id') or reputation.get('power_seller_status')
                        if level and not pub.get('reputacion'):
                            pub['reputacion'] = str(level)
        except Exception as e:
            logger.debug(f"merge_state error: {e}")
    
    def close(self):
        """Cierra el navegador"""
        if self.driver:
            logger.info("Cerrando navegador...")
            self.driver.quit()
    
    def _validate_and_add_properties(self, properties: List[Dict]) -> List[Dict]:
        """
        Valida y agrega propiedades a la lista interna.
        
        Si validate=True, usa DataValidator para validar cada propiedad.
        Solo las propiedades válidas se agregan a self.propiedades.
        
        Args:
            properties: Lista de propiedades a validar y agregar
            
        Returns:
            Lista de propiedades que fueron agregadas (válidas)
        """
        if not self.validate or not self.validator:
            # Sin validación, agregar todas
            self.propiedades.extend(properties)
            return properties
        
        valid_properties = []
        
        for prop in properties:
            try:
                result = self.validator.validate_property(prop)
                
                if result.is_valid:
                    self.propiedades.append(result.property_data)
                    valid_properties.append(result.property_data)
                    self.validation_stats['valid'] += 1
                    
                    if result.warnings:
                        self.validation_stats['warnings'] += len(result.warnings)
                        logger.debug(f"Propiedad {prop.get('id', 'N/A')} válida con {len(result.warnings)} advertencias")
                else:
                    self.validation_stats['invalid'] += 1
                    logger.warning(f"Propiedad inválida descartada: {result.errors}")
                    
            except Exception as e:
                logger.error(f"Error validando propiedad {prop.get('id', 'N/A')}: {e}")
                # En caso de error en validación, agregar de todos modos (no bloquear)
                self.propiedades.append(prop)
                valid_properties.append(prop)
        
        return valid_properties
    
    def get_properties(self) -> List[Dict[str, str]]:
        """Retorna las propiedades scrapeadas"""
        return self.propiedades
