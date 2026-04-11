"""
Tests para estadísticas avanzadas del DataLoader
"""

import pytest
import json
from pathlib import Path
from data_loader import JSONDataLoader


@pytest.fixture
def sample_properties():
    """Propiedades de ejemplo para testing"""
    return [
        {
            'id': 'MLC-001',
            'titulo': 'Departamento en Las Condes',
            'precio': '$ 150.000.000',
            'ubicacion': 'Las Condes',
            'operacion': 'venta',
            'tipo': 'departamento',
            'descripcion': 'Hermoso departamento',
            'imagenes': ['img1.jpg', 'img2.jpg'],
            'publisher': {'nombre': 'Inmobiliaria A'},
            'coordenadas': {'lat': -33.4, 'lng': -70.6},
            'scrapeado_en': '2026-04-09T10:00:00'
        },
        {
            'id': 'MLC-002',
            'titulo': 'Casa en Providencia',
            'precio': '$ 250.000.000',
            'ubicacion': 'Providencia',
            'operacion': 'venta',
            'tipo': 'casa',
            'descripcion': 'Casa amplia',
            'imagenes': ['img3.jpg'],
            'publisher': {'nombre': 'Inmobiliaria B'},
            'scrapeado_en': '2026-04-09T11:00:00'
        },
        {
            'id': 'MLC-003',
            'titulo': 'Departamento en Ñuñoa',
            'precio': '$ 80.000.000',
            'ubicacion': 'Ñuñoa',
            'operacion': 'arriendo',
            'tipo': 'departamento',
            'imagenes': [],
            'publisher': {'nombre': 'Inmobiliaria A'},
            'scrapeado_en': '2026-04-08T10:00:00'
        }
    ]


@pytest.fixture
def temp_json_dir(tmp_path, sample_properties):
    """Crear directorio temporal con archivos JSON de prueba"""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # Crear archivo JSON con propiedades
    json_file = output_dir / "test_properties.json"
    data = {
        'metadata': {
            'operacion': 'venta',
            'tipo': 'departamento',
            'total': len(sample_properties),
            'fecha_scraping': '2026-04-09T10:00:00'
        },
        'propiedades': sample_properties
    }
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return output_dir


def test_get_advanced_stats(temp_json_dir):
    """Test de estadísticas avanzadas"""
    loader = JSONDataLoader(str(temp_json_dir))
    stats = loader.get_advanced_stats()
    
    # Verificar estructura
    assert 'basic' in stats
    assert 'prices' in stats
    assert 'completeness' in stats
    assert 'temporal' in stats
    assert 'publishers' in stats
    assert 'by_comuna' in stats
    assert 'price_ranges' in stats
    
    # Verificar básicos
    assert stats['basic']['total'] == 3
    assert stats['basic']['files_loaded'] == 1
    
    # Verificar precios
    assert stats['prices']['total_with_price'] == 3
    assert stats['prices']['avg'] > 0
    assert stats['prices']['min'] == 80000000
    assert stats['prices']['max'] == 250000000
    
    # Verificar completitud
    assert 'overall' in stats['completeness']
    assert 'fields' in stats['completeness']
    assert stats['completeness']['with_images'] == 2
    assert stats['completeness']['with_description'] == 2
    
    # Verificar temporal
    assert 'by_date' in stats['temporal']
    assert len(stats['temporal']['by_date']) == 2  # 2 fechas diferentes
    
    # Verificar publicadores
    assert 'top' in stats['publishers']
    assert stats['publishers']['total_publishers'] == 2


def test_calculate_price_stats(temp_json_dir):
    """Test de cálculo de estadísticas de precios"""
    loader = JSONDataLoader(str(temp_json_dir))
    properties = loader.load_all_json_files()
    
    price_stats = loader._calculate_price_stats(properties)
    
    assert price_stats['avg'] > 0
    assert price_stats['min'] == 80000000
    assert price_stats['max'] == 250000000
    assert price_stats['median'] == 150000000
    assert 'by_operacion' in price_stats
    assert 'by_tipo' in price_stats


def test_calculate_completeness(temp_json_dir):
    """Test de cálculo de completitud"""
    loader = JSONDataLoader(str(temp_json_dir))
    properties = loader.load_all_json_files()
    
    completeness = loader._calculate_completeness(properties)
    
    assert 'overall' in completeness
    assert 'fields' in completeness
    assert completeness['overall'] > 0
    assert completeness['with_images'] == 2
    assert completeness['with_description'] == 2
    assert completeness['with_coordinates'] == 1


def test_calculate_temporal_distribution(temp_json_dir):
    """Test de distribución temporal"""
    loader = JSONDataLoader(str(temp_json_dir))
    properties = loader.load_all_json_files()
    
    temporal = loader._calculate_temporal_distribution(properties)
    
    assert 'by_date' in temporal
    assert 'total_dates' in temporal
    assert 'latest_date' in temporal
    assert 'oldest_date' in temporal
    assert temporal['total_dates'] == 2


def test_calculate_top_publishers(temp_json_dir):
    """Test de top publicadores"""
    loader = JSONDataLoader(str(temp_json_dir))
    properties = loader.load_all_json_files()
    
    publishers = loader._calculate_top_publishers(properties, limit=10)
    
    assert 'top' in publishers
    assert 'total_publishers' in publishers
    assert 'total_with_publisher' in publishers
    assert publishers['total_publishers'] == 2
    assert publishers['total_with_publisher'] == 3


def test_calculate_price_ranges(temp_json_dir):
    """Test de rangos de precio"""
    loader = JSONDataLoader(str(temp_json_dir))
    properties = loader.load_all_json_files()
    
    ranges = loader._calculate_price_ranges(properties)
    
    assert '0-50M' in ranges
    assert '50M-100M' in ranges
    assert '100M-150M' in ranges
    assert '150M-200M' in ranges
    assert '200M+' in ranges
    
    # Verificar distribución
    assert ranges['0-50M'] == 0
    assert ranges['50M-100M'] == 1  # 80M
    assert ranges['100M-150M'] == 0
    assert ranges['150M-200M'] == 1  # 150M
    assert ranges['200M+'] == 1  # 250M


def test_advanced_stats_empty_directory(tmp_path):
    """Test de estadísticas avanzadas con directorio vacío"""
    output_dir = tmp_path / "empty_output"
    output_dir.mkdir()
    
    loader = JSONDataLoader(str(output_dir))
    stats = loader.get_advanced_stats()
    
    assert stats['basic']['total'] == 0
    assert stats['prices']['avg'] == 0
    assert stats['completeness']['overall'] == 0
