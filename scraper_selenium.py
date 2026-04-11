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

logger = get_logger(__name__)


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
    
    def _extract_property_data(self, listing) -> Optional[Dict[str, str]]:
        """Extrae datos de una propiedad"""
        try:
            # Título - estructura: h3.poly-component__title-wrapper > a.poly-component__title
            titulo = "N/A"
            titulo_elem = listing.select_one('a.poly-component__title')
            if titulo_elem:
                titulo = titulo_elem.get_text(strip=True)
            
            # Headline (tipo de propiedad) - span.poly-component__headline
            headline = "N/A"
            headline_elem = listing.select_one('span.poly-component__headline')
            if headline_elem:
                headline = headline_elem.get_text(strip=True)
            
            # Precio - span.andes-money-amount__fraction dentro de .poly-price__current
            precio = "N/A"
            precio_elem = listing.select_one('.poly-price__current span.andes-money-amount__fraction')
            if precio_elem:
                precio = precio_elem.get_text(strip=True)
            
            # Moneda - span.andes-money-amount__currency-symbol
            moneda = ""
            moneda_elem = listing.select_one('.poly-price__current span.andes-money-amount__currency-symbol')
            if moneda_elem:
                moneda = moneda_elem.get_text(strip=True)
            
            # Ubicación - span.poly-component__location
            ubicacion = "N/A"
            ubicacion_elem = listing.select_one('span.poly-component__location')
            if ubicacion_elem:
                ubicacion = ubicacion_elem.get_text(strip=True)
            
            # Atributos (m², dormitorios, etc.) - ul.poly-attributes_list > li
            atributos = []
            atributos_elems = listing.select('ul.poly-attributes_list li.poly-attributes_list__item')
            for attr in atributos_elems:
                atributos.append(attr.get_text(strip=True))
            
            # URL - a.poly-component__title
            url = "N/A"
            link_elem = listing.select_one('a.poly-component__title')
            if link_elem:
                url = link_elem.get('href', 'N/A')
            
            # ID de la propiedad - extraer del URL (formato: MLC-XXXXXXX)
            property_id = "N/A"
            if url != "N/A" and 'MLC-' in url:
                import re
                match = re.search(r'MLC-(\d+)', url)
                if match:
                    property_id = f"MLC-{match.group(1)}"
            
            # Validar que al menos tengamos precio o título
            if titulo == "N/A" and precio == "N/A":
                return None
            
            return {
                'id': property_id,
                'titulo': titulo,
                'headline': headline,
                'precio': f"{moneda} {precio}" if moneda else precio,
                'ubicacion': ubicacion,
                'atributos': ', '.join(atributos) if atributos else "N/A",
                'url': url,
                'operacion': self.operacion,
                'tipo': self.tipo_propiedad
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
    
    def scrape_property_detail(self, property_id: str, property_url: str) -> Dict[str, any]:
        """
        Scrapea la página de detalle de una propiedad.
        
        Args:
            property_id: ID de la propiedad (ej: "MLC-3705621748")
            property_url: URL completa de la propiedad
            
        Returns:
            dict con datos detallados o dict vacío si falla
        """
        detail_data = {
            'descripcion': None,
            'caracteristicas': {},
            'publicador': {},
            'imagenes': [],
            'coordenadas': {},
            'fecha_publicacion': None
        }
        
        try:
            logger.info(f"Scrapeando detalle de propiedad {property_id}...")
            
            # Navegar a URL de detalle
            self.driver.get(property_url)
            time.sleep(3)  # Esperar carga inicial
            
            # Esperar a que cargue el contenido principal
            try:
                self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 
                        'div.ui-pdp-container__content, div.ui-pdp-header, h1.ui-pdp-title'))
                )
                logger.info(f"Página de detalle cargada para {property_id}")
            except Exception as e:
                logger.warning(f"Timeout esperando contenido de detalle para {property_id}: {e}")
            
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'lxml')
            
            # Extraer descripción completa
            try:
                desc_elem = soup.select_one('div.ui-pdp-description__content, div.ui-pdp-description, p[data-testid="description"]')
                if desc_elem:
                    detail_data['descripcion'] = desc_elem.get_text(strip=True)
                    logger.debug(f"Descripción extraída: {len(detail_data['descripcion'])} chars")
            except Exception as e:
                logger.debug(f"Error extrayendo descripción: {e}")
            
            # Extraer características detalladas
            try:
                # Buscar tabla de características o lista de atributos
                caracteristicas = {}
                
                # Selectores comunes para características
                attr_selectors = [
                    'div.ui-vip-specs__table table tr',
                    'div.ui-pdp-specs__table table tr',
                    'div.ui-pdp-specs__list dl',
                    '.andes-table__body .andes-table__row',
                    'div[data-testid="specs-list"] .andes-list__item'
                ]
                
                for selector in attr_selectors:
                    rows = soup.select(selector)
                    if rows:
                        for row in rows:
                            try:
                                # Intentar diferentes estructuras
                                key_elem = row.select_one('th, dt, .andes-table__header, .andes-list__item-primary')
                                value_elem = row.select_one('td, dd, .andes-table__column, .andes-list__item-secondary')
                                
                                if key_elem and value_elem:
                                    key = key_elem.get_text(strip=True).lower()
                                    value = value_elem.get_text(strip=True)
                                    
                                    # Mapear campos conocidos
                                    if any(x in key for x in ['orientación', 'orientacion']):
                                        caracteristicas['orientacion'] = value
                                    elif any(x in key for x in ['año', 'construcción', 'construccion']):
                                        # Extraer número del año
                                        import re
                                        year_match = re.search(r'\d{4}', value)
                                        if year_match:
                                            caracteristicas['año_construccion'] = int(year_match.group())
                                    elif any(x in key for x in ['gastos comunes', 'gasto común']):
                                        # Extraer número de gastos
                                        import re
                                        gasto_match = re.search(r'[\d.,]+', value.replace('.', '').replace(',', ''))
                                        if gasto_match:
                                            try:
                                                caracteristicas['gastos_comunes'] = int(gasto_match.group().replace('.', ''))
                                            except:
                                                pass
                                    elif any(x in key for x in ['estacionamiento', 'estacionamientos']):
                                        import re
                                        est_match = re.search(r'\d+', value)
                                        if est_match:
                                            caracteristicas['estacionamientos'] = int(est_match.group())
                                    elif any(x in key for x in ['bodega', 'bodegas']):
                                        import re
                                        bod_match = re.search(r'\d+', value)
                                        if bod_match:
                                            caracteristicas['bodegas'] = int(bod_match.group())
                            except:
                                continue
                        break  # Si encontramos datos, salir del loop de selectores
                
                detail_data['caracteristicas'] = caracteristicas
                logger.debug(f"Características extraídas: {len(caracteristicas)} items")
            except Exception as e:
                logger.debug(f"Error extrayendo características: {e}")
            
            # Extraer información del publicador
            try:
                publicador = {}
                
                # Buscar nombre del publicador
                pub_name_elem = soup.select_one('div.ui-pdp-seller__header__title, .ui-seller-data__name, [data-testid="seller-name"]')
                if pub_name_elem:
                    publicador['nombre'] = pub_name_elem.get_text(strip=True)
                
                # Determinar tipo (inmobiliaria vs particular)
                pub_type_elem = soup.select_one('div.ui-pdp-seller__header__label, .ui-seller-data__label, [data-testid="seller-type"]')
                if pub_type_elem:
                    tipo_text = pub_type_elem.get_text(strip=True).lower()
                    if any(x in tipo_text for x in ['inmobiliaria', 'agente', 'corredor']):
                        publicador['tipo'] = 'inmobiliaria'
                    else:
                        publicador['tipo'] = 'particular'
                else:
                    # Fallback: si no hay label específico, inferir por nombre
                    if publicador.get('nombre'):
                        nombre_lower = publicador['nombre'].lower()
                        if any(x in nombre_lower for x in ['inmobiliaria', 'propiedades', 'bienes raíces', 'asesor']):
                            publicador['tipo'] = 'inmobiliaria'
                        else:
                            publicador['tipo'] = 'particular'
                
                detail_data['publicador'] = publicador
                logger.debug(f"Publicador extraído: {publicador.get('nombre', 'N/A')}")
            except Exception as e:
                logger.debug(f"Error extrayendo publicador: {e}")
            
            # Extraer URLs de imágenes
            try:
                imagenes = []
                
                # Buscar galería de imágenes
                img_selectors = [
                    'div.ui-pdp-gallery__column img',
                    'div.ui-pdp-gallery img',
                    'figure.ui-pdp-gallery__figure img',
                    'img[data-testid="gallery-image"]'
                ]
                
                for selector in img_selectors:
                    img_elements = soup.select(selector)
                    if img_elements:
                        for img in img_elements:
                            # Intentar obtener URL de alta resolución
                            src = img.get('data-src') or img.get('data-full-src') or img.get('src')
                            if src and src not in imagenes:
                                # Limpiar URL para obtener versión grande
                                src = src.replace('/D_NQ_NP_', '/D_NQ_NP_2X_')
                                imagenes.append(src)
                        
                        if imagenes:
                            break
                
                detail_data['imagenes'] = imagenes[:10]  # Limitar a 10 imágenes
                logger.debug(f"Imágenes extraídas: {len(imagenes)}")
            except Exception as e:
                logger.debug(f"Error extrayendo imágenes: {e}")
            
            # Extraer coordenadas GPS
            try:
                coordenadas = {}
                
                # Buscar en scripts (datos de mapa)
                scripts = soup.find_all('script')
                for script in scripts:
                    script_text = script.string if script else ''
                    if script_text and ('latitude' in script_text or 'longitude' in script_text):
                        import re
                        # Buscar coordenadas en formato JSON o variables
                        lat_match = re.search(r'["\']latitude["\']\s*:\s*(-?\d+\.?\d*)', script_text)
                        lng_match = re.search(r'["\']longitude["\']\s*:\s*(-?\d+\.?\d*)', script_text)
                        
                        if lat_match and lng_match:
                            coordenadas['lat'] = float(lat_match.group(1))
                            coordenadas['lng'] = float(lng_match.group(1))
                            break
                
                # Alternativa: buscar en meta tags o elementos de mapa
                if not coordenadas:
                    map_elem = soup.select_one('div.ui-pdp-map, [data-testid="map-container"]')
                    if map_elem:
                        data_coords = map_elem.get('data-coordinates') or map_elem.get('data-latlng')
                        if data_coords:
                            import re
                            coords = re.findall(r'-?\d+\.?\d*', data_coords)
                            if len(coords) >= 2:
                                coordenadas['lat'] = float(coords[0])
                                coordenadas['lng'] = float(coords[1])
                
                if coordenadas:
                    detail_data['coordenadas'] = coordenadas
                    logger.debug(f"Coordenadas extraídas: {coordenadas}")
            except Exception as e:
                logger.debug(f"Error extrayendo coordenadas: {e}")
            
            # Extraer fecha de publicación
            try:
                fecha_elem = soup.select_one('div.ui-pdp-header__bottom-line span, .ui-pdp-date, [data-testid="publication-date"]')
                if fecha_elem:
                    fecha_text = fecha_elem.get_text(strip=True).lower()
                    # Parsear formatos comunes: "Publicado hace X días", "15 de marzo de 2024"
                    import re
                    from datetime import datetime, timedelta
                    
                    if 'hace' in fecha_text:
                        # "Publicado hace 5 días"
                        num_match = re.search(r'(\d+)', fecha_text)
                        if num_match:
                            dias = int(num_match.group(1))
                            fecha = datetime.now() - timedelta(days=dias)
                            detail_data['fecha_publicacion'] = fecha.strftime('%Y-%m-%d')
                    else:
                        # Intentar parsear fecha directa
                        meses_es = {
                            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
                            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
                            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
                        }
                        
                        # Buscar patrón: "15 de marzo de 2024"
                        fecha_match = re.search(r'(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})', fecha_text)
                        if fecha_match:
                            dia = int(fecha_match.group(1))
                            mes = meses_es.get(fecha_match.group(2).lower(), 0)
                            anio = int(fecha_match.group(3))
                            if mes > 0:
                                fecha = datetime(anio, mes, dia)
                                detail_data['fecha_publicacion'] = fecha.strftime('%Y-%m-%d')
            except Exception as e:
                logger.debug(f"Error extrayendo fecha: {e}")
            
            logger.info(f"Detalle scrapeado exitosamente para {property_id}")
            
        except Exception as e:
            logger.error(f"Error scrapeando detalle de {property_id}: {e}")
            # Retornar datos parciales si los hay, o vacío
        
        return detail_data
    
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
