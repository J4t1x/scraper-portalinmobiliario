"""
Tests unitarios para data_loader.py
"""

import json
import os
import pytest
from pathlib import Path
from data_loader import JSONDataLoader


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_json_data():
    """Datos JSON de ejemplo"""
    return {
        "metadata": {
            "operacion": "venta",
            "tipo": "departamento",
            "total": 3,
            "fecha_scraping": "2026-04-09T00:00:00"
        },
        "propiedades": [
            {
                "id": "MLC-11111111",
                "titulo": "Departamento en Providencia",
                "precio": "UF 3.000",
                "ubicacion": "Providencia, Santiago",
                "operacion": "venta",
                "tipo": "departamento"
            },
            {
                "id": "MLC-22222222",
                "titulo": "Casa en Las Condes",
                "precio": "$ 200.000.000",
                "ubicacion": "Las Condes, Santiago",
                "operacion": "venta",
                "tipo": "casa"
            },
            {
                "id": "MLC-33333333",
                "titulo": "Departamento en Ñuñoa",
                "precio": "$ 150.000.000",
                "ubicacion": "Ñuñoa, Santiago",
                "operacion": "arriendo",
                "tipo": "departamento"
            }
        ]
    }


@pytest.fixture
def temp_output_dir(tmp_path):
    """Directorio de salida temporal con archivos JSON"""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # Crear archivo JSON de prueba
    json_file = output_dir / "venta_departamento_20260409.json"
    data = {
        "metadata": {
            "operacion": "venta",
            "tipo": "departamento",
            "total": 2,
            "fecha_scraping": "2026-04-09T00:00:00"
        },
        "propiedades": [
            {
                "id": "MLC-11111111",
                "titulo": "Departamento en Providencia",
                "precio": "UF 3.000",
                "ubicacion": "Providencia, Santiago",
                "operacion": "venta",
                "tipo": "departamento"
            },
            {
                "id": "MLC-22222222",
                "titulo": "Casa en Las Condes",
                "precio": "$ 200.000.000",
                "ubicacion": "Las Condes, Santiago",
                "operacion": "venta",
                "tipo": "casa"
            }
        ]
    }
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # Crear segundo archivo JSON
    json_file2 = output_dir / "arriendo_departamento_20260409.json"
    data2 = {
        "metadata": {
            "operacion": "arriendo",
            "tipo": "departamento",
            "total": 1,
            "fecha_scraping": "2026-04-09T00:00:00"
        },
        "propiedades": [
            {
                "id": "MLC-33333333",
                "titulo": "Departamento en Ñuñoa",
                "precio": "$ 150.000.000",
                "ubicacion": "Ñuñoa, Santiago",
                "operacion": "arriendo",
                "tipo": "departamento"
            }
        ]
    }
    with open(json_file2, 'w', encoding='utf-8') as f:
        json.dump(data2, f, ensure_ascii=False, indent=2)
    
    return str(output_dir)


@pytest.fixture
def temp_output_dir_with_invalid(tmp_path):
    """Directorio con archivo JSON inválido"""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # Archivo válido
    json_file = output_dir / "valid.json"
    data = {
        "metadata": {"operacion": "venta", "tipo": "departamento"},
        "propiedades": [{"id": "MLC-111", "titulo": "Test", "operacion": "venta", "tipo": "departamento"}]
    }
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f)
    
    # Archivo inválido
    invalid_file = output_dir / "invalid.json"
    with open(invalid_file, 'w', encoding='utf-8') as f:
        f.write("{ invalid json content")
    
    return str(output_dir)


# ============================================================================
# Tests de Inicialización
# ============================================================================

def test_init_with_valid_directory(temp_output_dir):
    """Test inicialización con directorio válido"""
    loader = JSONDataLoader(temp_output_dir)
    assert loader.output_dir == Path(temp_output_dir)


def test_init_with_invalid_directory():
    """Test inicialización con directorio inválido"""
    with pytest.raises(FileNotFoundError):
        JSONDataLoader('/nonexistent/directory')


# ============================================================================
# Tests de Carga de Archivos
# ============================================================================

