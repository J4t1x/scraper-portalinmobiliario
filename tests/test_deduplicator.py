#!/usr/bin/env python3
"""
Tests unitarios para el módulo deduplicator
"""

import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path
from typing import Dict, List

# Añadir directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from deduplicator import Deduplicator, DeduplicationRegistry


class TestDeduplicationRegistry(unittest.TestCase):
    """Tests para DeduplicationRegistry dataclass"""
    
    def test_default_creation(self):
        """TC-REG-001: Creación con valores por defecto"""
        registry = DeduplicationRegistry()
        self.assertEqual(registry.ids, set())
        self.assertEqual(registry.first_seen, {})
        self.assertEqual(registry.last_seen, {})
        self.assertEqual(registry.execution_count, 0)
    
    def test_to_dict(self):
        """TC-REG-002: Serialización a diccionario"""
        registry = DeduplicationRegistry()
        registry.ids = {"MLC-123", "MLC-456"}
        registry.first_seen = {"MLC-123": "2026-01-01T00:00:00"}
        registry.execution_count = 5
        
        data = registry.to_dict()
        
        self.assertEqual(set(data["ids"]), {"MLC-123", "MLC-456"})
        self.assertEqual(data["first_seen"], {"MLC-123": "2026-01-01T00:00:00"})
        self.assertEqual(data["execution_count"], 5)
        self.assertEqual(data["total_unique"], 2)
    
    def test_from_dict(self):
        """TC-REG-003: Deserialización desde diccionario"""
        data = {
            "ids": ["MLC-123", "MLC-456"],
            "first_seen": {"MLC-123": "2026-01-01T00:00:00"},
            "last_seen": {"MLC-123": "2026-01-02T00:00:00"},
            "execution_count": 3,
            "total_unique": 2
        }
        
        registry = DeduplicationRegistry.from_dict(data)
        
        self.assertEqual(registry.ids, {"MLC-123", "MLC-456"})
        self.assertEqual(registry.first_seen["MLC-123"], "2026-01-01T00:00:00")
        self.assertEqual(registry.execution_count, 3)


