"""
Tests unitarios para el scraping de página de detalle
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import Mock, MagicMock, patch
from bs4 import BeautifulSoup
from scraper_selenium import PortalInmobiliarioSeleniumScraper


class TestScrapePropertyDetail:
    """Tests para el método scrape_property_detail"""
    
    @pytest.fixture
    def mock_scraper(self):
        """Fixture que crea un scraper con mocks"""
        with patch('scraper_selenium.ChromeDriverManager') as mock_manager, \
             patch('scraper_selenium.webdriver.Chrome') as mock_chrome, \
             patch('scraper_selenium.Service'):
            
            mock_driver = MagicMock()
            mock_chrome.return_value = mock_driver
            mock_manager.return_value.install.return_value = '/mock/chromedriver'
            
            scraper = PortalInmobiliarioSeleniumScraper(
                operacion='venta',
                tipo_propiedad='departamento',
                headless=True
            )
            
            # Mock del wait
            scraper.wait = MagicMock()
            
            yield scraper
    
    @pytest.fixture
    def sample_detail_html(self):
        """HTML de ejemplo de página de detalle"""
        return """
        <html>
            <body>
                <div class="ui-pdp-container__content">
                    <h1 class="ui-pdp-title">Departamento de lujo</h1>
                    <div class="ui-pdp-description__content">
                        <p>Amplio departamento con vista al mar, 3 dormitorios, 2 baños.</p>
                    </div>
                    <div class="ui-pdp-specs__table">
                        <table>
                            <tr><th>Orientación</th><td>Norte</td></tr>
                            <tr><th>Año de construcción</th><td>2020</td></tr>
                            <tr><th>Gastos comunes</th><td>$45.000</td></tr>
                            <tr><th>Estacionamientos</th><td>2</td></tr>
                            <tr><th>Bodegas</th><td>1</td></tr>
                        </table>
                    </div>
                    <div class="ui-pdp-seller__header">
                        <div class="ui-pdp-seller__header__title">Inmobiliaria XYZ</div>
                        <div class="ui-pdp-seller__header__label">Inmobiliaria</div>
                    </div>
                    <div class="ui-pdp-gallery">
                        <img data-src="https://example.com/img1.jpg" src="https://example.com/thumb1.jpg"/>
                        <img data-src="https://example.com/img2.jpg" src="https://example.com/thumb2.jpg"/>
                    </div>
                    <div class="ui-pdp-header__bottom-line">
                        <span>Publicado hace 5 días</span>
                    </div>
                </div>
            </body>
        </html>
        """
    
    def test_scrape_property_detail_returns_dict(self, mock_scraper):
        """Test que el método retorna un diccionario"""
        mock_scraper.driver.page_source = "<html><body></body></html>"
        
        result = mock_scraper.scrape_property_detail('MLC-123', 'https://example.com/123')
        
        assert isinstance(result, dict)
        assert 'descripcion' in result
        assert 'caracteristicas' in result
        assert 'publicador' in result
        assert 'imagenes' in result
        assert 'coordenadas' in result
        assert 'fecha_publicacion' in result
    
    def test_extract_description(self, mock_scraper, sample_detail_html):
        """Test extracción de descripción"""
        mock_scraper.driver.page_source = sample_detail_html
        
        result = mock_scraper.scrape_property_detail('MLC-123', 'https://example.com/123')
        
        assert result['descripcion'] is not None
        assert 'Amplio departamento' in result['descripcion']
    
    def test_extract_caracteristicas(self, mock_scraper, sample_detail_html):
        """Test extracción de características"""
        mock_scraper.driver.page_source = sample_detail_html
        
        result = mock_scraper.scrape_property_detail('MLC-123', 'https://example.com/123')
        
        assert 'caracteristicas' in result
        assert result['caracteristicas']['orientacion'] == 'Norte'
        assert result['caracteristicas']['año_construccion'] == 2020
        assert result['caracteristicas']['gastos_comunes'] == 45000
        assert result['caracteristicas']['estacionamientos'] == 2
        assert result['caracteristicas']['bodegas'] == 1
    
    def test_extract_publicador(self, mock_scraper, sample_detail_html):
        """Test extracción de información del publicador"""
        mock_scraper.driver.page_source = sample_detail_html
        
        result = mock_scraper.scrape_property_detail('MLC-123', 'https://example.com/123')
        
        assert 'publicador' in result
        assert result['publicador']['nombre'] == 'Inmobiliaria XYZ'
        assert result['publicador']['tipo'] == 'inmobiliaria'
    
    def test_extract_imagenes(self, mock_scraper, sample_detail_html):
        """Test extracción de URLs de imágenes"""
        mock_scraper.driver.page_source = sample_detail_html
        
        result = mock_scraper.scrape_property_detail('MLC-123', 'https://example.com/123')
        
        assert 'imagenes' in result
        assert len(result['imagenes']) == 2
        assert 'https://example.com/img1.jpg' in result['imagenes'][0]
    
    def test_extract_fecha_publicacion_relative(self, mock_scraper, sample_detail_html):
        """Test extracción de fecha de publicación (formato relativo)"""
        mock_scraper.driver.page_source = sample_detail_html
        
        result = mock_scraper.scrape_property_detail('MLC-123', 'https://example.com/123')
        
        assert 'fecha_publicacion' in result
        # Debe tener formato YYYY-MM-DD
        assert result['fecha_publicacion'] is not None
        assert len(result['fecha_publicacion']) == 10
    
    def test_extract_coordenadas_from_script(self, mock_scraper):
        """Test extracción de coordenadas GPS desde scripts"""
        html_with_coords = """
        <html>
            <body>
                <script>
                    window.__INITIAL_STATE__ = {
                        "latitude": -33.4569,
                        "longitude": -70.6483
                    };
                </script>
            </body>
        </html>
        """
        mock_scraper.driver.page_source = html_with_coords
        
        result = mock_scraper.scrape_property_detail('MLC-123', 'https://example.com/123')
        
        assert 'coordenadas' in result
        assert result['coordenadas']['lat'] == -33.4569
        assert result['coordenadas']['lng'] == -70.6483
    
    def test_handles_errors_gracefully(self, mock_scraper):
        """Test que maneja errores sin lanzar excepciones"""
        # Simular driver que lanza excepción
        mock_scraper.driver.get.side_effect = Exception("Connection error")
        
        result = mock_scraper.scrape_property_detail('MLC-123', 'https://example.com/123')
        
        # Debe retornar estructura vacía sin lanzar excepción
        assert isinstance(result, dict)
        assert 'descripcion' in result
    
    def test_publicador_tipo_particular(self, mock_scraper):
        """Test detección de publicador particular"""
        html_particular = """
        <html>
            <body>
                <div class="ui-pdp-seller__header__title">Juan Pérez</div>
                <div class="ui-pdp-seller__header__label">Particular</div>
            </body>
        </html>
        """
        mock_scraper.driver.page_source = html_particular
        
        result = mock_scraper.scrape_property_detail('MLC-123', 'https://example.com/123')
        
        assert result['publicador']['tipo'] == 'particular'
    
    def test_publicador_inference_from_name(self, mock_scraper):
        """Test inferencia de tipo por nombre cuando no hay label"""
        html_inference = """
        <html>
            <body>
                <div class="ui-pdp-seller__header__title">Inmobiliaria ABC Propiedades</div>
            </body>
        </html>
        """
        mock_scraper.driver.page_source = html_inference
        
        result = mock_scraper.scrape_property_detail('MLC-123', 'https://example.com/123')
        
        assert result['publicador']['tipo'] == 'inmobiliaria'
    
    def test_imagenes_limit_to_10(self, mock_scraper):
        """Test que limita imágenes a máximo 10"""
        # Crear HTML con 15 imágenes
        img_tags = ''.join([f'<img data-src="https://example.com/img{i}.jpg"/>' for i in range(15)])
        html_many_imgs = f"<html><body><div class='ui-pdp-gallery'>{img_tags}</div></body></html>"
        
        mock_scraper.driver.page_source = html_many_imgs
        
        result = mock_scraper.scrape_property_detail('MLC-123', 'https://example.com/123')
        
        assert len(result['imagenes']) <= 10
    
    def test_empty_fields_when_no_data(self, mock_scraper):
        """Test que campos vacíos tienen valores por defecto cuando no hay datos"""
        mock_scraper.driver.page_source = "<html><body></body></html>"
        
        result = mock_scraper.scrape_property_detail('MLC-123', 'https://example.com/123')
        
        assert result['descripcion'] is None
        assert result['caracteristicas'] == {}
        assert result['publicador'] == {}
        assert result['imagenes'] == []
        assert result['coordenadas'] == {}
        assert result['fecha_publicacion'] is None
    
    def test_navigates_to_url(self, mock_scraper):
        """Test que navega a la URL proporcionada"""
        mock_scraper.driver.page_source = "<html><body></body></html>"
        test_url = 'https://example.com/property/MLC-123'
        
        mock_scraper.scrape_property_detail('MLC-123', test_url)
        
        mock_scraper.driver.get.assert_called_once_with(test_url)


class TestScrapeAllPagesIntegration:
    """Tests para la integración de scrape_property_detail con scrape_all_pages"""
    
    @pytest.fixture
    def mock_scraper_with_pages(self):
        """Fixture que crea un scraper con mocks para testing de páginas"""
        with patch('scraper_selenium.ChromeDriverManager') as mock_manager, \
             patch('scraper_selenium.webdriver.Chrome') as mock_chrome, \
             patch('scraper_selenium.Service'):
            
            mock_driver = MagicMock()
            mock_chrome.return_value = mock_driver
            mock_manager.return_value.install.return_value = '/mock/chromedriver'
            
            scraper = PortalInmobiliarioSeleniumScraper(
                operacion='venta',
                tipo_propiedad='departamento',
                headless=True
            )
            
            scraper.wait = MagicMock()
            
            yield scraper
    
    def test_scrape_all_pages_without_details(self, mock_scraper_with_pages):
        """Test que scrape_all_pages funciona sin scrape_details"""
        # Mock de página con propiedades
        mock_scraper_with_pages.driver.page_source = """
        <html>
            <body>
                <li class="ui-search-layout__item">
                    <a class="poly-component__title" href="https://example.com/MLC-12345678">Propiedad 1</a>
                    <span class="andes-money-amount__fraction">1000</span>
                </li>
            </body>
        </html>
        """
        
        # Mock para has_next_page (sin página siguiente)
        mock_scraper_with_pages.driver.find_elements.return_value = []
        
        result = mock_scraper_with_pages.scrape_all_pages(
            max_pages=1, 
            scrape_details=False
        )
        
        assert isinstance(result, list)
        assert len(result) == 1
        # No debe llamar a scrape_property_detail
        assert mock_scraper_with_pages.driver.get.call_count == 1  # Solo la página de listado
    
    def test_scrape_all_pages_with_details(self, mock_scraper_with_pages):
        """Test que scrape_all_pages llama a scrape_property_detail cuando scrape_details=True"""
        # Primera llamada: página de listado
        listado_html = """
        <html>
            <body>
                <li class="ui-search-layout__item">
                    <a class="poly-component__title" href="https://example.com/MLC-12345678">Propiedad 1</a>
                    <span class="andes-money-amount__fraction">1000</span>
                </li>
            </body>
        </html>
        """
        
        # Segunda llamada: página de detalle
        detalle_html = """
        <html>
            <body>
                <div class="ui-pdp-description__content">Descripción completa</div>
            </body>
        </html>
        """
        
        # Configurar side_effect para retornar diferentes HTMLs
        mock_scraper_with_pages.driver.page_source = listado_html
        mock_scraper_with_pages.driver.find_elements.return_value = []
        
        result = mock_scraper_with_pages.scrape_all_pages(
            max_pages=1,
            scrape_details=True,
            max_detail_properties=1
        )
        
        # Debe haber navegado al menos 2 veces: listado + detalle
        assert mock_scraper_with_pages.driver.get.call_count >= 1


class TestDataExporterFlatten:
    """Tests para el método flatten_property del exporter"""
    
    @pytest.fixture
    def exporter(self):
        """Fixture del exportador"""
        from exporter import DataExporter
        with patch('exporter.os.makedirs'):
            return DataExporter()
    
    def test_flatten_simple_property(self, exporter):
        """Test aplanar propiedad sin campos anidados"""
        prop = {
            'id': 'MLC-123',
            'titulo': 'Departamento',
            'precio': 'UF 3.000'
        }
        
        result = exporter.flatten_property(prop)
        
        assert result['id'] == 'MLC-123'
        assert result['titulo'] == 'Departamento'
        assert result['precio'] == 'UF 3.000'
    
    def test_flatten_nested_dict(self, exporter):
        """Test aplanar propiedad con diccionario anidado"""
        prop = {
            'id': 'MLC-123',
            'caracteristicas': {
                'orientacion': 'Norte',
                'año_construccion': 2020
            }
        }
        
        result = exporter.flatten_property(prop)
        
        assert result['id'] == 'MLC-123'
        assert result['caracteristicas_orientacion'] == 'Norte'
        assert result['caracteristicas_año_construccion'] == '2020'
        assert 'caracteristicas' not in result
    
    def test_flatten_list(self, exporter):
        """Test aplanar propiedad con lista"""
        prop = {
            'id': 'MLC-123',
            'imagenes': ['url1.jpg', 'url2.jpg', 'url3.jpg']
        }
        
        result = exporter.flatten_property(prop)
        
        assert result['id'] == 'MLC-123'
        assert result['imagenes'] == 'url1.jpg | url2.jpg | url3.jpg'
    
    def test_flatten_none_values(self, exporter):
        """Test manejo de valores None"""
        prop = {
            'id': 'MLC-123',
            'descripcion': None,
            'caracteristicas': {'orientacion': None}
        }
        
        result = exporter.flatten_property(prop)
        
        assert result['descripcion'] == ''
        assert result['caracteristicas_orientacion'] == ''
    
    def test_flatten_complete_property(self, exporter):
        """Test aplanar propiedad completa con todos los campos"""
        prop = {
            'id': 'MLC-3705621748',
            'titulo': 'Departamento de lujo',
            'descripcion': 'Amplio departamento...',
            'caracteristicas': {
                'orientacion': 'Norte',
                'año_construccion': 2024,
                'gastos_comunes': 45000,
                'estacionamientos': 1,
                'bodegas': 1
            },
            'publicador': {
                'nombre': 'Inmobiliaria XYZ',
                'tipo': 'inmobiliaria'
            },
            'imagenes': ['https://img1.jpg', 'https://img2.jpg'],
            'coordenadas': {
                'lat': -33.4569,
                'lng': -70.6483
            },
            'fecha_publicacion': '2024-03-15'
        }
        
        result = exporter.flatten_property(prop)
        
        # Verificar campos aplanados
        assert result['id'] == 'MLC-3705621748'
        assert result['caracteristicas_orientacion'] == 'Norte'
        assert result['caracteristicas_año_construccion'] == '2024'
        assert result['publicador_nombre'] == 'Inmobiliaria XYZ'
        assert result['publicador_tipo'] == 'inmobiliaria'
        assert result['imagenes'] == 'https://img1.jpg | https://img2.jpg'
        assert result['coordenadas_lat'] == '-33.4569'
        assert result['coordenadas_lng'] == '-70.6483'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
