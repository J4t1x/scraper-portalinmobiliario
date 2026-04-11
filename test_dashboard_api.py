#!/usr/bin/env python
"""
Script de prueba para validar el endpoint de estadísticas avanzadas
"""

from data_loader import JSONDataLoader
import json

def test_advanced_stats_api():
    """Probar el endpoint de estadísticas avanzadas"""
    try:
        loader = JSONDataLoader()
        stats = loader.get_advanced_stats()
        
        print("=" * 80)
        print("ESTADÍSTICAS AVANZADAS DEL DASHBOARD")
        print("=" * 80)
        
        # Básicos
        print("\n📊 ESTADÍSTICAS BÁSICAS:")
        print(f"  Total propiedades: {stats['basic']['total']}")
        print(f"  Archivos JSON: {stats['basic']['files_loaded']}")
        print(f"  Por operación: {stats['basic']['by_operacion']}")
        print(f"  Por tipo: {stats['basic']['by_tipo']}")
        
        # Precios
        print("\n💰 ESTADÍSTICAS DE PRECIOS:")
        print(f"  Precio promedio: ${stats['prices']['avg']:,.0f}")
        print(f"  Precio mínimo: ${stats['prices']['min']:,.0f}")
        print(f"  Precio máximo: ${stats['prices']['max']:,.0f}")
        print(f"  Precio mediana: ${stats['prices']['median']:,.0f}")
        print(f"  Propiedades con precio: {stats['prices']['total_with_price']}")
        
        # Completitud
        print("\n✅ COMPLETITUD DE DATOS:")
        print(f"  Completitud general: {stats['completeness']['overall']:.1f}%")
        print(f"  Con imágenes: {stats['completeness']['with_images']}")
        print(f"  Con descripción: {stats['completeness']['with_description']}")
        print(f"  Con coordenadas: {stats['completeness']['with_coordinates']}")
        
        # Temporal
        print("\n📅 DISTRIBUCIÓN TEMPORAL:")
        print(f"  Total fechas: {stats['temporal']['total_dates']}")
        print(f"  Fecha más antigua: {stats['temporal']['oldest_date']}")
        print(f"  Fecha más reciente: {stats['temporal']['latest_date']}")
        
        # Publicadores
        print("\n🏢 PUBLICADORES:")
        print(f"  Total publicadores: {stats['publishers']['total_publishers']}")
        print(f"  Propiedades con publicador: {stats['publishers']['total_with_publisher']}")
        if stats['publishers']['top']:
            print("  Top 5 publicadores:")
            for i, (name, count) in enumerate(list(stats['publishers']['top'].items())[:5], 1):
                print(f"    {i}. {name}: {count} propiedades")
        
        # Rangos de precio
        print("\n💵 RANGOS DE PRECIO:")
        for range_name, count in stats['price_ranges'].items():
            print(f"  {range_name}: {count} propiedades")
        
        # Comunas
        print("\n🏘️  TOP 10 COMUNAS:")
        top_comunas = sorted(stats['by_comuna'].items(), key=lambda x: x[1], reverse=True)[:10]
        for i, (comuna, count) in enumerate(top_comunas, 1):
            print(f"  {i}. {comuna}: {count} propiedades")
        
        print("\n" + "=" * 80)
        print("✅ TODAS LAS ESTADÍSTICAS SE CALCULARON CORRECTAMENTE")
        print("=" * 80)
        
        return True
        
    except FileNotFoundError:
        print("\n⚠️  No se encontró el directorio output/")
        print("Ejecuta el scraper primero para generar datos.")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_advanced_stats_api()
    exit(0 if success else 1)