class TestDeduplicator(unittest.TestCase):
    """Tests para Deduplicator class"""
    
    def setUp(self):
        """Setup para cada test - crear directorio temporal"""
        self.temp_dir = tempfile.mkdtemp()
        self.registry_path = os.path.join(self.temp_dir, "test_registry.json")
        self.deduplicator = Deduplicator(self.registry_path)
    
    def tearDown(self):
        """Cleanup después de cada test"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init_creates_new_registry(self):
        """TC-001: Inicialización crea nuevo registro"""
        self.assertEqual(len(self.deduplicator.registry.ids), 0)
        self.assertFalse(os.path.exists(self.registry_path))
    
    def test_is_duplicate_new_id(self):
        """TC-002: ID nuevo no está duplicado"""
        result = self.deduplicator.is_duplicate("MLC-NEW123")
        self.assertFalse(result)
    
    def test_is_duplicate_existing_id(self):
        """TC-003: ID existente está duplicado"""
        self.deduplicator.registry.ids.add("MLC-EXISTING")
        result = self.deduplicator.is_duplicate("MLC-EXISTING")
        self.assertTrue(result)
    
    def test_add_to_registry(self):
        """TC-004: Agregar ID al registro"""
        self.deduplicator.add_to_registry("MLC-TEST123")
        
        self.assertIn("MLC-TEST123", self.deduplicator.registry.ids)
        self.assertIn("MLC-TEST123", self.deduplicator.registry.first_seen)
        self.assertIn("MLC-TEST123", self.deduplicator.registry.last_seen)
    
    def test_add_duplicate_updates_last_seen(self):
        """TC-005: Agregar duplicado actualiza last_seen"""
        self.deduplicator.add_to_registry("MLC-DUP")
        first_seen = self.deduplicator.registry.first_seen["MLC-DUP"]
        
        time.sleep(0.01)  # Pequeña pausa para diferenciar timestamps
        self.deduplicator.add_to_registry("MLC-DUP")
        last_seen = self.deduplicator.registry.last_seen["MLC-DUP"]
        
        self.assertEqual(first_seen, self.deduplicator.registry.first_seen["MLC-DUP"])
        self.assertNotEqual(first_seen, last_seen)
    
    def test_save_and_load_registry(self):
        """TC-006: Persistencia guarda y carga correctamente"""
        # Agregar datos
        self.deduplicator.add_to_registry("MLC-1")
        self.deduplicator.add_to_registry("MLC-2")
        self.deduplicator.registry.execution_count = 3
        
        # Guardar
        self.deduplicator.save_registry()
        self.assertTrue(os.path.exists(self.registry_path))
        
        # Crear nuevo deduplicador y cargar
        new_deduplicator = Deduplicator(self.registry_path)
        
        self.assertEqual(new_deduplicator.registry.ids, {"MLC-1", "MLC-2"})
        self.assertEqual(new_deduplicator.registry.execution_count, 3)
    
    def test_mark_property_with_id(self):
        """TC-007: Marcar propiedad con ID directo"""
        self.deduplicator.registry.ids.add("MLC-PROP123")
        
        prop = {"id": "MLC-PROP123", "titulo": "Casa Test"}
        marked = self.deduplicator.mark_property(prop)
        
        self.assertTrue(marked["is_duplicate"])
    
    def test_mark_property_with_url(self):
        """TC-008: Extraer ID desde URL"""
        self.deduplicator.registry.ids.add("MLC-99988877")
        
        prop = {
            "url": "https://www.portalinmobiliario.com/propiedades/MLC-99988877-casa-en-venta.html",
            "titulo": "Casa URL Test"
        }
        marked = self.deduplicator.mark_property(prop)
        
        self.assertTrue(marked["is_duplicate"])
    
    def test_mark_property_new(self):
        """TC-009: Marcar propiedad nueva (no duplicada)"""
        prop = {"id": "MLC-NEW", "titulo": "Nueva Propiedad"}
        marked = self.deduplicator.mark_property(prop)
        
        self.assertFalse(marked["is_duplicate"])
    
    def test_mark_property_no_id(self):
        """TC-010: Marcar propiedad sin ID"""
        prop = {"titulo": "Sin ID", "precio": "1000"}
        marked = self.deduplicator.mark_property(prop)
        
        # No debe marcar como duplicado si no tiene ID
        self.assertFalse(marked["is_duplicate"])
    
    def test_process_properties(self):
        """TC-011: Procesar lista de propiedades"""
        # Pre-poblar registro
        self.deduplicator.add_to_registry("MLC-OLD")
        
        properties = [
            {"id": "MLC-OLD", "titulo": "Propiedad Vieja"},
            {"id": "MLC-NEW", "titulo": "Propiedad Nueva"},
            {"id": "MLC-OLD", "titulo": "Otra Vieja"},  # Duplicada
        ]
        
        processed = self.deduplicator.process_properties(properties)
        
        self.assertEqual(len(processed), 3)
        self.assertTrue(processed[0]["is_duplicate"])
        self.assertFalse(processed[1]["is_duplicate"])
        self.assertTrue(processed[2]["is_duplicate"])
    
    def test_process_properties_adds_to_registry(self):
        """TC-012: Procesar agrega IDs nuevos al registro"""
        properties = [
            {"id": "MLC-A", "titulo": "A"},
            {"id": "MLC-B", "titulo": "B"},
        ]
        
        self.deduplicator.process_properties(properties)
        
        self.assertIn("MLC-A", self.deduplicator.registry.ids)
        self.assertIn("MLC-B", self.deduplicator.registry.ids)
    
    def test_filter_duplicates(self):
        """TC-013: Filtrar duplicados"""
        properties = [
            {"id": "MLC-1", "titulo": "A", "is_duplicate": False},
            {"id": "MLC-2", "titulo": "B", "is_duplicate": True},
            {"id": "MLC-3", "titulo": "C", "is_duplicate": False},
        ]
        
        filtered = self.deduplicator.filter_duplicates(properties)
        
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0]["id"], "MLC-1")
        self.assertEqual(filtered[1]["id"], "MLC-3")
    
    def test_reset_registry(self):
        """TC-014: Reset limpia el registro"""
        self.deduplicator.add_to_registry("MLC-1")
        self.deduplicator.save_registry()
        
        self.deduplicator.reset_registry()
        
        self.assertEqual(len(self.deduplicator.registry.ids), 0)
        # Archivo original debe haberse movido a .reset
        reset_file = self.registry_path + ".reset"
        self.assertTrue(os.path.exists(reset_file))
    
    def test_get_stats(self):
        """TC-015: Estadísticas del registro"""
        self.deduplicator.add_to_registry("MLC-1")
        self.deduplicator.add_to_registry("MLC-2")
        self.deduplicator.registry.execution_count = 5
        
        stats = self.deduplicator.get_stats()
        
        self.assertEqual(stats["total_ids"], 2)
        self.assertEqual(stats["execution_count"], 5)
        self.assertEqual(stats["registry_file"], self.registry_path)
    
    def test_handle_corrupt_registry(self):
        """TC-016: Manejo de archivo corrupto"""
        # Crear archivo JSON inválido
        with open(self.registry_path, 'w') as f:
            f.write("{invalid json}")
        
        # Inicializar debe manejarlo gracefully
        dedup = Deduplicator(self.registry_path)
        
        self.assertEqual(len(dedup.registry.ids), 0)
        # Backup debe existir
        self.assertTrue(os.path.exists(self.registry_path + ".corrupt"))
    
    def test_extract_property_id_direct(self):
        """TC-017: Extraer ID directo"""
        prop = {"id": "MLC-123", "titulo": "Test"}
        result = self.deduplicator._extract_property_id(prop)
        self.assertEqual(result, "MLC-123")
    
    def test_extract_property_id_from_url(self):
        """TC-018: Extraer ID desde URL"""
        prop = {"url": "https://portalinmobiliario.com/MLC-98765432-propiedad.html"}
        result = self.deduplicator._extract_property_id(prop)
        self.assertEqual(result, "MLC-98765432")
    
    def test_extract_property_id_none(self):
        """TC-019: Extraer ID cuando no hay"""
        prop = {"titulo": "Sin ID", "precio": "100"}
        result = self.deduplicator._extract_property_id(prop)
        self.assertIsNone(result)


class TestDeduplicatorPerformance(unittest.TestCase):
    """Tests de performance para deduplicator"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.registry_path = os.path.join(self.temp_dir, "perf_registry.json")
        self.deduplicator = Deduplicator(self.registry_path)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_performance_10k_ids(self):
        """TC-PERF-001: Performance con 10,000 IDs <500ms"""
        # Pre-poblar con 10,000 IDs
        for i in range(10000):
            self.deduplicator.registry.ids.add(f"MLC-{i:08d}")
        
        # Medir tiempo de lookup
        start_time = time.time()
        
        # Realizar 1000 lookups aleatorios
        import random
        for _ in range(1000):
            test_id = f"MLC-{random.randint(0, 99999):08d}"
            self.deduplicator.is_duplicate(test_id)
        
        elapsed = time.time() - start_time
        
        # Debe ser mucho menos de 500ms para 1000 lookups
        self.assertLess(elapsed, 0.5, f"Performance: {elapsed:.3f}s para 1000 lookups")
    
    def test_o1_lookup_time(self):
        """TC-PERF-002: Verificar O(1) lookup behavior"""
        # Agregar IDs
        for i in range(1000):
            self.deduplicator.registry.ids.add(f"MLC-{i:06d}")
        
        # Medir lookups
        times = []
        for i in range(100):
            start = time.time()
            self.deduplicator.is_duplicate(f"MLC-{i:06d}")
            times.append(time.time() - start)
        
        # Todos los lookups deben ser rápidos (O(1))
        avg_time = sum(times) / len(times)
        self.assertLess(avg_time, 0.0001, f"Lookup promedio: {avg_time:.6f}s")


