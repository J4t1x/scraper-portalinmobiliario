"""
Tests para el módulo de exportación de datos
"""

import os
import sys
import json
import csv
import tempfile
import shutil
from pathlib import Path

# Agregar directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from exporter import DataExporter
from config import Config


class TestDataExporter:
    """Tests para DataExporter"""
    
    def setup_method(self):
        """Setup antes de cada test"""
        self.exporter = DataExporter()
        # Crear directorio temporal para tests
        self.test_output_dir = tempfile.mkdtemp()
        # Backup del output dir original
        self.original_output_dir = Config.OUTPUT_DIR
        Config.OUTPUT_DIR = self.test_output_dir
    
    def teardown_method(self):
        """Cleanup después de cada test"""
        # Restaurar output dir original
        Config.OUTPUT_DIR = self.original_output_dir
        # Eliminar directorio temporal
        shutil.rmtree(self.test_output_dir, ignore_errors=True)
    
    def test_flatten_property_basic(self):
        """Test de aplanado de propiedad básica"""
        prop = {
            'id': 'TEST-001',
            'titulo': 'Departamento Test',
            'precio': '$100.000.000',
            'precio_uf': 2800.5,
            'ubicacion': 'Las Condes',
            'metros_cuadrados': 80,
            'dormitorios': 3,
            'banos': 2
        }
        
        flat = self.exporter.flatten_property(prop)
        
        assert flat['id'] == 'TEST-001'
        assert flat['titulo'] == 'Departamento Test'
        assert flat['precio_uf'] == '2800.5'
        assert flat['metros_cuadrados'] == '80'
    
    def test_flatten_property_with_details(self):
        """Test de aplanado de propiedad con datos de detalle"""
        prop = {
            'id': 'TEST-002',
            'titulo': 'Casa con Detalle',
            'precio': '$200.000.000',
            'descripcion': 'Hermosa casa con jardín',
            'caracteristicas': {
                'orientacion': 'Norte',
                'año_construccion': 2010,
                'estacionamientos': 2
            },
            'publicador': {
                'nombre': 'Inmobiliaria Test',
                'telefono': '+56912345678'
            },
            'coordenadas': {
                'lat': -33.4567,
                'lng': -70.6789
            },
            'imagenes': ['http://img1.jpg', 'http://img2.jpg'],
            'fecha_publicacion': '2026-04-01'
        }
        
        flat = self.exporter.flatten_property(prop)
        
        # Verificar campos básicos
        assert flat['id'] == 'TEST-002'
        assert flat['descripcion'] == 'Hermosa casa con jardín'
        
        # Verificar campos anidados aplanados
        assert flat['caracteristicas_orientacion'] == 'Norte'
        assert flat['caracteristicas_año_construccion'] == '2010'
        assert flat['caracteristicas_estacionamientos'] == '2'
        assert flat['publicador_nombre'] == 'Inmobiliaria Test'
        assert flat['publicador_telefono'] == '+56912345678'
        assert flat['coordenadas_lat'] == '-33.4567'
        assert flat['coordenadas_lng'] == '-70.6789'
        
        # Verificar que listas se convierten a string con pipe
        assert flat['imagenes'] == 'http://img1.jpg | http://img2.jpg'
    
    def test_flatten_property_empty_values(self):
        """Test de aplanado con valores vacíos o None"""
        prop = {
            'id': 'TEST-003',
            'titulo': None,
            'descripcion': None,
            'caracteristicas': {},
            'imagenes': [],
            'publicador': {'nombre': None}
        }
        
        flat = self.exporter.flatten_property(prop)
        
        assert flat['titulo'] == ''
        assert flat['descripcion'] == ''
        assert flat['imagenes'] == ''
        assert flat['publicador_nombre'] == ''
    
    def test_export_to_json_with_details(self):
        """Test de exportación JSON con datos de detalle"""
        properties = [
            {
                'id': 'TEST-001',
                'titulo': 'Propiedad 1',
                'descripcion': 'Descripción completa 1',
                'caracteristicas': {'orientacion': 'Sur'},
                'coordenadas': {'lat': -33.1, 'lng': -70.1}
            },
            {
                'id': 'TEST-002',
                'titulo': 'Propiedad 2',
                'descripcion': 'Descripción completa 2',
                'caracteristicas': {'orientacion': 'Norte'},
                'publicador': {'nombre': 'Agente Test'}
            }
        ]
        
        filepath = self.exporter.export_to_json(properties, 'venta', 'departamento')
        
        # Verificar que el archivo existe
        assert os.path.exists(filepath)
        assert filepath.endswith('.json')
        
        # Leer y verificar contenido
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data['metadata']['total'] == 2
        assert len(data['propiedades']) == 2
        
        # Verificar que los detalles están presentes
        prop1 = data['propiedades'][0]
        assert prop1['descripcion'] == 'Descripción completa 1'
        assert prop1['caracteristicas']['orientacion'] == 'Sur'
        assert prop1['coordenadas']['lat'] == -33.1
        
        prop2 = data['propiedades'][1]
        assert prop2['publicador']['nombre'] == 'Agente Test'
    
    def test_export_to_csv_with_details(self):
        """Test de exportación CSV con datos de detalle"""
        properties = [
            {
                'id': 'TEST-001',
                'titulo': 'Propiedad CSV 1',
                'precio': '$100.000.000',
                'descripcion': 'Descripción CSV',
                'caracteristicas': {
                    'orientacion': 'Norte',
                    'año_construccion': 2015
                },
                'publicador': {
                    'nombre': 'Inmobiliaria CSV'
                },
                'imagenes': ['img1.jpg', 'img2.jpg']
            }
        ]
        
        filepath = self.exporter.export_to_csv(properties, 'venta', 'casa')
        
        # Verificar que el archivo existe
        assert os.path.exists(filepath)
        assert filepath.endswith('.csv')
        
        # Leer y verificar contenido CSV
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 1
        row = rows[0]
        
        # Verificar campos de detalle aplanados
        assert row['descripcion'] == 'Descripción CSV'
        assert row['caracteristicas_orientacion'] == 'Norte'
        assert row['caracteristicas_año_construccion'] == '2015'
        assert row['publicador_nombre'] == 'Inmobiliaria CSV'
        assert row['imagenes'] == 'img1.jpg | img2.jpg'
    
    def test_export_to_txt_with_details(self):
        """Test de exportación TXT con datos de detalle"""
        properties = [
            {
                'id': 'TEST-001',
                'titulo': 'Casa Test TXT',
                'precio': '$150.000.000',
                'ubicacion': 'Providencia',
                'descripcion': 'Hermosa casa en Providencia con excelente ubicación',
                'caracteristicas': {
                    'orientacion': 'Oriente',
                    'año_construccion': 2018
                },
                'publicador': {
                    'nombre': 'Juan Pérez',
                    'telefono': '+56987654321'
                },
                'coordenadas': {
                    'lat': -33.4321,
                    'lng': -70.6234
                },
                'fecha_publicacion': '2026-04-05'
            }
        ]
        
        filepath = self.exporter.export_to_txt(properties, 'venta', 'casa')
        
        # Verificar que el archivo existe
        assert os.path.exists(filepath)
        assert filepath.endswith('.txt')
        
        # Leer y verificar contenido
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar estructura del TXT
        assert 'PROPIEDADES - VENTA - CASA' in content
        assert 'PROPIEDAD #1' in content
        assert 'INFORMACIÓN BÁSICA' in content
        assert 'DETALLES DE LA PROPIEDAD' in content
        
        # Verificar datos específicos
        assert 'Casa Test TXT' in content
        assert '$150.000.000' in content
        assert 'Providencia' in content
        assert 'Hermosa casa en Providencia' in content
        assert 'Oriente' in content
        assert 'Juan Pérez' in content
        assert '-33.4321' in content or '-33.432' in content
        assert '2026-04-05' in content
    
    def test_export_to_txt_without_details(self):
        """Test de exportación TXT sin datos de detalle"""
        properties = [
            {
                'id': 'TEST-001',
                'titulo': 'Propiedad Sin Detalle',
                'precio': '$100.000.000'
            }
        ]
        
        filepath = self.exporter.export_to_txt(properties, 'arriendo', 'departamento')
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar que no aparece la sección de detalles
        assert 'Propiedad Sin Detalle' in content
        # No debe tener sección de detalles ya que no hay datos
        assert 'FIN DEL LISTADO' in content
    
    def test_export_empty_properties(self):
        """Test de exportación con lista vacía"""
        properties = []
        
        # JSON debería manejar lista vacía
        filepath_json = self.exporter.export_to_json(properties, 'venta', 'casa')
        assert os.path.exists(filepath_json)
        
        with open(filepath_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert data['metadata']['total'] == 0
        assert data['propiedades'] == []
        
        # CSV retorna filepath pero no crea archivo si está vacío (según implementación actual)
        filepath_csv = self.exporter.export_to_csv(properties, 'venta', 'casa')
        assert filepath_csv is not None  # Retorna path aunque no cree archivo


def run_tests():
    """Ejecutar todos los tests"""
    import traceback
    
    test_class = TestDataExporter()
    methods = [m for m in dir(test_class) if m.startswith('test_')]
    
    passed = 0
    failed = 0
    
    print("=" * 60)
    print("TESTS DE EXPORTER.PY")
    print("=" * 60)
    
    for method_name in methods:
        try:
            test_class.setup_method()
            method = getattr(test_class, method_name)
            method()
            test_class.teardown_method()
            print(f"✅ {method_name}: PASSED")
            passed += 1
        except Exception as e:
            print(f"❌ {method_name}: FAILED")
            print(f"   Error: {e}")
            traceback.print_exc()
            failed += 1
    
    print("=" * 60)
    print(f"Resultados: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
