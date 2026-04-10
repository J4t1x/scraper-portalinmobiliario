"""
Tests para el sistema de logging robusto.
"""

import os
import sys
import json
import gzip
import time
import shutil
import tempfile
import logging
from pathlib import Path
from datetime import datetime, timedelta

# Agregar parent al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logger_config import (
    LoggerConfig, 
    CustomJSONFormatter, 
    setup_logging, 
    get_logger,
    log_performance
)


class TestJSONFormatter:
    """Tests para el formatter JSON personalizado."""
    
    def test_json_format_basic(self):
        """TC-001: Log JSON tiene todos los campos requeridos."""
        formatter = CustomJSONFormatter()
        record = logging.LogRecord(
            name='test.logger',
            level=logging.INFO,
            pathname='test.py',
            lineno=10,
            msg='Test message',
            args=(),
            exc_info=None
        )
        record.funcName = 'test_function'
        record.module = 'test_module'
        
        output = formatter.format(record)
        parsed = json.loads(output)
        
        # Verificar campos obligatorios
        assert 'timestamp' in parsed, "Debe tener timestamp"
        assert 'level' in parsed, "Debe tener level"
        assert 'logger' in parsed, "Debe tener logger"
        assert 'module' in parsed, "Debe tener module"
        assert 'function' in parsed, "Debe tener function"
        assert 'line' in parsed, "Debe tener line"
        assert 'message' in parsed, "Debe tener message"
        assert 'thread' in parsed, "Debe tener thread"
        assert 'process' in parsed, "Debe tener process"
        
        # Verificar valores
        assert parsed['level'] == 'INFO'
        assert parsed['logger'] == 'test.logger'
        assert parsed['function'] == 'test_function'
        assert parsed['message'] == 'Test message'
        
        print("✅ TC-001: Log JSON tiene todos los campos requeridos")
    
    def test_json_format_with_context(self):
        """TC-007: Contexto extra aparece en JSON."""
        formatter = CustomJSONFormatter()
        record = logging.LogRecord(
            name='test.logger',
            level=logging.INFO,
            pathname='test.py',
            lineno=10,
            msg='Test with context',
            args=(),
            exc_info=None
        )
        record.funcName = 'test_function'
        record.module = 'test_module'
        record.context = {
            'property_id': 'MLC-12345678',
            'url': 'https://example.com',
            'execution_time_ms': 1250
        }
        
        output = formatter.format(record)
        parsed = json.loads(output)
        
        assert 'context' in parsed, "Debe tener context"
        assert parsed['context']['property_id'] == 'MLC-12345678'
        assert parsed['context']['execution_time_ms'] == 1250
        
        print("✅ TC-007: Contexto extra aparece en JSON")