class TestIntegration(unittest.TestCase):
    """Tests de integración"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.registry_path = os.path.join(self.temp_dir, "integration.json")
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_full_workflow(self):
        """TC-INT-001: Workflow completo"""
        # Simular dos ejecuciones
        
        # Ejecución 1: 3 propiedades nuevas
        dedup1 = Deduplicator(self.registry_path)
        props1 = [
            {"id": "MLC-A", "titulo": "Casa A"},
            {"id": "MLC-B", "titulo": "Casa B"},
            {"id": "MLC-C", "titulo": "Casa C"},
        ]
        processed1 = dedup1.process_properties(props1)
        dedup1.save_registry()
        
        self.assertEqual(sum(1 for p in processed1 if not p["is_duplicate"]), 3)
        
        # Ejecución 2: 2 nuevas + 1 duplicada
        dedup2 = Deduplicator(self.registry_path)
        props2 = [
            {"id": "MLC-A", "titulo": "Casa A (dup)"},  # Duplicada
            {"id": "MLC-D", "titulo": "Casa D"},       # Nueva
            {"id": "MLC-E", "titulo": "Casa E"},       # Nueva
        ]
        processed2 = dedup2.process_properties(props2)
        
        self.assertEqual(sum(1 for p in processed2 if p["is_duplicate"]), 1)
        self.assertEqual(sum(1 for p in processed2 if not p["is_duplicate"]), 2)
        
        # Verificar estadísticas
        stats = dedup2.get_stats()
        self.assertEqual(stats["total_ids"], 5)  # A, B, C, D, E
        self.assertEqual(stats["execution_count"], 2)


if __name__ == "__main__":
    # Configurar logging para tests
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # Ejecutar tests
    unittest.main(verbosity=2)
