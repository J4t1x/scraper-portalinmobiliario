import pytest
import os
from app import app
from api import cache

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['CACHE_TYPE'] = 'SimpleCache'  # Use simple cache for tests
    os.environ['API_KEY'] = 'test-key-123'
    
    with app.app_context():
        cache.clear()
        
    with app.test_client() as client:
        yield client

def test_cache_invalidate_requires_token(client):
    response = client.delete('/api/v2/cache/invalidate')
    assert response.status_code == 401
    
def test_cache_invalidate_with_token(client):
    headers = {'X-API-KEY': 'test-key-123'}
    
    # Store dummy data in cache to test invalidation
    with app.app_context():
        cache.set("dummy_key", "dummy_value", timeout=60)
        assert cache.get("dummy_key") == "dummy_value"
        
    response = client.delete('/api/v2/cache/invalidate', headers=headers)
    assert response.status_code == 200
    assert response.json['success'] == True
    
    with app.app_context():
        assert cache.get("dummy_key") is None
