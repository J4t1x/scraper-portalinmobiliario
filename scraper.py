import requests
from bs4 import BeautifulSoup
import time
import logging
from typing import List, Dict, Optional
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PortalInmobiliarioScraper:
    """Scraper para portalinmobiliario.com"""
    
    def __init__(self, operacion: str, tipo_propiedad: str):
        """
        Inicializa el scraper
        
        Args:
            operacion: Tipo de operación (venta, arriendo, etc.)
            tipo_propiedad: Tipo de propiedad (departamento, casa, etc.)
        """
        if operacion not in Config.OPERACIONES:
            raise ValueError(f"Operación '{operacion}' no válida. Opciones: {Config.OPERACIONES}")
        
        if tipo_propiedad not in Config.TIPOS_PROPIEDAD:
            raise ValueError(f"Tipo de propiedad '{tipo_propiedad}' no válido. Opciones: {Config.TIPOS_PROPIEDAD}")
        
        self.operacion = operacion
        self.tipo_propiedad = tipo_propiedad
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': Config.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-CL,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        
        self.propiedades = []
        
    def build_url(self, offset: int = 0) -> str:
        """
        Construye la URL para scraping
        
        Args:
            offset: Offset para paginación
            
        Returns:
            URL completa
        """
        base = f"{Config.BASE_URL}/{self.operacion}/{self.tipo_propiedad}"
        
        if offset > 0:
            return f"{base}_Desde_{offset}"
        
        return base
    
    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Obtiene y parsea una página
        
        Args:
            url: URL a scrapear
            
        Returns:
            BeautifulSoup object o None si falla
        """
        for attempt in range(Config.MAX_RETRIES):
            try:
                logger.info(f"Fetching: {url} (intento {attempt + 1}/{Config.MAX_RETRIES})")
                
                response = self.session.get(url, timeout=Config.TIMEOUT)
                response.raise_for_status()
                
                return BeautifulSoup(response.content, 'lxml')
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Error en intento {attempt + 1}: {e}")
                
                if attempt < Config.MAX_RETRIES - 1:
                    time.sleep(Config.DELAY_BETWEEN_REQUESTS * 2)
                else:
                    logger.error(f"Falló después de {Config.MAX_RETRIES} intentos")
                    return None
    
    def extract_properties(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """
        Extrae datos de propiedades de la página
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Lista de diccionarios con datos de propiedades
        """
        properties = []
        
        try:
            listings = soup.find_all('div', {'data-id': True, 'data-posting-type': True})
            
            if not listings:
                logger.warning("No se encontraron listados en la página")
                return properties
            
            logger.info(f"Encontrados {len(listings)} listados")
            
            for listing in listings:
                try:
                    property_data = self._extract_property_data(listing)
                    if property_data:
                        properties.append(property_data)
                        
                except Exception as e:
                    logger.warning(f"Error extrayendo propiedad: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error en extract_properties: {e}")
        
        return properties
    
    def _extract_property_data(self, listing) -> Optional[Dict[str, str]]:
        """
        Extrae datos de una propiedad individual
        
        Args:
            listing: Elemento HTML del listado
            
        Returns:
            Diccionario con datos o None
        """
        try:
            titulo_elem = listing.find('h2', class_='ui-search-item__title')
            titulo = titulo_elem.get_text(strip=True) if titulo_elem else "N/A"
            
            precio_elem = listing.find('span', class_='andes-money-amount__fraction')
            precio = precio_elem.get_text(strip=True) if precio_elem else "N/A"
            
            ubicacion_elem = listing.find('span', class_='ui-search-item__location-label')
            ubicacion = ubicacion_elem.get_text(strip=True) if ubicacion_elem else "N/A"
            
            link_elem = listing.find('a', class_='ui-search-link')
            url = link_elem.get('href') if link_elem else "N/A"
            
            property_id = listing.get('data-id', 'N/A')
            
            return {
                'id': property_id,
                'titulo': titulo,
                'precio': precio,
                'ubicacion': ubicacion,
                'url': url,
                'operacion': self.operacion,
                'tipo': self.tipo_propiedad
            }
            
        except Exception as e:
            logger.warning(f"Error extrayendo datos individuales: {e}")
            return None
    
    def has_next_page(self, soup: BeautifulSoup) -> bool:
        """
        Verifica si hay más páginas disponibles
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            True si hay más páginas
        """
        try:
            pagination = soup.find('li', class_='andes-pagination__button--next')
            return pagination is not None and not pagination.find('a', class_='andes-pagination__link--disabled')
        except:
            return False
    
    def scrape_all_pages(self, max_pages: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Scrapea todas las páginas disponibles
        
        Args:
            max_pages: Número máximo de páginas a scrapear (None = todas)
            
        Returns:
            Lista de todas las propiedades encontradas
        """
        logger.info(f"Iniciando scraping: {self.operacion} / {self.tipo_propiedad}")
        
        offset = 0
        page_count = 0
        
        while True:
            if max_pages and page_count >= max_pages:
                logger.info(f"Alcanzado límite de {max_pages} páginas")
                break
            
            url = self.build_url(offset)
            soup = self.fetch_page(url)
            
            if not soup:
                logger.error("No se pudo obtener la página, deteniendo scraping")
                break
            
            properties = self.extract_properties(soup)
            
            if not properties:
                logger.info("No se encontraron más propiedades, finalizando")
                break
            
            self.propiedades.extend(properties)
            page_count += 1
            
            logger.info(f"Página {page_count}: {len(properties)} propiedades | Total acumulado: {len(self.propiedades)}")
            
            if not self.has_next_page(soup):
                logger.info("No hay más páginas disponibles")
                break
            
            offset += Config.ITEMS_PER_PAGE
            time.sleep(Config.DELAY_BETWEEN_REQUESTS)
        
        logger.info(f"Scraping completado: {len(self.propiedades)} propiedades en {page_count} páginas")
        
        return self.propiedades
    
    def get_properties(self) -> List[Dict[str, str]]:
        """Retorna las propiedades scrapeadas"""
        return self.propiedades
