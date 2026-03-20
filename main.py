#!/usr/bin/env python3
"""
Portal Inmobiliario Scraper
Script principal para scrapear propiedades de portalinmobiliario.com
"""

import argparse
import sys
from scraper_selenium import PortalInmobiliarioSeleniumScraper
from exporter import DataExporter
from config import Config
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description='Scraper de propiedades de portalinmobiliario.com',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python main.py --operacion venta --tipo departamento
  python main.py --operacion arriendo --tipo casa --max-pages 5
  python main.py --operacion venta --tipo oficina --formato json
  python main.py --operacion arriendo --tipo departamento --formato csv --max-pages 10

Operaciones disponibles: venta, arriendo, arriendo-de-temporada
Tipos disponibles: departamento, casa, oficina, terreno, local-comercial, bodega, estacionamiento, parcela
        """
    )
    
    parser.add_argument(
        '--operacion',
        type=str,
        required=True,
        choices=Config.OPERACIONES,
        help='Tipo de operación (venta, arriendo, arriendo-de-temporada)'
    )
    
    parser.add_argument(
        '--tipo',
        type=str,
        required=True,
        choices=Config.TIPOS_PROPIEDAD,
        help='Tipo de propiedad'
    )
    
    parser.add_argument(
        '--max-pages',
        type=int,
        default=None,
        help='Número máximo de páginas a scrapear (default: todas)'
    )
    
    parser.add_argument(
        '--formato',
        type=str,
        default='txt',
        choices=['txt', 'json', 'csv'],
        help='Formato de exportación (default: txt)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Modo verbose (más detalles en logs)'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        logger.info("=" * 60)
        logger.info("PORTAL INMOBILIARIO SCRAPER")
        logger.info("=" * 60)
        logger.info(f"Operación: {args.operacion}")
        logger.info(f"Tipo: {args.tipo}")
        logger.info(f"Formato: {args.formato}")
        if args.max_pages:
            logger.info(f"Máximo de páginas: {args.max_pages}")
        logger.info("=" * 60)
        
        scraper = PortalInmobiliarioSeleniumScraper(args.operacion, args.tipo, headless=True)
        
        properties = scraper.scrape_all_pages(max_pages=args.max_pages)
        
        if not properties:
            logger.warning("No se encontraron propiedades")
            sys.exit(0)
        
        exporter = DataExporter()
        
        if args.formato == 'txt':
            filepath = exporter.export_to_txt(properties, args.operacion, args.tipo)
        elif args.formato == 'json':
            filepath = exporter.export_to_json(properties, args.operacion, args.tipo)
        elif args.formato == 'csv':
            filepath = exporter.export_to_csv(properties, args.operacion, args.tipo)
        
        logger.info("=" * 60)
        logger.info(f"✅ COMPLETADO EXITOSAMENTE")
        logger.info(f"Total de propiedades: {len(properties)}")
        logger.info(f"Archivo generado: {filepath}")
        logger.info("=" * 60)
        
    except KeyboardInterrupt:
        logger.info("\n⚠️  Scraping interrumpido por el usuario")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=args.verbose)
        sys.exit(1)


if __name__ == "__main__":
    main()
