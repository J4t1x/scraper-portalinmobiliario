#!/usr/bin/env python3
"""
Script de prueba para verificar la integración con Ollama
"""

import sys
import os

# Agregar el directorio actual al path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.openai_agent import AnalyticsAgent
from logger_config import get_logger

logger = get_logger(__name__)

def test_ollama_connection():
    """Prueba la conexión con Ollama"""
    print("=" * 60)
    print("TEST: Conexión con Ollama")
    print("=" * 60)
    
    agent = AnalyticsAgent()
    
    if agent.client:
        print("✅ Conexión exitosa con Ollama")
        print(f"   URL: {agent.ollama_url}")
        print(f"   Modelo: {agent.model}")
        return True
    else:
        print("❌ No se pudo conectar con Ollama")
        print("   Asegúrate de que Ollama esté corriendo: ollama serve")
        return False

def test_simple_query():
    """Prueba una consulta simple"""
    print("\n" + "=" * 60)
    print("TEST: Consulta simple")
    print("=" * 60)
    
    agent = AnalyticsAgent()
    
    if not agent.client:
        print("❌ Saltando prueba - Ollama no está disponible")
        return False
    
    # Consulta de prueba simple
    query = "¿Cuántas propiedades hay en total?"
    print(f"\nConsulta: {query}")
    print("\nRespuesta:")
    print("-" * 60)
    
    try:
        response = agent.generate_response(query)
        print(response)
        print("-" * 60)
        
        if response and not response.startswith("Error"):
            print("\n✅ Consulta exitosa")
            return True
        else:
            print("\n❌ La consulta retornó un error")
            return False
    except Exception as e:
        print(f"\n❌ Error durante la consulta: {e}")
        return False

def test_analytical_query():
    """Prueba una consulta analítica más compleja"""
    print("\n" + "=" * 60)
    print("TEST: Consulta analítica")
    print("=" * 60)
    
    agent = AnalyticsAgent()
    
    if not agent.client:
        print("❌ Saltando prueba - Ollama no está disponible")
        return False
    
    # Consulta analítica
    query = "¿Cuál es el precio promedio por metro cuadrado en las diferentes comunas?"
    print(f"\nConsulta: {query}")
    print("\nRespuesta:")
    print("-" * 60)
    
    try:
        response = agent.generate_response(query)
        print(response)
        print("-" * 60)
        
        if response and not response.startswith("Error"):
            print("\n✅ Consulta exitosa")
            return True
        else:
            print("\n❌ La consulta retornó un error")
            return False
    except Exception as e:
        print(f"\n❌ Error durante la consulta: {e}")
        return False

def main():
    """Ejecuta todas las pruebas"""
    print("\n🧪 PRUEBAS DE INTEGRACIÓN OLLAMA")
    print("=" * 60)
    
    results = []
    
    # Test 1: Conexión
    results.append(("Conexión", test_ollama_connection()))
    
    # Test 2: Consulta simple
    if results[0][1]:  # Solo si la conexión fue exitosa
        results.append(("Consulta simple", test_simple_query()))
        results.append(("Consulta analítica", test_analytical_query()))
    
    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN DE PRUEBAS")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    total = len(results)
    passed = sum(1 for _, result in results if result)
    
    print(f"\nTotal: {passed}/{total} pruebas exitosas")
    
    if passed == total:
        print("\n🎉 ¡Todas las pruebas pasaron!")
        return 0
    else:
        print("\n⚠️  Algunas pruebas fallaron")
        return 1

if __name__ == "__main__":
    sys.exit(main())
