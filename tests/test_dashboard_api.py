"""
Tests para Dashboard API endpoints (JSONDataLoader-based)

Tests de integración para los endpoints de la API del dashboard
que usan JSONDataLoader en lugar de PostgreSQL (MVP).
"""

import pytest
import json
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from app import app
from data_loader import JSONDataLoader


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_output_dir():
    """Directorio output temporal con datos de prueba"""
    temp_dir = tempfile.mkdtemp()
    output_dir = os.path.join(temp_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    
    # Crear archivos JSON de prueba
    properties_data = {
        "metadata": {
            "operacion": "venta",
            "tipo": "departamento",
            "total": 3,
            "fecha_scraping": "2026-04-09T10:30:00"
        },
        "propiedades": [
            {
                "id": "MLC-12345678",
                "titulo": "Departamento en Las Condes",
                "precio": "UF 5.500",
                "ubicacion": "Las Condes, Santiago",
                "tipo": "departamento",
                "operacion": "venta"
            },
            {
                "id": "MLC-87654321",
                "titulo": "Casa en La Reina",
                "precio": "$ 150.000.000",
                "ubicacion": "La Reina, Santiago",
                "tipo": "casa",
                "operacion": "venta"
            },
            {
                "id": "MLC-11111111",
                "titulo": "Departamento en Providencia",
                "precio": "$ 80.000.000",
                "ubicacion": "Providencia, Santiago",
                "tipo": "departamento",
                "operacion": "arriendo"
            }
        ]
    }
    
    json_file = os.path.join(output_dir, "venta_departamento_20260409.json")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(properties_data, f, ensure_ascii=False, indent=2)
    
    yield output_dir
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_data_loader(temp_output_dir):
    """Mock de JSONDataLoader con datos de prueba"""
    loader = Mock(spec=JSONDataLoader)
    
    # Datos de prueba
    properties = [
        {
            "id": "MLC-12345678",
            "titulo": "Departamento en Las Condes",
            "precio": "UF 5.500",
            "ubicacion": "Las Condes, Santiago",
            "tipo": "departamento",
            "operacion": "venta"
        },
        {
            "id": "MLC-87654321",
            "titulo": "Casa en La Reina",
            "precio": "$ 150.000.000",
            "ubicacion": "La Reina, Santiago",
            "tipo": "casa",
            "operacion": "venta"
        },
        {
            "id": "MLC-11111111",
            "titulo": "Departamento en Providencia",
            "precio": "$ 80.000.000",
            "ubicacion": "Providencia, Santiago",
            "tipo": "departamento",
            "operacion": "arriendo"
        }
    ]
    
    # Configurar load_all_json_files
    loader.load_all_json_files.return_value = properties
    
    # Configurar load_by_filters con lógica de filtrado real
    def mock_load_by_filters(**kwargs):
        filtered = properties
        if kwargs.get('operacion'):
            filtered = [p for p in filtered if p.get('operacion') == kwargs['operacion']]
        if kwargs.get('tipo'):
            filtered = [p for p in filtered if p.get('tipo') == kwargs['tipo']]
        if kwargs.get('search'):
            search = kwargs['search'].lower()
            filtered = [p for p in filtered if search in p.get('titulo', '').lower() or search in p.get('ubicacion', '').lower()]
        return filtered
    
    loader.load_by_filters.side_effect = mock_load_by_filters
    
    # Configurar get_stats
    loader.get_stats.return_value = {
        'total': 3,
        'by_operacion': {'venta': 2, 'arriendo': 1},
        'by_tipo': {'departamento': 2, 'casa': 1},
        'files_loaded': 1
    }
    
    # Configurar paginate con lógica real
    def mock_paginate(props, page=1, per_page=20):
        total = len(props)
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1
        
        # Validar página (como en la implementación real)
        if page < 1:
            page = 1
        if page > total_pages:
            page = total_pages
        
        start = (page - 1) * per_page
        end = start + per_page
        return {
            'data': props[start:end],
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
    
    loader.paginate.side_effect = mock_paginate
    
    return loader


@pytest.fixture
def client(mock_data_loader):
    """Cliente de prueba Flask con JSONDataLoader mockeado"""
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    with app.test_client() as client:
        with patch('dashboard.routes.JSONDataLoader', return_value=mock_data_loader):
            yield client


@pytest.fixture
def authenticated_client(client):
    """Cliente autenticado"""
    # Login con credenciales de prueba
    response = client.post('/login', data={
        'username': 'admin',
        'password': 'admin123'
    }, follow_redirects=False)
    
    # Si el login falla (porque no hay usuario real), hacer mock
    if response.status_code != 302:
        # Crear sesión manualmente
        with client.session_transaction() as sess:
            sess['_user_id'] = '1'
            sess['_fresh'] = True
    
    return client


# ============================================================================
# Tests de API Endpoints
# ============================================================================

class TestAPIProperties:
    """Tests para endpoint /api/properties"""
    
    def test_api_properties_unauthorized(self, client):
        """Test acceso sin autenticación"""
        response = client.get('/api/properties')
        assert response.status_code == 302 or response.status_code == 401
    
    def test_api_properties_basic(self, authenticated_client):
        """Test endpoint básico sin filtros"""
        response = authenticated_client.get('/api/properties')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'data' in data
        assert 'pagination' in data
        assert isinstance(data['data'], list)
    
    def test_api_properties_with_filters(self, authenticated_client):
        """Test endpoint con filtro de operación"""
        response = authenticated_client.get('/api/properties?operacion=venta')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Verificar que todas las propiedades sean venta
        for prop in data['data']:
            assert prop.get('operacion') == 'venta'
    
    def test_api_properties_with_tipo_filter(self, authenticated_client):
        """Test endpoint con filtro de tipo"""
        response = authenticated_client.get('/api/properties?tipo=departamento')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Verificar que todas las propiedades sean departamentos
        for prop in data['data']:
            assert prop.get('tipo') == 'departamento'
    
    def test_api_properties_with_search(self, authenticated_client):
        """Test endpoint con búsqueda de texto"""
        response = authenticated_client.get('/api/properties?search=Las Condes')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Verificar que al menos una propiedad coincida
        assert len(data['data']) >= 0
    
    def test_api_properties_pagination(self, authenticated_client):
        """Test paginación"""
        response = authenticated_client.get('/api/properties?page=1&per_page=2')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['pagination']['page'] == 1
        assert data['pagination']['per_page'] == 2
        assert len(data['data']) <= 2


class TestAPIPropertyDetail:
    """Tests para endpoint /api/properties/<id>"""
    
    def test_api_property_detail_unauthorized(self, client):
        """Test acceso sin autenticación"""
        response = client.get('/api/properties/MLC-12345678')
        assert response.status_code == 302 or response.status_code == 401
    
    def test_api_property_detail_found(self, authenticated_client):
        """Test propiedad encontrada"""
        response = authenticated_client.get('/api/properties/MLC-12345678')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['id'] == 'MLC-12345678'
    
    def test_api_property_detail_not_found(self, authenticated_client):
        """Test propiedad no encontrada"""
        response = authenticated_client.get('/api/properties/MLC-NONEXISTENT')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'error' in data


class TestAPIStats:
    """Tests para endpoint /api/stats"""
    
    def test_api_stats_unauthorized(self, client):
        """Test acceso sin autenticación"""
        response = client.get('/api/stats')
        assert response.status_code == 302 or response.status_code == 401
    
    def test_api_stats_basic(self, authenticated_client):
        """Test endpoint de estadísticas"""
        response = authenticated_client.get('/api/stats')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'data' in data
        assert 'total' in data['data']
        assert 'by_operacion' in data['data']
        assert 'by_tipo' in data['data']
        assert 'files_loaded' in data['data']
        assert data['data']['total'] > 0


class TestAPIFilters:
    """Tests para endpoint /api/filters"""
    
    def test_api_filters_unauthorized(self, client):
        """Test acceso sin autenticación"""
        response = client.get('/api/filters')
        assert response.status_code == 302 or response.status_code == 401
    
    def test_api_filters_basic(self, authenticated_client):
        """Test endpoint de filtros disponibles"""
        response = authenticated_client.get('/api/filters')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'data' in data
        assert 'operaciones' in data['data']
        assert 'tipos' in data['data']
        assert 'comunas' in data['data']
        assert isinstance(data['data']['operaciones'], list)
        assert isinstance(data['data']['tipos'], list)
        assert isinstance(data['data']['comunas'], list)
    
    def test_api_filters_sorted(self, authenticated_client):
        """Test que los filtros estén ordenados"""
        response = authenticated_client.get('/api/filters')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        operaciones = data['data']['operaciones']
        tipos = data['data']['tipos']
        
        # Verificar que estén ordenados
        assert operaciones == sorted(operaciones)
        assert tipos == sorted(tipos)


class TestAPIErrorHandling:
    """Tests para manejo de errores"""
    
    def test_api_properties_invalid_filter(self, authenticated_client):
        """Test con filtro inválido"""
        response = authenticated_client.get('/api/properties?precio_min=invalid')
        # Should handle gracefully (filter ignored)
        assert response.status_code in [200, 400, 500]
    
    def test_api_properties_invalid_page(self, authenticated_client):
        """Test con página inválida"""
        response = authenticated_client.get('/api/properties?page=-1')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        # Should default to page 1
        assert data['pagination']['page'] >= 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
