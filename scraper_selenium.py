import time
import logging
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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PortalInmobiliarioSeleniumScraper:
    """Scraper usando Selenium para manejar JavaScript"""
    
    def __init__(self, operacion: str, tipo_propiedad: str, headless: bool = True):
        """
        Inicializa el scraper con Selenium
        
        Args:
            operacion: Tipo de operación
            tipo_propiedad: Tipo de propiedad
            headless: Ejecutar sin interfaz gráfica
        """
        if operacion not in Config.OPERACIONES:
            raise ValueError(f"Operación '{operacion}' no válida")
        
        if tipo_propiedad not in Config.TIPOS_PROPIEDAD:
            raise ValueError(f"Tipo de propiedad '{tipo_propiedad}' no válido")
        
        self.operacion = operacion
        self.tipo_propiedad = tipo_propiedad
        self.propiedades = []
        
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument(f'user-agent={Config.USER_AGENT}')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        logger.info("Inicializando navegador Chrome...")
        driver_path = ChromeDriverManager().install()
        
        # Corregir path si apunta al archivo incorrecto
        if 'THIRD_PARTY_NOTICES' in driver_path or not driver_path.endswith('chromedriver'):
            import os
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
    
    def scrape_all_pages(self, max_pages: Optional[int] = None) -> List[Dict[str, str]]:
        """Scrapea todas las páginas"""
        logger.info(f"Iniciando scraping: {self.operacion} / {self.tipo_propiedad}")
        
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
                
                self.propiedades.extend(properties)
                page_count += 1
                
                logger.info(f"Página {page_count}: {len(properties)} propiedades | Total: {len(self.propiedades)}")
                
                if not self.has_next_page():
                    logger.info("No hay más páginas")
                    break
                
                offset += Config.ITEMS_PER_PAGE
                time.sleep(Config.DELAY_BETWEEN_REQUESTS)
            
            logger.info(f"Scraping completado: {len(self.propiedades)} propiedades en {page_count} páginas")
            
        finally:
            self.close()
        
        return self.propiedades
    
    def close(self):
        """Cierra el navegador"""
        if self.driver:
            logger.info("Cerrando navegador...")
            self.driver.quit()
    
    def get_properties(self) -> List[Dict[str, str]]:
        """Retorna las propiedades scrapeadas"""
        return self.propiedades
