#!/usr/bin/env python3
"""
Ejemplo de uso del scraper de Portal Inmobiliario
"""

from scraper import PortalInmobiliarioScraper
from exporter import DataExporter
from utils import print_property_summary, get_price_statistics
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def example_basic():
    """Ejemplo básico: scrapear departamentos en venta"""
    print("\n" + "="*60)
    print("EJEMPLO 1: Scraping básico")
    print("="*60 + "\n")
    
    scraper = PortalInmobiliarioScraper("venta", "departamento")
    
    properties = scraper.scrape_all_pages(max_pages=2)
    
    print_property_summary(properties)
    
    exporter = DataExporter()
    exporter.export_to_txt(properties, "venta", "departamento")


def example_with_stats():
    """Ejemplo con estadísticas de precios"""
    print("\n" + "="*60)
    print("EJEMPLO 2: Scraping con estadísticas")
    print("="*60 + "\n")
    
    scraper = PortalInmobiliarioScraper("arriendo", "casa")
    
    properties = scraper.scrape_all_pages(max_pages=3)
    
    stats = get_price_statistics(properties)
    
    print(f"\n📊 ESTADÍSTICAS DE PRECIOS:")
    print(f"   Total con precio: {stats['total']}")
    print(f"   Precio mínimo: ${stats['min']:,.0f}")
    print(f"   Precio máximo: ${stats['max']:,.0f}")
    print(f"   Precio promedio: ${stats['avg']:,.0f}\n")
    
    exporter = DataExporter()
    exporter.export_to_json(properties, "arriendo", "casa")


def example_multiple_formats():
    """Ejemplo: exportar a múltiples formatos"""
    print("\n" + "="*60)
    print("EJEMPLO 3: Exportación a múltiples formatos")
    print("="*60 + "\n")
    
    scraper = PortalInmobiliarioScraper("venta", "oficina")
    
    properties = scraper.scrape_all_pages(max_pages=1)
    
    exporter = DataExporter()
    
    txt_file = exporter.export_to_txt(properties, "venta", "oficina")
    json_file = exporter.export_to_json(properties, "venta", "oficina")
    csv_file = exporter.export_to_csv(properties, "venta", "oficina")
    
    print(f"\n✅ Archivos generados:")
    print(f"   - TXT:  {txt_file}")
    print(f"   - JSON: {json_file}")
    print(f"   - CSV:  {csv_file}\n")


if __name__ == "__main__":
    print("\n🏠 EJEMPLOS DE USO - PORTAL INMOBILIARIO SCRAPER\n")
    
    try:
        example_basic()
        
    except KeyboardInterrupt:
        print("\n⚠️  Ejemplos interrumpidos por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
