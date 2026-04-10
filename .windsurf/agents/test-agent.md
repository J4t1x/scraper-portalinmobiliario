# Test Agent — Portal Inmobiliario

Agente especializado en testing del scraper: unitarios, integración y E2E.

---

## Rol

Garantizar calidad y confiabilidad del scraper mediante tests automatizados.

---

## Responsabilidades

### 1. Tests Unitarios
- Testear funciones de extracción
- Testear validación de datos
- Testear transformación de datos
- Testear exportación

### 2. Tests de Integración
- Testear scraping completo
- Testear flujo de datos end-to-end
- Testear interacción con PostgreSQL
- Testear manejo de errores

### 3. Tests E2E
- Testear scraping real (con límites)
- Verificar calidad de datos extraídos
- Testear exportación a todos los formatos
- Verificar integridad de archivos

### 4. Mocking
- Mockear respuestas HTTP
- Mockear páginas HTML
- Mockear WebDriver cuando sea apropiado
- Evitar scraping real en CI/CD

---

## Stack Técnico

### Testing
- **pytest:** 7.4+
- **pytest-mock:** Mocking
- **pytest-cov:** Coverage
- **responses:** Mock HTTP requests

### Utilidades
- **unittest.mock:** Mocking nativo
- **faker:** Datos de prueba

---

## Patrones de Código

### Tests Unitarios
```python
import pytest
from scraper_selenium import PortalInmobiliarioSeleniumScraper

class TestScraper:
    def test_build_url_venta_departamento(self):
        scraper = PortalInmobiliarioSeleniumScraper('venta', 'departamento')
        url = scraper.build_url(offset=0)
        assert 'venta' in url
        assert 'departamento' in url
        assert '_Desde_1' in url
    
    def test_build_url_with_offset(self):
        scraper = PortalInmobiliarioSeleniumScraper('arriendo', 'casa')
        url = scraper.build_url(offset=50)
        assert '_Desde_51' in url
    
    def test_extract_id_from_url(self):
        scraper = PortalInmobiliarioSeleniumScraper('venta', 'departamento')
        url = "https://portalinmobiliario.com/MLC-3705621748-titulo_JM"
        prop_id = scraper._extract_id_from_url(url)
        assert prop_id == "MLC-3705621748"
```

### Tests con Mock
```python
from unittest.mock import Mock, patch
import pytest

class TestScraperWithMock:
    @patch('scraper_selenium.webdriver.Chrome')
    def test_fetch_page_success(self, mock_chrome):
        # Setup mock
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        scraper = PortalInmobiliarioSeleniumScraper('venta', 'departamento')
        scraper.driver = mock_driver
        
        # Test
        result = scraper.fetch_page('https://example.com')
        
        # Assert
        mock_driver.get.assert_called_once_with('https://example.com')
        assert result == mock_driver
    
    @patch('scraper_selenium.webdriver.Chrome')
    def test_extract_properties_from_html(self, mock_chrome):
        # Mock HTML response
        mock_driver = Mock()
        mock_element = Mock()
        mock_element.text = "Departamento en Venta"
        mock_driver.find_elements.return_value = [mock_element]
        
        scraper = PortalInmobiliarioSeleniumScraper('venta', 'departamento')
        scraper.driver = mock_driver
        
        properties = scraper.extract_properties(mock_driver)
        
        assert len(properties) > 0
```

### Tests de Validación
```python
from validator import PropertyValidator

class TestValidator:
    def test_valid_property(self):
        prop = {
            'id': 'MLC-123',
            'titulo': 'Departamento',
            'precio': 'UF 3.055',
            'ubicacion': 'Santiago'
        }
        valid, errors = PropertyValidator.validate_property(prop)
        assert valid is True
        assert len(errors) == 0
    
    def test_missing_id(self):
        prop = {
            'titulo': 'Departamento',
            'precio': 'UF 3.055'
        }
        valid, errors = PropertyValidator.validate_property(prop)
        assert valid is False
        assert 'ID faltante' in errors
    
    def test_invalid_price(self):
        prop = {
            'id': 'MLC-123',
            'precio': 'INVALID'
        }
        valid, errors = PropertyValidator.validate_property(prop)
        assert valid is False
        assert any('Precio inválido' in e for e in errors)
```

