"""
Tests unitarios para el módulo config
"""

import os
import pytest
from config import Config


class TestConfigDefaults:
    """Tests para valores por defecto de configuración"""
    
    def test_base_url(self):
        """TC-CONF-001: BASE_URL es correcto"""
        assert Config.BASE_URL == "https://www.portalinmobiliario.com"
    
    def test_default_delay(self, monkeypatch):
        """TC-CONF-002: DELAY_BETWEEN_REQUESTS por defecto"""
        monkeypatch.delenv("DELAY_BETWEEN_REQUESTS", raising=False)
        # Recargar módulo para obtener valor por defecto
        import importlib
        import config
        importlib.reload(config)
        assert config.Config.DELAY_BETWEEN_REQUESTS == 2.0
    
    def test_default_max_retries(self, monkeypatch):
        """TC-CONF-003: MAX_RETRIES por defecto"""
        monkeypatch.delenv("MAX_RETRIES", raising=False)
        import importlib
        import config
        importlib.reload(config)
        assert config.Config.MAX_RETRIES == 3
    
    def test_default_timeout(self, monkeypatch):
        """TC-CONF-004: TIMEOUT por defecto"""
        monkeypatch.delenv("TIMEOUT", raising=False)
        import importlib
        import config
        importlib.reload(config)
        assert config.Config.TIMEOUT == 30
    
    def test_default_user_agent(self, monkeypatch):
        """TC-CONF-005: USER_AGENT por defecto contiene Mozilla"""
        monkeypatch.delenv("USER_AGENT", raising=False)
        import importlib
        import config
        importlib.reload(config)
        assert "Mozilla" in config.Config.USER_AGENT
    
    def test_items_per_page(self):
        """TC-CONF-006: ITEMS_PER_PAGE es 50"""
        assert Config.ITEMS_PER_PAGE == 50
    
    def test_output_dir(self):
        """TC-CONF-007: OUTPUT_DIR es 'output'"""
        assert Config.OUTPUT_DIR == "output"


class TestConfigEnvVars:
    """Tests para configuración desde variables de entorno"""
    
    def test_delay_from_env(self, monkeypatch):
        """TC-CONF-008: DELAY_BETWEEN_REQUESTS desde env"""
        monkeypatch.setenv("DELAY_BETWEEN_REQUESTS", "5")
        import importlib
        import config
        importlib.reload(config)
        assert config.Config.DELAY_BETWEEN_REQUESTS == 5.0
    
    def test_max_retries_from_env(self, monkeypatch):
        """TC-CONF-009: MAX_RETRIES desde env"""
        monkeypatch.setenv("MAX_RETRIES", "5")
        import importlib
        import config
        importlib.reload(config)
        assert config.Config.MAX_RETRIES == 5
    
    def test_timeout_from_env(self, monkeypatch):
        """TC-CONF-010: TIMEOUT desde env"""
        monkeypatch.setenv("TIMEOUT", "60")
        import importlib
        import config
        importlib.reload(config)
        assert config.Config.TIMEOUT == 60
    
    def test_user_agent_from_env(self, monkeypatch):
        """TC-CONF-011: USER_AGENT desde env"""
        monkeypatch.setenv("USER_AGENT", "CustomAgent/1.0")
        import importlib
        import config
        importlib.reload(config)
        assert config.Config.USER_AGENT == "CustomAgent/1.0"


class TestConfigOperations:
    """Tests para operaciones y tipos de propiedad"""
    
    def test_operaciones_list(self):
        """TC-CONF-012: Lista de operaciones es correcta"""
        expected = ["venta", "arriendo", "arriendo-de-temporada"]
        assert Config.OPERACIONES == expected
    
    def test_tipos_propiedad_list(self):
        """TC-CONF-013: Lista de tipos de propiedad es correcta"""
        expected = [
            "departamento",
            "casa",
            "oficina",
            "terreno",
            "local-comercial",
            "bodega",
            "estacionamiento",
            "parcela"
        ]
        assert Config.TIPOS_PROPIEDAD == expected
    
    def test_venta_in_operaciones(self):
        """TC-CONF-014: 'venta' está en operaciones"""
        assert "venta" in Config.OPERACIONES
    
    def test_departamento_in_tipos(self):
        """TC-CONF-015: 'departamento' está en tipos"""
        assert "departamento" in Config.TIPOS_PROPIEDAD


class TestConfigTypeConversion:
    """Tests para conversión de tipos en configuración"""
    
    def test_delay_is_float(self, monkeypatch):
        """TC-CONF-016: DELAY es convertido a float"""
        monkeypatch.setenv("DELAY_BETWEEN_REQUESTS", "1.5")
        import importlib
        import config
        importlib.reload(config)
        assert isinstance(config.Config.DELAY_BETWEEN_REQUESTS, float)
        assert config.Config.DELAY_BETWEEN_REQUESTS == 1.5
    
    def test_max_retries_is_int(self, monkeypatch):
        """TC-CONF-017: MAX_RETRIES es convertido a int"""
        monkeypatch.setenv("MAX_RETRIES", "10")
        import importlib
        import config
        importlib.reload(config)
        assert isinstance(config.Config.MAX_RETRIES, int)
        assert config.Config.MAX_RETRIES == 10
    
    def test_timeout_is_int(self, monkeypatch):
        """TC-CONF-018: TIMEOUT es convertido a int"""
        monkeypatch.setenv("TIMEOUT", "45")
        import importlib
        import config
        importlib.reload(config)
        assert isinstance(config.Config.TIMEOUT, int)
        assert config.Config.TIMEOUT == 45
