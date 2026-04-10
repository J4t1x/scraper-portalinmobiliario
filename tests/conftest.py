"""
Fixtures compartidos para tests del scraper-portalinmobiliario
"""

import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import MagicMock, Mock

import pytest

# Agregar directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================================
# Fixtures de Propiedades
# ============================================================================

@pytest.fixture
def sample_property() -> Dict[str, Any]:
    """Propiedad de ejemplo completa"""
    return {
        "id": "MLC-12345678",
        "titulo": "Departamento en Las Condes",
        "precio": "UF 5.500",
        "precio_clp": 220000000,
        "moneda": "UF",
        "monto": 5500.0,
        "ubicacion": "Las Condes, Santiago",
        "dormitorios": 3,
        "banos": 2,
        "metros_cuadrados": 85,
        "tipo": "departamento",
        "operacion": "venta",
        "url": "https://www.portalinmobiliario.com/MLC-12345678-departamento-en-las-condes",
        "descripcion": "Hermoso departamento con vista panorámica",
        "features": ["gimnasio", "piscina", "quinchos"],
        "imagenes": ["https://img1.jpg", "https://img2.jpg"],
        "coordenadas": {"lat": -33.4, "lng": -70.6},
        "fecha_publicacion": "2026-04-01",
        "is_duplicate": False
    }


@pytest.fixture
def sample_property_minimal() -> Dict[str, Any]:
    """Propiedad mínima válida"""
    return {
        "id": "MLC-87654321",
        "titulo": "Casa en La Reina",
        "precio": "$ 150.000.000",
        "ubicacion": "La Reina, Santiago"
    }


@pytest.fixture
def sample_properties_list() -> List[Dict[str, Any]]:
    """Lista de propiedades de ejemplo"""
    return [
        {
            "id": "MLC-11111111",
            "titulo": "Departamento 1",
            "precio": "UF 3.000",
            "ubicacion": "Providencia"
        },
        {
            "id": "MLC-22222222",
            "titulo": "Departamento 2",
            "precio": "UF 4.000",
            "ubicacion": "Las Condes"
        },
        {
            "id": "MLC-33333333",
            "titulo": "Casa",
            "precio": "$ 200.000.000",
            "ubicacion": "La Reina"
        }
    ]


@pytest.fixture
def invalid_property_no_id() -> Dict[str, Any]:
    """Propiedad inválida - sin ID"""
    return {
        "titulo": "Departamento sin ID",
        "precio": "UF 3.000",
        "ubicacion": "Santiago"
    }


@pytest.fixture
def invalid_property_bad_price() -> Dict[str, Any]:
    """Propiedad con precio inválido - ID válido para test de warnings"""
    return {
        "id": "MLC-87654321",
        "titulo": "Propiedad con precio inválido",
        "precio": "INVALIDO",
        "ubicacion": "Santiago"
    }


# ============================================================================
# Fixtures de Directorios Temporales
# ============================================================================

@pytest.fixture
def temp_dir():
    """Directorio temporal para tests"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def temp_output_dir(temp_dir):
    """Directorio de salida temporal"""
    output_path = os.path.join(temp_dir, "output")
    os.makedirs(output_path, exist_ok=True)
    return output_path


# ============================================================================
# Fixtures de Mock WebDriver
# ============================================================================

@pytest.fixture
def mock_webdriver():
    """Mock de Selenium WebDriver"""
    driver = MagicMock()
    driver.page_source = "<html><body>Mock HTML</body></html>"
    driver.find_elements.return_value = []
    driver.find_element.return_value = MagicMock()
    return driver


@pytest.fixture
def mock_webdriver_with_elements():
    """Mock de WebDriver con elementos"""
    driver = MagicMock()
    
    # Mock de elementos
    mock_element = MagicMock()
    mock_element.text = "Departamento en Venta - UF 3.000 - Las Condes"
    mock_element.get_attribute.return_value = "https://www.portalinmobiliario.com/MLC-12345678-propiedad"
    
    driver.find_elements.return_value = [mock_element]
    driver.find_element.return_value = mock_element
    
    return driver


# ============================================================================
# Fixtures de HTML de Prueba
# ============================================================================

@pytest.fixture
def sample_listing_html() -> str:
    """HTML de página de listado de propiedades"""
    return """
    <html>
    <body>
        <div class="ui-search-result__wrapper">
            <a href="https://www.portalinmobiliario.com/MLC-12345678-propiedad-1">
                <h2>Departamento en Las Condes</h2>
            </a>
            <span class="price">UF 5.500</span>
            <span class="location">Las Condes, Santiago</span>
        </div>
        <div class="ui-search-result__wrapper">
            <a href="https://www.portalinmobiliario.com/MLC-87654321-propiedad-2">
                <h2>Casa en La Reina</h2>
            </a>
            <span class="price">$ 150.000.000</span>
            <span class="location">La Reina, Santiago</span>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def sample_detail_html() -> str:
    """HTML de página de detalle de propiedad"""
    return """
    <html>
    <body>
        <h1>Departamento en Venta Las Condes</h1>
        <div class="price">UF 5.500</div>
        <div class="location">Las Condes, Santiago</div>
        <div class="description">
            Hermoso departamento de 3 dormitorios y 2 baños.
            85 m² construidos. Excelente ubicación.
        </div>
        <ul class="features">
            <li>Gimnasio</li>
            <li>Piscina</li>
            <li>Quinchos</li>
        </ul>
    </body>
    </html>
    """


# ============================================================================
# Fixtures de Configuración
# ============================================================================

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Variables de entorno de prueba"""
    env_vars = {
        "DELAY_BETWEEN_REQUESTS": "1",
        "MAX_RETRIES": "2",
        "TIMEOUT": "10",
        "USER_AGENT": "Test-Agent/1.0",
        "HEADLESS": "true"
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    return env_vars


# ============================================================================
# Fixtures de Archivos
# ============================================================================

@pytest.fixture
def sample_json_file(temp_dir, sample_properties_list):
    """Archivo JSON de propiedades"""
    filepath = os.path.join(temp_dir, "properties.json")
    data = {
        "metadata": {
            "operacion": "venta",
            "tipo": "departamento",
            "total": len(sample_properties_list),
            "fecha_scraping": "2026-04-09T00:00:00"
        },
        "propiedades": sample_properties_list
    }
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return filepath


@pytest.fixture
def sample_txt_file(temp_dir, sample_properties_list):
    """Archivo TXT (JSONL) de propiedades"""
    filepath = os.path.join(temp_dir, "properties.txt")
    with open(filepath, 'w', encoding='utf-8') as f:
        for prop in sample_properties_list:
            f.write(json.dumps(prop, ensure_ascii=False) + '\n')
    return filepath
