"""
Unit tests for data_validator module.
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.data_validator import DataValidator


class TestDataValidator:
    """Test cases for DataValidator class."""
    
    def test_validate_property_success(self):
        """Test validation of a valid property."""
        prop = {
            'id': 'MLC-123',
            'titulo': 'Departamento en venta',
            'precio': 'UF 3.055',
            'ubicacion': 'Santiago, Chile',
            'url': 'https://example.com/MLC-123',
            'operacion': 'venta',
            'tipo': 'departamento'
        }
        
        is_valid, errors = DataValidator.validate_property(prop)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_property_missing_id(self):
        """Test validation fails when ID is missing."""
        prop = {
            'titulo': 'Departamento',
            'precio': 'UF 3.055',
            'ubicacion': 'Santiago',
            'url': 'https://example.com',
            'operacion': 'venta',
            'tipo': 'departamento'
        }
        
        is_valid, errors = DataValidator.validate_property(prop)
        
        assert is_valid is False
        assert any('Missing required field: id' in e for e in errors)
    
    def test_validate_property_missing_required_field(self):
        """Test validation fails when any required field is missing."""
        prop = {
            'id': 'MLC-123',
            'titulo': 'Departamento',
            'precio': 'UF 3.055'
            # Missing ubicacion, url, operacion, tipo
        }
        
        is_valid, errors = DataValidator.validate_property(prop)
        
        assert is_valid is False
        assert len(errors) >= 4  # At least 4 missing required fields
    
    def test_validate_property_invalid_operation(self):
        """Test validation fails with invalid operation type."""
        prop = {
            'id': 'MLC-123',
            'titulo': 'Departamento',
            'precio': 'UF 3.055',
            'ubicacion': 'Santiago',
            'url': 'https://example.com',
            'operacion': 'invalid_operation',
            'tipo': 'departamento'
        }
        
        is_valid, errors = DataValidator.validate_property(prop)
        
        assert is_valid is False
        assert any('Invalid operation' in e for e in errors)
    
    def test_validate_property_invalid_type(self):
        """Test validation fails with invalid property type."""
        prop = {
            'id': 'MLC-123',
            'titulo': 'Departamento',
            'precio': 'UF 3.055',
            'ubicacion': 'Santiago',
            'url': 'https://example.com',
            'operacion': 'venta',
            'tipo': 'invalid_type'
        }
        
        is_valid, errors = DataValidator.validate_property(prop)
        
        assert is_valid is False
        assert any('Invalid property type' in e for e in errors)
    
    def test_validate_property_invalid_price(self):
        """Test validation fails with invalid price format."""
        prop = {
            'id': 'MLC-123',
            'titulo': 'Departamento',
            'precio': 'INVALID_PRICE',
            'ubicacion': 'Santiago',
            'url': 'https://example.com',
            'operacion': 'venta',
            'tipo': 'departamento'
        }
        
        is_valid, errors = DataValidator.validate_property(prop)
        
        assert is_valid is False
        assert any('Invalid price format' in e for e in errors)
    
    def test_validate_property_valid_price_uf(self):
        """Test validation accepts UF price format."""
        prop = {
            'id': 'MLC-123',
            'titulo': 'Departamento',
            'precio': 'UF 3.055',
            'ubicacion': 'Santiago',
            'url': 'https://example.com',
            'operacion': 'venta',
            'tipo': 'departamento'
        }
        
        is_valid, errors = DataValidator.validate_property(prop)
        
        assert is_valid is True
    
    def test_validate_property_valid_price_clp(self):
        """Test validation accepts CLP price format."""
        prop = {
            'id': 'MLC-123',
            'titulo': 'Departamento',
            'precio': '$ 740.000',
            'ubicacion': 'Santiago',
            'url': 'https://example.com',
            'operacion': 'venta',
            'tipo': 'departamento'
        }
        
        is_valid, errors = DataValidator.validate_property(prop)
        
        assert is_valid is True
    
    def test_validate_property_valid_price_usd(self):
        """Test validation accepts USD price format."""
        prop = {
            'id': 'MLC-123',
            'titulo': 'Departamento',
            'precio': 'USD 1,200',
            'ubicacion': 'Santiago',
            'url': 'https://example.com',
            'operacion': 'venta',
            'tipo': 'departamento'
        }
        
        is_valid, errors = DataValidator.validate_property(prop)
        
        assert is_valid is True
    
    def test_validate_property_invalid_url(self):
        """Test validation fails with invalid URL."""
        prop = {
            'id': 'MLC-123',
            'titulo': 'Departamento',
            'precio': 'UF 3.055',
            'ubicacion': 'Santiago',
            'url': 'not-a-valid-url',
            'operacion': 'venta',
            'tipo': 'departamento'
        }
        
        is_valid, errors = DataValidator.validate_property(prop)
        
        assert is_valid is False
        assert any('Invalid URL' in e for e in errors)
    
    def test_validate_property_invalid_date(self):
        """Test validation fails with invalid date format."""
        prop = {
            'id': 'MLC-123',
            'titulo': 'Departamento',
            'precio': 'UF 3.055',
            'ubicacion': 'Santiago',
            'url': 'https://example.com',
            'operacion': 'venta',
            'tipo': 'departamento',
            'fecha_publicacion': 'invalid-date'
        }
        
        is_valid, errors = DataValidator.validate_property(prop)
        
        assert is_valid is False
        assert any('Invalid date format' in e for e in errors)
    
    def test_validate_property_valid_date(self):
        """Test validation accepts valid ISO 8601 date."""
        prop = {
            'id': 'MLC-123',
            'titulo': 'Departamento',
            'precio': 'UF 3.055',
            'ubicacion': 'Santiago',
            'url': 'https://example.com',
            'operacion': 'venta',
            'tipo': 'departamento',
            'fecha_publicacion': '2026-04-09'
        }
        
        is_valid, errors = DataValidator.validate_property(prop)
        
        assert is_valid is True
    
    def test_validate_property_invalid_coordinate(self):
        """Test validation fails with invalid coordinate."""
        prop = {
            'id': 'MLC-123',
            'titulo': 'Departamento',
            'precio': 'UF 3.055',
            'ubicacion': 'Santiago',
            'url': 'https://example.com',
            'operacion': 'venta',
            'tipo': 'departamento',
            'coordenadas': {'lat': 'invalid', 'lng': 'invalid'}
        }
        
        is_valid, errors = DataValidator.validate_property(prop)
        
        assert is_valid is False
        assert any('Invalid latitude' in e for e in errors)
    
    def test_validate_property_valid_coordinates(self):
        """Test validation accepts valid coordinates."""
        prop = {
            'id': 'MLC-123',
            'titulo': 'Departamento',
            'precio': 'UF 3.055',
            'ubicacion': 'Santiago',
            'url': 'https://example.com',
            'operacion': 'venta',
            'tipo': 'departamento',
            'coordenadas': {'lat': -33.4489, 'lng': -70.6693}
        }
        
        is_valid, errors = DataValidator.validate_property(prop)
        
        assert is_valid is True
    
    def test_validate_batch_all_valid(self):
        """Test batch validation with all valid properties."""
        properties = [
            {
                'id': 'MLC-1',
                'titulo': 'Prop 1',
                'precio': 'UF 3.000',
                'ubicacion': 'Santiago',
                'url': 'https://example.com/1',
                'operacion': 'venta',
                'tipo': 'departamento'
            },
            {
                'id': 'MLC-2',
                'titulo': 'Prop 2',
                'precio': '$ 500.000',
                'ubicacion': 'Santiago',
                'url': 'https://example.com/2',
                'operacion': 'venta',
                'tipo': 'casa'
            }
        ]
        
        valid_count, invalid_count, invalid_props = DataValidator.validate_batch(properties)
        
        assert valid_count == 2
        assert invalid_count == 0
        assert len(invalid_props) == 0
    
    def test_validate_batch_mixed(self):
        """Test batch validation with mixed valid/invalid properties."""
        properties = [
            {
                'id': 'MLC-1',
                'titulo': 'Prop 1',
                'precio': 'UF 3.000',
                'ubicacion': 'Santiago',
                'url': 'https://example.com/1',
                'operacion': 'venta',
                'tipo': 'departamento'
            },
            {
                'id': 'MLC-2',
                'titulo': 'Prop 2',
                'precio': 'INVALID'
                # Missing required fields
            }
        ]
        
        valid_count, invalid_count, invalid_props = DataValidator.validate_batch(properties)
        
        assert valid_count == 1
        assert invalid_count == 1
        assert len(invalid_props) == 1
        assert invalid_props[0]['property']['id'] == 'MLC-2'
    
    def test_normalize_property(self):
        """Test property normalization."""
        prop = {
            'id': 'MLC-123',
            'titulo': 'Departamento',
            'precio': 'UF 3.055',
            'ubicacion': 'Santiago',
            'url': 'https://example.com',
            'operacion': 'venta',
            'tipo': 'departamento',
            'fecha_publicacion': '2026-04-09'
        }
        
        normalized = DataValidator.normalize_property(prop)
        
        assert 'precio_original' in normalized
        assert normalized['precio_original'] == 'UF 3.055'