def test_load_all_json_files(temp_output_dir):
    """Test carga de todos los archivos JSON"""
    loader = JSONDataLoader(temp_output_dir)
    properties = loader.load_all_json_files()
    
    assert len(properties) == 3
    assert properties[0]['id'] == 'MLC-11111111'
    assert properties[1]['id'] == 'MLC-22222222'
    assert properties[2]['id'] == 'MLC-33333333'


def test_load_all_json_files_with_invalid(temp_output_dir_with_invalid):
    """Test carga con archivo JSON inválido (debe continuar)"""
    loader = JSONDataLoader(temp_output_dir_with_invalid)
    properties = loader.load_all_json_files()
    
    # Debe cargar solo el archivo válido
    assert len(properties) == 1
    assert properties[0]['id'] == 'MLC-111'


def test_load_all_json_files_empty_directory(tmp_path):
    """Test carga con directorio vacío"""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    loader = JSONDataLoader(str(output_dir))
    properties = loader.load_all_json_files()
    
    assert len(properties) == 0


# ============================================================================
# Tests de Filtros
# ============================================================================

def test_filter_by_operacion(temp_output_dir):
    """Test filtro por operación"""
    loader = JSONDataLoader(temp_output_dir)
    properties = loader.load_by_filters(operacion='venta')
    
    assert len(properties) == 2
    assert all(p['operacion'] == 'venta' for p in properties)


def test_filter_by_tipo(temp_output_dir):
    """Test filtro por tipo"""
    loader = JSONDataLoader(temp_output_dir)
    properties = loader.load_by_filters(tipo='departamento')
    
    assert len(properties) == 2
    assert all(p['tipo'] == 'departamento' for p in properties)


def test_filter_by_operacion_and_tipo(temp_output_dir):
    """Test filtro combinado por operación y tipo"""
    loader = JSONDataLoader(temp_output_dir)
    properties = loader.load_by_filters(operacion='venta', tipo='departamento')
    
    assert len(properties) == 1
    assert properties[0]['id'] == 'MLC-11111111'


def test_filter_by_price_range(temp_output_dir):
    """Test filtro por rango de precio"""
    loader = JSONDataLoader(temp_output_dir)
    properties = loader.load_by_filters(precio_min=100000000, precio_max=180000000)
    
    assert len(properties) == 1
    assert properties[0]['id'] == 'MLC-33333333'


def test_filter_by_price_min_only(temp_output_dir):
    """Test filtro por precio mínimo"""
    loader = JSONDataLoader(temp_output_dir)
    properties = loader.load_by_filters(precio_min=160000000)
    
    assert len(properties) == 1
    assert properties[0]['id'] == 'MLC-22222222'


def test_filter_by_price_max_only(temp_output_dir):
    """Test filtro por precio máximo"""
    loader = JSONDataLoader(temp_output_dir)
    properties = loader.load_by_filters(precio_max=180000000)
    
    assert len(properties) == 1
    assert properties[0]['id'] == 'MLC-33333333'


def test_search_text(temp_output_dir):
    """Test búsqueda por texto"""
    loader = JSONDataLoader(temp_output_dir)
    properties = loader.load_by_filters(search='Providencia')
    
    assert len(properties) == 1
    assert 'Providencia' in properties[0]['titulo'] or 'Providencia' in properties[0]['ubicacion']


def test_search_text_case_insensitive(temp_output_dir):
    """Test búsqueda por texto case-insensitive"""
    loader = JSONDataLoader(temp_output_dir)
    properties = loader.load_by_filters(search='providencia')
    
    assert len(properties) == 1


def test_search_text_no_results(temp_output_dir):
    """Test búsqueda sin resultados"""
    loader = JSONDataLoader(temp_output_dir)
    properties = loader.load_by_filters(search='NoExiste')
    
    assert len(properties) == 0


def test_filter_no_filters(temp_output_dir):
    """Test sin filtros (carga todo)"""
    loader = JSONDataLoader(temp_output_dir)
    properties = loader.load_by_filters()
    
    assert len(properties) == 3


# ============================================================================
# Tests de Estadísticas
# ============================================================================

