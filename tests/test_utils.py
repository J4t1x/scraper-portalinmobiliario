"""
Tests unitarios para el módulo utils
"""

import json
import os
import tempfile
import pytest
from utils import (
    load_properties_from_txt,
    load_properties_from_json,
    print_property_summary,
    get_price_statistics
)


class TestLoadPropertiesFromTxt:
    """Tests para carga de propiedades desde TXT"""
    
    def test_load_valid_txt(self, temp_dir):
        """TC-UTIL-001: Cargar TXT válido"""
        filepath = os.path.join(temp_dir, "test.txt")
        properties = [
            {'id': 'MLC-1', 'titulo': 'Prop 1', 'precio': 'UF 3.000'},
            {'id': 'MLC-2', 'titulo': 'Prop 2', 'precio': 'UF 4.000'}
        ]
        with open(filepath, 'w', encoding='utf-8') as f:
            for prop in properties:
                f.write(json.dumps(prop, ensure_ascii=False) + '\n')
        
        result = load_properties_from_txt(filepath)
        assert len(result) == 2
        assert result[0]['id'] == 'MLC-1'
        assert result[1]['titulo'] == 'Prop 2'
    
    def test_load_empty_txt(self, temp_dir):
        """TC-UTIL-002: Cargar TXT vacío"""
        filepath = os.path.join(temp_dir, "empty.txt")
        with open(filepath, 'w', encoding='utf-8') as f:
            pass
        
        result = load_properties_from_txt(filepath)
        assert result == []
    
    def test_load_txt_with_empty_lines(self, temp_dir):
        """TC-UTIL-003: Cargar TXT con líneas vacías"""
        filepath = os.path.join(temp_dir, "test.txt")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('{"id": "MLC-1"}\n\n\n{"id": "MLC-2"}\n')
        
        result = load_properties_from_txt(filepath)
        assert len(result) == 2
    
    def test_load_txt_invalid_json(self, temp_dir):
        """TC-UTIL-004: Cargar TXT con JSON inválido (salta línea)"""
        filepath = os.path.join(temp_dir, "test.txt")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('{"id": "MLC-1"}\n')
            f.write('invalid json line\n')
            f.write('{"id": "MLC-2"}\n')
        
        result = load_properties_from_txt(filepath)
        # Debe saltar la línea inválida y cargar las válidas
        assert len(result) == 2
    
    def test_load_nonexistent_txt(self):
        """TC-UTIL-005: Intentar cargar archivo inexistente"""
        with pytest.raises(Exception):
            load_properties_from_txt("/nonexistent/path/file.txt")