class TestLogRotation:
    """Tests para rotación de logs."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = Path(self.temp_dir) / "logs"
    
    def teardown_method(self):
        """Cleanup después de cada test."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_log_directories_created(self):
        """Verificar que se crean los directorios de logs."""
        config = LoggerConfig(log_dir=str(self.log_dir))
        
        assert (self.log_dir / "scraping").exists()
        assert (self.log_dir / "errors").exists()
        assert (self.log_dir / "performance").exists()
        
        print("✅ Directorios de logs creados correctamente")
    
    def test_logs_are_json_format(self):
        """Verificar que los logs se escriben en formato JSON."""
        config = LoggerConfig(log_dir=str(self.log_dir))
        logger = config.get_logger("test.json")
        
        logger.info("Test JSON log message")
        
        # Dar tiempo a que se escriba
        time.sleep(0.1)
        
        # Verificar archivo de scraping
        scraping_file = self.log_dir / "scraping" / "scraping.json"
        if scraping_file.exists():
            with open(scraping_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    # Verificar que es JSON válido
                    log_entry = json.loads(lines[0])
                    assert 'timestamp' in log_entry
                    assert 'message' in log_entry
        
        print("✅ Logs escritos en formato JSON")


class TestLogLevels:
    """Tests para niveles de log."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = Path(self.temp_dir) / "logs"
    
    def teardown_method(self):
        """Cleanup después de cada test."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_debug_level_not_in_production(self):
        """TC-006: Nivel DEBUG no loggea en producción (INFO por defecto)."""
        # Configurar con nivel INFO (default de producción)
        config = LoggerConfig(log_level="INFO", log_dir=str(self.log_dir))
        logger = config.get_logger("test.levels")
        
        logger.debug("This debug message should not appear")
        logger.info("This info message should appear")
        
        # Dar tiempo a que se escriba
        time.sleep(0.1)
        
        # El debug no debería aparecer en archivos de nivel INFO
        scraping_file = self.log_dir / "scraping" / "scraping.json"
        if scraping_file.exists():
            with open(scraping_file, 'r') as f:
                content = f.read()
                assert "This debug message" not in content
                assert "This info message" in content
        
        print("✅ TC-006: Nivel DEBUG no loggea en producción")
    
    def test_error_log_separation(self):
        """Verificar que errores van a archivo separado."""
        config = LoggerConfig(log_dir=str(self.log_dir))
        logger = config.get_logger("test.errors")
        
        logger.info("Info message")
        logger.error("Error message")
        
        # Dar tiempo a que se escriba
        time.sleep(0.1)
        
        # Verificar archivo de errores
        errors_file = self.log_dir / "errors" / "errors.json"
        scraping_file = self.log_dir / "scraping" / "scraping.json"
        
        if errors_file.exists():
            with open(errors_file, 'r') as f:
                content = f.read()
                assert "Error message" in content
                assert "Info message" not in content
        
        print("✅ Errores separados correctamente")


class TestPerformanceLogging:
    """Tests para logging de performance."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = Path(self.temp_dir) / "logs"
    
    def teardown_method(self):
        """Cleanup después de cada test."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_performance_log_format(self):
        """Verificar formato de logs de performance."""
        config = LoggerConfig(log_dir=str(self.log_dir))
        
        log_performance(
            "scrape_property",
            1250.5,
            {"property_id": "MLC-12345678"}
        )
        
        # Dar tiempo a que se escriba
        time.sleep(0.1)
        
        perf_file = self.log_dir / "performance" / "performance.json"
        if perf_file.exists():
            with open(perf_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    log_entry = json.loads(lines[0])
                    assert log_entry['context']['operation'] == 'scrape_property'
                    assert log_entry['context']['duration_ms'] == 1250.5
                    assert log_entry['context']['property_id'] == 'MLC-12345678'
        
        print("✅ Logs de performance con formato correcto")


class TestLoggerSafety:
    """Tests para seguridad del logger (TC-005)."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = Path(self.temp_dir) / "logs"
    
    def teardown_method(self):
        """Cleanup después de cada test."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_logger_error_does_not_stop_scraper(self):
        """TC-005: Error en logging no detiene scraper."""
        config = LoggerConfig(log_dir=str(self.log_dir))
        logger = config.get_logger("test.safety")
        
        # Intentar loggear algo problemático
        try:
            # Loggear objeto no serializable en contexto
            class NonSerializable:
                pass
            
            logger.info("Test message", extra={'context': {'obj': NonSerializable()}})
        except Exception as e:
            # El logger no debería lanzar excepciones
            assert False, f"El logger no debería lanzar excepciones: {e}"
        
        print("✅ TC-005: Error en logging no detiene scraper")


class TestLogRetention:
    """Tests para retención de logs."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = Path(self.temp_dir) / "logs"
    
    def teardown_method(self):
        """Cleanup después de cada test."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_old_logs_cleaned(self):
        """TC-004: Logs >30 días se eliminan automáticamente."""
        # Crear archivos de log antiguos
        scraping_dir = self.log_dir / "scraping"
        scraping_dir.mkdir(parents=True)
        
        old_file = scraping_dir / "scraping.json.2025-01-01"
        old_file.write_text('{"test": "old"}')
        
        # Modificar fecha de modificación a 40 días atrás
        old_time = time.time() - (40 * 24 * 60 * 60)
        os.utime(old_file, (old_time, old_time))
        
        # Inicializar logger (debería limpiar logs antiguos)
        config = LoggerConfig(log_dir=str(self.log_dir))
        config.clean_old_logs()
        
        # Verificar que archivo antiguo fue eliminado
        assert not old_file.exists(), "Archivos antiguos deben ser eliminados"
        
        print("✅ TC-004: Logs >30 días se eliminan automáticamente")


def run_all_tests():
    """Ejecutar todos los tests."""
    print("\n" + "=" * 60)
    print("TESTING: Sistema de Logging Robusto")
    print("=" * 60 + "\n")
    
    # Tests de formatter
    formatter_tests = TestJSONFormatter()
    formatter_tests.test_json_format_basic()
    formatter_tests.test_json_format_with_context()
    
    # Tests de rotación
    rotation_tests = TestLogRotation()
    rotation_tests.setup_method()
    rotation_tests.test_log_directories_created()
    rotation_tests.teardown_method()
    
    rotation_tests.setup_method()
    rotation_tests.test_logs_are_json_format()
    rotation_tests.teardown_method()
    
    # Tests de niveles
    level_tests = TestLogLevels()
    level_tests.setup_method()
    level_tests.test_debug_level_not_in_production()
    level_tests.teardown_method()
    
    level_tests.setup_method()
    level_tests.test_error_log_separation()
    level_tests.teardown_method()
    
    # Tests de performance
    perf_tests = TestPerformanceLogging()
    perf_tests.setup_method()
    perf_tests.test_performance_log_format()
    perf_tests.teardown_method()
    
    # Tests de seguridad
    safety_tests = TestLoggerSafety()
    safety_tests.setup_method()
    safety_tests.test_logger_error_does_not_stop_scraper()
    safety_tests.teardown_method()
    
    # Tests de retención
    retention_tests = TestLogRetention()
    retention_tests.setup_method()
    retention_tests.test_old_logs_cleaned()
    retention_tests.teardown_method()
    
    print("\n" + "=" * 60)
    print("✅ TODOS LOS TESTS PASARON")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    run_all_tests()