def test_get_stats(temp_output_dir):
    """Test obtención de estadísticas"""
    loader = JSONDataLoader(temp_output_dir)
    stats = loader.get_stats()
    
    assert stats['total'] == 3
    assert stats['by_operacion']['venta'] == 2
    assert stats['by_operacion']['arriendo'] == 1
    assert stats['by_tipo']['departamento'] == 2
    assert stats['by_tipo']['casa'] == 1
    assert stats['files_loaded'] == 2


def test_get_stats_empty_directory(tmp_path):
    """Test estadísticas con directorio vacío"""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    loader = JSONDataLoader(str(output_dir))
    stats = loader.get_stats()
    
    assert stats['total'] == 0
    assert stats['files_loaded'] == 0
    assert stats['by_operacion'] == {}
    assert stats['by_tipo'] == {}


# ============================================================================
# Tests de Paginación
# ============================================================================

def test_paginate_first_page(temp_output_dir):
    """Test paginación primera página"""
    loader = JSONDataLoader(temp_output_dir)
    properties = loader.load_all_json_files()
    result = loader.paginate(properties, page=1, per_page=2)
    
    assert len(result['data']) == 2
    assert result['page'] == 1
    assert result['per_page'] == 2
    assert result['total'] == 3
    assert result['total_pages'] == 2
    assert result['has_next'] is True
    assert result['has_prev'] is False


def test_paginate_second_page(temp_output_dir):
    """Test paginación segunda página"""
    loader = JSONDataLoader(temp_output_dir)
    properties = loader.load_all_json_files()
    result = loader.paginate(properties, page=2, per_page=2)
    
    assert len(result['data']) == 1
    assert result['page'] == 2
    assert result['has_next'] is False
    assert result['has_prev'] is True


def test_paginate_page_out_of_range(temp_output_dir):
    """Test paginación con página fuera de rango"""
    loader = JSONDataLoader(temp_output_dir)
    properties = loader.load_all_json_files()
    result = loader.paginate(properties, page=10, per_page=2)
    
    # Debe retornar la última página
    assert result['page'] == 2
    assert len(result['data']) == 1


def test_paginate_page_zero(temp_output_dir):
    """Test paginación con página 0 (debe ser 1)"""
    loader = JSONDataLoader(temp_output_dir)
    properties = loader.load_all_json_files()
    result = loader.paginate(properties, page=0, per_page=2)
    
    assert result['page'] == 1


def test_paginate_empty_list():
    """Test paginación con lista vacía"""
    loader = JSONDataLoader('output')  # No se usa el directorio
    result = loader.paginate([], page=1, per_page=20)
    
    assert len(result['data']) == 0
    assert result['total'] == 0
    assert result['total_pages'] == 0
    assert result['has_next'] is False
    assert result['has_prev'] is False


def test_paginate_custom_per_page(temp_output_dir):
    """Test paginación con per_page personalizado"""
    loader = JSONDataLoader(temp_output_dir)
    properties = loader.load_all_json_files()
    result = loader.paginate(properties, page=1, per_page=1)
    
    assert len(result['data']) == 1
    assert result['per_page'] == 1
    assert result['total_pages'] == 3


# ============================================================================
# Tests de Extracción de Precio
# ============================================================================

def test_extract_price_clp_clp():
    """Test extracción de precio en CLP"""
    loader = JSONDataLoader('output')
    price = loader._extract_price_clp('$ 150.000.000')
    
    assert price == 150000000.0


def test_extract_price_clp_no_symbol():
    """Test extracción de precio sin símbolo"""
    loader = JSONDataLoader('output')
    price = loader._extract_price_clp('150000000')
    
    assert price == 150000000.0


def test_extract_price_clp_uf():
    """Test extracción de precio en UF (debe retornar None)"""
    loader = JSONDataLoader('output')
    price = loader._extract_price_clp('UF 3.000')
    
    assert price is None


def test_extract_price_clp_empty():
    """Test extracción de precio vacío"""
    loader = JSONDataLoader('output')
    price = loader._extract_price_clp('')
    
    assert price is None


def test_extract_price_clp_none():
    """Test extracción de precio None"""
    loader = JSONDataLoader('output')
    price = loader._extract_price_clp(None)
    
    assert price is None


def test_extract_price_clp_invalid():
    """Test extracción de precio inválido"""
    loader = JSONDataLoader('output')
    price = loader._extract_price_clp('INVALIDO')
    
    assert price is None
