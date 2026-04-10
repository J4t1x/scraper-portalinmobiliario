"""Tests para scraper.py (requests + BeautifulSoup)"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from bs4 import BeautifulSoup
from scraper import PortalInmobiliarioScraper


class TestPortalInmobiliarioScraperInit:
    """Tests para inicialización del scraper"""
    
    def test_init_valid_operacion_tipo(self):
        """Test inicialización con operación y tipo válidos"""
        scraper = PortalInmobiliarioScraper('venta', 'departamento')
        assert scraper.operacion == 'venta'
        assert scraper.tipo_propiedad == 'departamento'
        assert scraper.propiedades == []
        assert scraper.session is not None
    
    def test_init_invalid_operacion(self):
        """Test inicialización con operación inválida"""
        with pytest.raises(ValueError, match="Operación 'invalida' no válida"):
            PortalInmobiliarioScraper('invalida', 'departamento')
    
    def test_init_invalid_tipo(self):
        """Test inicialización con tipo inválido"""
        with pytest.raises(ValueError, match="Tipo de propiedad 'invalido' no válido"):
            PortalInmobiliarioScraper('venta', 'invalido')
    
    def test_session_headers(self):
        """Test que los headers del session están configurados"""
        scraper = PortalInmobiliarioScraper('venta', 'departamento')
        assert 'User-Agent' in scraper.session.headers
        assert 'Accept' in scraper.session.headers


class TestBuildUrl:
    """Tests para el método build_url"""
    
    def test_build_url_no_offset(self):
        """Test construcción de URL sin offset"""
        scraper = PortalInmobiliarioScraper('venta', 'departamento')
        url = scraper.build_url(0)
        assert 'venta' in url
        assert 'departamento' in url
        assert 'Desde' not in url
    
    def test_build_url_with_offset(self):
        """Test construcción de URL con offset"""
        scraper = PortalInmobiliarioScraper('venta', 'departamento')
        url = scraper.build_url(50)
        assert 'venta' in url
        assert 'departamento' in url
        assert 'Desde_50' in url


class TestFetchPage:
    """Tests para el método fetch_page"""
    
    @patch('scraper.requests.Session.get')
    def test_fetch_page_success(self, mock_get):
        """Test fetch_page exitoso"""
        mock_response = Mock()
        mock_response.content = b'<html><body>Test</body></html>'
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        scraper = PortalInmobiliarioScraper('venta', 'departamento')
        result = scraper.fetch_page('http://test.com')
        
        assert isinstance(result, BeautifulSoup)
        mock_get.assert_called_once()
    
    @patch('scraper.requests.Session.get')
    def test_fetch_page_failure(self, mock_get):
        """Test fetch_page con error de request"""
        mock_get.side_effect = requests.exceptions.RequestException("Error")
        
        scraper = PortalInmobiliarioScraper('venta', 'departamento')
        result = scraper.fetch_page('http://test.com')
        
        assert result is None
    
    @patch('scraper.requests.Session.get')
    @patch('scraper.time.sleep')
    def test_fetch_page_retry(self, mock_sleep, mock_get):
        """Test fetch_page con retry"""
        mock_get.side_effect = [
            requests.exceptions.RequestException("Error"),
            Mock(content=b'<html><body>Test</body></html>', raise_for_status=Mock())
        ]
        
        scraper = PortalInmobiliarioScraper('venta', 'departamento')
        result = scraper.fetch_page('http://test.com')
        
        assert isinstance(result, BeautifulSoup)
        assert mock_get.call_count == 2


class TestExtractProperties:
    """Tests para el método extract_properties"""
    
    def test_extract_properties_success(self):
        """Test extracción de propiedades exitosa"""
        html = """
        <html>
            <body>
                <div data-id="MLC-12345678" data-posting-type="used">
                    <h2 class="ui-search-item__title">Departamento Test</h2>
                    <span class="andes-money-amount__fraction">1000</span>
                    <span class="ui-search-item__location-label">Santiago</span>
                    <a class="ui-search-link" href="http://test.com">Link</a>
                </div>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'lxml')
        scraper = PortalInmobiliarioScraper('venta', 'departamento')
        
        result = scraper.extract_properties(soup)
        
        assert len(result) == 1
        assert result[0]['id'] == 'MLC-12345678'
        assert result[0]['titulo'] == 'Departamento Test'
    
    def test_extract_properties_no_listings(self):
        """Test cuando no hay listados"""
        html = '<html><body><p>No listings</p></body></html>'
        soup = BeautifulSoup(html, 'lxml')
        scraper = PortalInmobiliarioScraper('venta', 'departamento')
        
        result = scraper.extract_properties(soup)
        
        assert len(result) == 0
    
    def test_extract_properties_multiple(self):
        """Test extracción de múltiples propiedades"""
        html = """
        <html>
            <body>
                <div data-id="MLC-12345678" data-posting-type="used">
                    <h2 class="ui-search-item__title">Prop 1</h2>
                    <span class="andes-money-amount__fraction">1000</span>
                    <span class="ui-search-item__location-label">Santiago</span>
                    <a class="ui-search-link" href="http://test1.com">Link</a>
                </div>
                <div data-id="MLC-87654321" data-posting-type="used">
                    <h2 class="ui-search-item__title">Prop 2</h2>
                    <span class="andes-money-amount__fraction">2000</span>
                    <span class="ui-search-item__location-label">Providencia</span>
                    <a class="ui-search-link" href="http://test2.com">Link</a>
                </div>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'lxml')
        scraper = PortalInmobiliarioScraper('venta', 'departamento')
        
        result = scraper.extract_properties(soup)
        
        assert len(result) == 2


class TestExtractPropertyData:
    """Tests para el método _extract_property_data"""
    
    def test_extract_property_data_complete(self):
        """Test extracción de datos completos"""
        html = """
        <div data-id="MLC-12345678" data-posting-type="used">
            <h2 class="ui-search-item__title">Departamento Test</h2>
            <span class="andes-money-amount__fraction">UF 3000</span>
            <span class="ui-search-item__location-label">Santiago Centro</span>
            <a class="ui-search-link" href="http://test.com">Link</a>
        </div>
        """
        soup = BeautifulSoup(html, 'lxml')
        listing = soup.find('div')
        scraper = PortalInmobiliarioScraper('venta', 'departamento')
        
        result = scraper._extract_property_data(listing)
        
        assert result is not None
        assert result['id'] == 'MLC-12345678'
        assert result['titulo'] == 'Departamento Test'
        assert result['precio'] == 'UF 3000'
        assert result['ubicacion'] == 'Santiago Centro'
        assert result['url'] == 'http://test.com'
        assert result['operacion'] == 'venta'
        assert result['tipo'] == 'departamento'
    
    def test_extract_property_data_missing_fields(self):
        """Test extracción con campos faltantes"""
        html = '<div data-id="MLC-12345678" data-posting-type="used"></div>'
        soup = BeautifulSoup(html, 'lxml')
        listing = soup.find('div')
        scraper = PortalInmobiliarioScraper('venta', 'departamento')
        
        result = scraper._extract_property_data(listing)
        
        assert result is not None
        assert result['id'] == 'MLC-12345678'
        assert result['titulo'] == 'N/A'
        assert result['precio'] == 'N/A'


class TestHasNextPage:
    """Tests para el método has_next_page"""
    
    def test_has_next_page_true(self):
        """Test cuando hay siguiente página"""
        html = """
        <html>
            <body>
                <li class="andes-pagination__button--next">
                    <a class="andes-pagination__link">Siguiente</a>
                </li>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'lxml')
        scraper = PortalInmobiliarioScraper('venta', 'departamento')
        
        result = scraper.has_next_page(soup)
        
        assert result is True
    
    def test_has_next_page_disabled(self):
        """Test cuando siguiente página está deshabilitada"""
        html = """
        <html>
            <body>
                <li class="andes-pagination__button--next">
                    <a class="andes-pagination__link andes-pagination__link--disabled">Siguiente</a>
                </li>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'lxml')
        scraper = PortalInmobiliarioScraper('venta', 'departamento')
        
        result = scraper.has_next_page(soup)
        
        assert result is False
    
    def test_has_next_page_no_element(self):
        """Test cuando no hay elemento de paginación"""
        html = '<html><body><p>No pagination</p></body></html>'
        soup = BeautifulSoup(html, 'lxml')
        scraper = PortalInmobiliarioScraper('venta', 'departamento')
        
        result = scraper.has_next_page(soup)
        
        assert result is False


class TestScrapeAllPages:
    """Tests para el método scrape_all_pages"""
    
    @patch('scraper.PortalInmobiliarioScraper.fetch_page')
    @patch('scraper.time.sleep')
    def test_scrape_all_pages_max_pages(self, mock_sleep, mock_fetch):
        """Test con límite de páginas"""
        html = """
        <html>
            <body>
                <div data-id="MLC-12345678" data-posting-type="used">
                    <h2 class="ui-search-item__title">Prop 1</h2>
                    <span class="andes-money-amount__fraction">1000</span>
                    <span class="ui-search-item__location-label">Santiago</span>
                    <a class="ui-search-link" href="http://test.com">Link</a>
                </div>
                <li class="andes-pagination__button--next">
                    <a class="andes-pagination__link">Siguiente</a>
                </li>
            </body>
        </html>
        """
        mock_fetch.return_value = BeautifulSoup(html, 'lxml')
        scraper = PortalInmobiliarioScraper('venta', 'departamento')
        
        result = scraper.scrape_all_pages(max_pages=2)
        
        assert len(result) == 2
        assert mock_fetch.call_count == 2
    
    @patch('scraper.PortalInmobiliarioScraper.fetch_page')
    def test_scrape_all_pages_no_properties(self, mock_fetch):
        """Test cuando no hay propiedades"""
        html = '<html><body><p>No properties</p></body></html>'
        mock_fetch.return_value = BeautifulSoup(html, 'lxml')
        scraper = PortalInmobiliarioScraper('venta', 'departamento')
        
        result = scraper.scrape_all_pages()
        
        assert len(result) == 0
    
    @patch('scraper.PortalInmobiliarioScraper.fetch_page')
    def test_scrape_all_pages_fetch_failure(self, mock_fetch):
        """Test cuando falla fetch_page"""
        mock_fetch.return_value = None
        scraper = PortalInmobiliarioScraper('venta', 'departamento')
        
        result = scraper.scrape_all_pages()
        
        assert len(result) == 0


class TestGetProperties:
    """Tests para el método get_properties"""
    
    def test_get_properties_empty(self):
        """Test get_properties cuando está vacío"""
        scraper = PortalInmobiliarioScraper('venta', 'departamento')
        result = scraper.get_properties()
        assert result == []
    
    def test_get_properties_with_data(self):
        """Test get_properties con datos"""
        scraper = PortalInmobiliarioScraper('venta', 'departamento')
        scraper.propiedades = [{'id': 'MLC-123', 'titulo': 'Test'}]
        result = scraper.get_properties()
        assert len(result) == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
