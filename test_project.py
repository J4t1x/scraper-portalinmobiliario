"""
Script de prueba para validar el funcionamiento del proyecto scraper-portalinmoviliario.
"""

import sys
from datetime import datetime

def test_project_functionality():
    """Test that the project works correctly without database."""
    
    print("=" * 60)
    print("Validando funcionamiento del proyecto scraper-portalinmoviliario")
    print("=" * 60)
    
    # Test 1: Importar configuración
    print("\n1. Probando configuración...")
    try:
        from config import Config
        print(f"   ✓ Configuración cargada correctamente")
        print(f"   - DATABASE_URL: {Config.DATABASE_URL or 'No configurado'}")
        print(f"   - DB_POOL_SIZE: {Config.DB_POOL_SIZE}")
        print(f"   - DELAY_BETWEEN_REQUESTS: {Config.DELAY_BETWEEN_REQUESTS}")
        print(f"   - MAX_RETRIES: {Config.MAX_RETRIES}")
        print(f"   - TIMEOUT: {Config.TIMEOUT}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Test 2: Importar modelos
    print("\n2. Probando modelos de base de datos...")
    try:
        from models import Base, Property, Feature, Image, Publisher
        print(f"   ✓ Modelos importados correctamente")
        print(f"   - Property: {Property.__tablename__}")
        print(f"   - Feature: {Feature.__tablename__}")
        print(f"   - Image: {Image.__tablename__}")
        print(f"   - Publisher: {Publisher.__tablename__}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Test 3: Verificar configuración de base de datos
    print("\n3. Verificando configuración de base de datos...")
    try:
        from scraper_db_integration import is_database_configured
        db_configured = is_database_configured()
        print(f"   ✓ Verificación completada")
        print(f"   - Base de datos configurada: {db_configured}")
        if not db_configured:
            print(f"   - Nota: El proyecto funciona sin base de datos")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Test 4: Probar función de persistencia sin base de datos
    print("\n4. Probando función de persistencia sin base de datos...")
    try:
        from scraper_db_integration import persist_properties
        
        # Datos de prueba
        test_properties = [
            {
                'url': 'https://test.com/prop1',
                'portal_id': 'TEST-001',
                'titulo': 'Propiedad de prueba',
                'precio': 100000000,
                'precio_moneda': 'CLP',
                'operacion': 'venta',
                'tipo': 'departamento',
                'comuna': 'Santiago',
                'region': 'Metropolitana',
                'direccion': 'Dirección de prueba',
                'publicado_en': datetime.now(),
                'features': {'dormitorios': '2', 'baños': '1', 'm2': '50'},
                'imagenes': ['https://test.com/img1.jpg', 'https://test.com/img2.jpg'],
                'publisher': {'nombre': 'Test Publisher', 'telefono': '12345678', 'email': 'test@test.com', 'tipo': 'profesional'}
            }
        ]
        
        # Intentar persistir (debería retornar 0 si no hay base de datos configurada)
        count = persist_properties(test_properties)
        print(f"   ✓ Función de persistencia ejecutada correctamente")
        print(f"   - Propiedades persistidas: {count}")
        if count == 0:
            print(f"   - Comportamiento esperado: sin base de datos configurada")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Test 5: Verificar estructura de modelos
    print("\n5. Verificando estructura de modelos...")
    try:
        from models import Property, Feature, Image, Publisher
        
        # Verificar Property
        assert hasattr(Property, '__tablename__'), "Property debe tener __tablename__"
        assert hasattr(Property, 'id'), "Property debe tener id"
        assert hasattr(Property, 'url'), "Property debe tener url"
        print(f"   ✓ Estructura de Property correcta")
        
        # Verificar Feature
        assert hasattr(Feature, '__tablename__'), "Feature debe tener __tablename__"
        assert hasattr(Feature, 'property_id'), "Feature debe tener property_id"
        print(f"   ✓ Estructura de Feature correcta")
        
        # Verificar Image
        assert hasattr(Image, '__tablename__'), "Image debe tener __tablename__"
        assert hasattr(Image, 'property_id'), "Image debe tener property_id"
        print(f"   ✓ Estructura de Image correcta")
        
        # Verificar Publisher
        assert hasattr(Publisher, '__tablename__'), "Publisher debe tener __tablename__"
        assert hasattr(Publisher, 'property_id'), "Publisher debe tener property_id"
        print(f"   ✓ Estructura de Publisher correcta")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Test 6: Verificar configuración de Alembic
    print("\n6. Verificando configuración de Alembic...")
    try:
        import os
        alembic_ini = os.path.join(os.path.dirname(__file__), 'migrations', 'alembic.ini')
        env_py = os.path.join(os.path.dirname(__file__), 'migrations', 'env.py')
        
        if os.path.exists(alembic_ini):
            print(f"   ✓ alembic.ini existe")
        else:
            print(f"   ✗ alembic.ini no existe")
            return False
            
        if os.path.exists(env_py):
            print(f"   ✓ env.py existe")
        else:
            print(f"   ✗ env.py no existe")
            return False
            
        versions_dir = os.path.join(os.path.dirname(__file__), 'migrations', 'versions')
        if os.path.exists(versions_dir):
            print(f"   ✓ versions/ existe")
        else:
            print(f"   ✗ versions/ no existe")
            return False
            
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ Todas las pruebas pasaron exitosamente")
    print("=" * 60)
    print("\nEl proyecto está funcionando correctamente sin base de datos.")
    print("Para usar la base de datos:")
    print("1. Configurar DATABASE_URL en .env")
    print("2. Instalar psycopg2-binary: pip install psycopg2-binary")
    print("3. Ejecutar migraciones: alembic upgrade head")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = test_project_functionality()
    sys.exit(0 if success else 1)