class TestLoadPropertiesFromJson:
    """Tests para carga de propiedades desde JSON"""
    
    def test_load_valid_json(self, temp_dir):
        """TC-UTIL-006: Cargar JSON válido"""
        filepath = os.path.join(temp_dir, "test.json")
        data = {
            'metadata': {'total': 2},
            'propiedades': [
                {'id': 'MLC-1', 'titulo': 'Prop 1'},
                {'id': 'MLC-2', 'titulo': 'Prop 2'}
            ]
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        
        result = load_properties_from_json(filepath)
        assert len(result) == 2
        assert result[0]['id'] == 'MLC-1'
    
    def test_load_json_empty_properties(self, temp_dir):
        """TC-UTIL-007: Cargar JSON con lista vacía"""
        filepath = os.path.join(temp_dir, "test.json")
        data = {
            'metadata': {'total': 0},
            'propiedades': []
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        
        result = load_properties_from_json(filepath)
        assert result == []
    
    def test_load_json_no_propiedades_key(self, temp_dir):
        """TC-UTIL-008: Cargar JSON sin key 'propiedades'"""
        filepath = os.path.join(temp_dir, "test.json")
        data = {'metadata': {'total': 0}}
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        
        result = load_properties_from_json(filepath)
        assert result == []
    
    def test_load_nonexistent_json(self):
        """TC-UTIL-009: Intentar cargar JSON inexistente"""
        with pytest.raises(Exception):
            load_properties_from_json("/nonexistent/path/file.json")
    
    def test_load_invalid_json(self, temp_dir):
        """TC-UTIL-010: Intentar cargar JSON mal formado"""
        filepath = os.path.join(temp_dir, "test.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('not valid json')
        
        with pytest.raises(Exception):
            load_properties_from_json(filepath)


class TestPrintPropertySummary:
    """Tests para impresión de resumen"""
    
    def test_print_empty_properties(self, capsys):
        """TC-UTIL-011: Imprimir lista vacía"""
        print_property_summary([])
        captured = capsys.readouterr()
        assert "No hay propiedades" in captured.out
    
    def test_print_properties(self, capsys):
        """TC-UTIL-012: Imprimir propiedades"""
        properties = [
            {'id': 'MLC-1', 'titulo': 'Propiedad 1', 'precio': 'UF 3.000', 'ubicacion': 'Santiago'},
            {'id': 'MLC-2', 'titulo': 'Propiedad 2', 'precio': 'UF 4.000', 'ubicacion': 'Las Condes'}
        ]
        print_property_summary(properties)
        captured = capsys.readouterr()
        assert "RESUMEN DE PROPIEDADES" in captured.out
        assert "Propiedad 1" in captured.out
        assert "Propiedad 2" in captured.out
    
    def test_print_more_than_10(self, capsys):
        """TC-UTIL-013: Imprimir más de 10 propiedades (trunca)"""
        properties = [
            {'id': f'MLC-{i}', 'titulo': f'Propiedad {i}', 'precio': f'UF {i}.000', 'ubicacion': 'Santiago'}
            for i in range(15)
        ]
        print_property_summary(properties)
        captured = capsys.readouterr()
        assert "y 5 propiedades más" in captured.out


class TestGetPriceStatistics:
    """Tests para estadísticas de precios"""
    
    def test_empty_properties(self):
        """TC-UTIL-014: Estadísticas de lista vacía"""
        result = get_price_statistics([])
        assert result['total'] == 0
        assert result['min'] == 0
        assert result['max'] == 0
        assert result['avg'] == 0
    
    def test_single_property(self):
        """TC-UTIL-015: Estadísticas de una propiedad"""
        properties = [{'precio': '100000000'}]
        result = get_price_statistics(properties)
        assert result['total'] == 1
        assert result['min'] == 100000000.0
        assert result['max'] == 100000000.0
        assert result['avg'] == 100000000.0
    
    def test_multiple_properties(self):
        """TC-UTIL-016: Estadísticas de múltiples propiedades"""
        properties = [
            {'precio': '100000000'},
            {'precio': '200000000'},
            {'precio': '300000000'}
        ]
        result = get_price_statistics(properties)
        assert result['total'] == 3
        assert result['min'] == 100000000.0
        assert result['max'] == 300000000.0
        assert result['avg'] == 200000000.0
    
    def test_properties_with_dots(self):
        """TC-UTIL-017: Precios con separadores de miles"""
        properties = [
            {'precio': '100.000.000'},
            {'precio': '200.000.000'}
        ]
        result = get_price_statistics(properties)
        assert result['total'] == 2
        assert result['min'] == 100000000.0
    
    def test_properties_invalid_price(self):
        """TC-UTIL-018: Propiedades con precio inválido"""
        properties = [
            {'precio': '100000000'},
            {'precio': 'INVALIDO'},
            {'precio': '200000000'}
        ]
        result = get_price_statistics(properties)
        assert result['total'] == 2  # Solo 2 válidos
    
    def test_properties_no_price(self):
        """TC-UTIL-019: Propiedades sin precio"""
        properties = [
            {'id': 'MLC-1'},
            {'titulo': 'Sin precio'}
        ]
        result = get_price_statistics(properties)
        assert result['total'] == 0
