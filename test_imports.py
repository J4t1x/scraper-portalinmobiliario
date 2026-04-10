"""
Script de prueba para validar que los modelos se importen correctamente.
"""

import sys

def test_imports():
    """Test that all modules can be imported successfully."""
    
    print("Testing imports...")
    
    try:
        print("✓ Importing config...")
        from config import Config
        print(f"  - DATABASE_URL: {Config.DATABASE_URL}")
        print(f"  - DB_POOL_SIZE: {Config.DB_POOL_SIZE}")
        print(f"  - DB_MAX_OVERFLOW: {Config.DB_MAX_OVERFLOW}")
        print(f"  - DELAY_BETWEEN_REQUESTS: {Config.DELAY_BETWEEN_REQUESTS}")
        print(f"  - MAX_RETRIES: {Config.MAX_RETRIES}")
        print(f"  - TIMEOUT: {Config.TIMEOUT}")
        print(f"  - USER_AGENT: {Config.USER_AGENT}")
    except Exception as e:
        print(f"✗ Error importing config: {e}")
        return False
    
    try:
        print("\n✓ Importing models...")
        from models import Base, Property, Feature, Image, Publisher
        print("  - Base: OK")
        print("  - Property: OK")
        print("  - Feature: OK")
        print("  - Image: OK")
        print("  - Publisher: OK")
    except Exception as e:
        print(f"✗ Error importing models: {e}")
        return False
    
    try:
        print("\n✓ Importing database module...")
        from database import setup_database, get_engine, get_session, DatabaseSession
        print("  - setup_database: OK")
        print("  - get_engine: OK")
        print("  - get_session: OK")
        print("  - DatabaseSession: OK")
    except Exception as e:
        print(f"✗ Error importing database: {e}")
        return False
    
    try:
        print("\n✓ Importing scraper_db_integration module...")
        from scraper_db_integration import persist_properties, persist_single_property, is_database_configured
        print("  - persist_properties: OK")
        print("  - persist_single_property: OK")
        print("  - is_database_configured: OK")
    except Exception as e:
        print(f"✗ Error importing scraper_db_integration: {e}")
        return False
    
    print("\n✓ All imports successful!")
    return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
