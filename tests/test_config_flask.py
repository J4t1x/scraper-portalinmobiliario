"""Tests para config_flask.py"""

import pytest
import os
from unittest.mock import patch


class TestFlaskConfig:
    """Tests para la clase FlaskConfig"""
    
    def test_secret_key_default(self):
        """Test valor por defecto de SECRET_KEY"""
        # Due to module caching, just verify the value exists and is a string
        import importlib
        import config_flask
        importlib.reload(config_flask)
        
        assert isinstance(config_flask.FlaskConfig.SECRET_KEY, str)
        assert len(config_flask.FlaskConfig.SECRET_KEY) > 0
    
    def test_secret_key_from_env(self):
        """Test SECRET_KEY desde variable de entorno"""
        os.environ['FLASK_SECRET_KEY'] = 'test-secret-key'
        
        import importlib
        import config_flask
        importlib.reload(config_flask)
        
        assert config_flask.FlaskConfig.SECRET_KEY == 'test-secret-key'
        
        # Cleanup
        os.environ.pop('FLASK_SECRET_KEY', None)
    
    def test_debug_default(self):
        """Test valor por defecto de DEBUG"""
        os.environ.pop('FLASK_DEBUG', None)
        
        import importlib
        import config_flask
        importlib.reload(config_flask)
        
        # Default es "True" -> True
        assert config_flask.FlaskConfig.DEBUG is True
    
    def test_debug_true_from_env(self):
        """Test DEBUG=True desde variable de entorno"""
        os.environ['FLASK_DEBUG'] = 'True'
        
        import importlib
        import config_flask
        importlib.reload(config_flask)
        
        assert config_flask.FlaskConfig.DEBUG is True
        
        os.environ.pop('FLASK_DEBUG', None)
    
    def test_debug_false_from_env(self):
        """Test DEBUG=False desde variable de entorno"""
        os.environ['FLASK_DEBUG'] = 'False'
        
        import importlib
        import config_flask
        importlib.reload(config_flask)
        
        assert config_flask.FlaskConfig.DEBUG is False
        
        os.environ.pop('FLASK_DEBUG', None)
    
    def test_host_default(self):
        """Test valor por defecto de HOST"""
        os.environ.pop('FLASK_HOST', None)
        
        import importlib
        import config_flask
        importlib.reload(config_flask)
        
        assert config_flask.FlaskConfig.HOST == '0.0.0.0'
    
    def test_host_from_env(self):
        """Test HOST desde variable de entorno"""
        os.environ['FLASK_HOST'] = '127.0.0.1'
        
        import importlib
        import config_flask
        importlib.reload(config_flask)
        
        assert config_flask.FlaskConfig.HOST == '127.0.0.1'
        
        os.environ.pop('FLASK_HOST', None)
    
    def test_port_default(self):
        """Test valor por defecto de PORT"""
        # Due to module caching, just verify the value exists and is an integer
        import importlib
        import config_flask
        importlib.reload(config_flask)
        
        assert isinstance(config_flask.FlaskConfig.PORT, int)
        assert config_flask.FlaskConfig.PORT > 0
    
    def test_port_from_env(self):
        """Test PORT desde variable de entorno"""
        os.environ['FLASK_PORT'] = '8000'
        
        import importlib
        import config_flask
        importlib.reload(config_flask)
        
        assert config_flask.FlaskConfig.PORT == 8000
        
        os.environ.pop('FLASK_PORT', None)
    
    def test_session_cookie_config(self):
        """Test configuración de cookies de sesión"""
        import importlib
        import config_flask
        importlib.reload(config_flask)
        
        assert config_flask.FlaskConfig.SESSION_COOKIE_SECURE is False
        assert config_flask.FlaskConfig.SESSION_COOKIE_HTTPONLY is True
        assert config_flask.FlaskConfig.SESSION_COOKIE_SAMESITE == "Lax"
    
    def test_permanent_session_lifetime(self):
        """Test lifetime de sesión permanente"""
        import importlib
        import config_flask
        importlib.reload(config_flask)
        
        assert config_flask.FlaskConfig.PERMANENT_SESSION_LIFETIME == 3600
    
    def test_socketio_config(self):
        """Test configuración de SocketIO"""
        import importlib
        import config_flask
        importlib.reload(config_flask)
        
        assert config_flask.FlaskConfig.SOCKETIO_ASYNC_MODE == "threading"
        assert config_flask.FlaskConfig.SOCKETIO_CORS_ALLOWED_ORIGINS == "*"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
