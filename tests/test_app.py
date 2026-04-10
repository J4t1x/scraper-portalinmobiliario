"""Tests para app.py (Flask app initialization)"""

import pytest
from unittest.mock import patch, MagicMock

# Skip these tests due to SQLAlchemy compatibility issues with Python 3.14
pytestmark = pytest.mark.skip(reason="SQLAlchemy compatibility issues with Python 3.14")


class TestFlaskApp:
    """Tests para la inicialización de la aplicación Flask"""
    
    @patch('app.login_manager')
    @patch('app.socketio')
    @patch('app.bp')
    @patch('app.scheduler_bp')
    def test_app_initialization(self, mock_scheduler_bp, mock_bp, mock_socketio, mock_login_manager):
        """Test que la aplicación Flask se inicializa correctamente"""
        with patch('app.Flask') as mock_flask:
            mock_app = MagicMock()
            mock_flask.return_value = mock_app
            
            # Import app after mocking
            import app
            
            # Verificar que Flask fue instanciado
            mock_flask.assert_called_once_with(__name__)
            
            # Verificar que config se cargó
            mock_app.config.from_object.assert_called_once()
            
            # Verificar que login_manager se inicializó
            mock_login_manager.init_app.assert_called_once_with(mock_app)
            
            # Verificar que blueprints se registraron
            assert mock_app.register_blueprint.call_count == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
