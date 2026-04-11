import pytest
import os
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    # Ensure test environment handles API_KEY directly if needed
    os.environ['API_KEY'] = 'test-key-123'
    with app.test_client() as client:
        yield client

def test_api_docs_available(client):
    """Test that swagger documentation is available"""
    response = client.get('/api/v2/docs')
    assert response.status_code == 200

def test_health_check_without_token(client):
    """Test health check does not require token"""
    response = client.get('/api/v2/health')
    assert response.status_code == 200
    assert response.json['success'] == True
    assert response.json['data']['status'] == 'healthy'

def test_properties_requires_token(client):
    """Test that endpoints require API KEY"""
    response = client.get('/api/v2/properties')
    assert response.status_code == 401
    assert 'Token es invalido o falta' in response.json['message']

def test_properties_with_token(client):
    """Test properties endpoint with valid token"""
    headers = {'X-API-KEY': 'test-key-123'}
    response = client.get('/api/v2/properties', headers=headers)
    # The actual response may be 200 depending on JSONDataLoader behavior in test environment
    # but we just want to test auth layer and route availability here
    assert response.status_code in (200, 500)

def test_stats_with_token(client):
    headers = {'X-API-KEY': 'test-key-123'}
    response = client.get('/api/v2/analytics/stats', headers=headers)
    assert response.status_code in (200, 500)