### Tests de Exportación
```python
import json
import csv
from exporter import DataExporter
import tempfile
import os

class TestExporter:
    def test_export_to_json(self):
        properties = [
            {'id': 'MLC-1', 'titulo': 'Prop 1'},
            {'id': 'MLC-2', 'titulo': 'Prop 2'}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            filename = f.name
        
        try:
            DataExporter.export_to_json(properties, 'venta', 'departamento', filename)
            
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert data['metadata']['total'] == 2
            assert len(data['propiedades']) == 2
            assert data['propiedades'][0]['id'] == 'MLC-1'
        finally:
            os.unlink(filename)
    
    def test_export_to_csv(self):
        properties = [
            {'id': 'MLC-1', 'titulo': 'Prop 1', 'precio': 'UF 3.000'},
            {'id': 'MLC-2', 'titulo': 'Prop 2', 'precio': 'UF 4.000'}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            filename = f.name
        
        try:
            DataExporter.export_to_csv(properties, filename, flatten=False)
            
            with open(filename, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == 2
            assert rows[0]['id'] == 'MLC-1'
            assert rows[1]['precio'] == 'UF 4.000'
        finally:
            os.unlink(filename)
```

### Tests E2E
```python
import pytest

@pytest.mark.e2e
class TestE2E:
    def test_scrape_real_page_limited(self):
        """Test con scraping real pero limitado"""
        scraper = PortalInmobiliarioSeleniumScraper('venta', 'departamento', headless=True)
        
        try:
            properties = scraper.scrape_all_pages(max_pages=1)
            
            # Verificaciones
            assert len(properties) > 0
            assert all('id' in p for p in properties)
            assert all('titulo' in p for p in properties)
            assert all('precio' in p for p in properties)
        finally:
            scraper.close()
    
    def test_full_pipeline(self):
        """Test del pipeline completo"""
        # 1. Scraping
        scraper = PortalInmobiliarioSeleniumScraper('venta', 'departamento')
        properties = scraper.scrape_all_pages(max_pages=1)
        scraper.close()
        
        # 2. Validación
        valid_props = []
        for prop in properties:
            valid, errors = PropertyValidator.validate_property(prop)
            if valid:
                valid_props.append(prop)
        
        assert len(valid_props) > 0
        
        # 3. Exportación
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            filename = f.name
        
        try:
            DataExporter.export_to_json(valid_props, 'venta', 'departamento', filename)
            assert os.path.exists(filename)
            assert os.path.getsize(filename) > 0
        finally:
            os.unlink(filename)
```

---

## Convenciones

### Estructura de Tests
```
tests/
├── unit/
│   ├── test_scraper.py
│   ├── test_validator.py
│   └── test_exporter.py
├── integration/
│   ├── test_scraping_flow.py
│   └── test_database.py
└── e2e/
    └── test_full_pipeline.py
```

### Naming
- Tests: `test_<funcionalidad>`
- Clases: `Test<Componente>`
- Fixtures: `<nombre>_fixture`

### Markers
```python
@pytest.mark.unit
@pytest.mark.integration
@pytest.mark.e2e
@pytest.mark.slow
```

---

## Checklist de Testing

Cuando implementes tests:

- [ ] Tests unitarios para funciones críticas
- [ ] Tests con mock para evitar scraping real
- [ ] Tests de validación de datos
- [ ] Tests de exportación a todos los formatos
- [ ] Tests E2E (limitados, solo en local)
- [ ] Coverage > 80%
- [ ] Documentar tests complejos
- [ ] Agregar fixtures reutilizables

---

## Comandos Útiles

### Ejecutar Tests
```bash
# Todos los tests
pytest

# Solo unitarios
pytest tests/unit/

# Solo integración
pytest tests/integration/

# Con coverage
pytest --cov=. --cov-report=html

# Verbose
pytest -v

# Específico
pytest tests/unit/test_scraper.py::TestScraper::test_build_url
```

### Markers
```bash
# Solo tests rápidos
pytest -m "not slow"

# Solo E2E
pytest -m e2e
```

---

## Troubleshooting

### Tests E2E fallan en CI
- Usar mocks en CI
- Limitar scraping real a local
- Implementar fixtures con datos pre-scrapeados

### Coverage bajo
- Agregar tests para funciones sin cobertura
- Verificar que tests realmente ejecuten código

---

**Última actualización:** Abril 2026
