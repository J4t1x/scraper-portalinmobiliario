#!/usr/bin/env python3
"""
Portal Inmobiliario Scraper
Script principal para scrapear propiedades de portalinmobiliario.com
"""

import argparse
import sys
import asyncio
from scraper_selenium import PortalInmobiliarioSeleniumScraper
from exporter import DataExporter
from deduplicator import Deduplicator
from config import Config
from logger_config import setup_logging, get_logger, log_performance

# Setup logging robusto al inicio
setup_logging()
logger = get_logger(__name__)


def run_scraping(
    operacion: str,
    tipo: str,
    max_pages: int = None,
    formato: str = 'txt',
    scrape_details: bool = False,
    max_detail_properties: int = None,
    exclude_duplicates: bool = False,
    reset_duplicates: bool = False,
    registry_path: str = 'data/scraped_ids.json',
    persist_to_db: bool = False,
    verbose: bool = False
) -> dict:
    """
    Ejecutar scraping y retornar resultado con métricas.
    
    Args:
        operacion: Tipo de operación
        tipo: Tipo de propiedad
        max_pages: Máximo de páginas
        formato: Formato de exportación
        scrape_details: Scrapear detalles
        max_detail_properties: Máximo de propiedades con detalle
        exclude_duplicates: Excluir duplicados
        reset_duplicates: Resetear registro
        registry_path: Ruta al registro
        persist_to_db: Persistir en DB
        verbose: Modo verbose
        
    Returns:
        Dict con métricas del scraping
    """
    try:
        logger.info("=" * 60)
        logger.info("PORTAL INMOBILIARIO SCRAPER")
        logger.info("=" * 60)
        logger.info(f"Operación: {operacion}")
        logger.info(f"Tipo: {tipo}")
        logger.info(f"Formato: {formato}")
        if max_pages:
            logger.info(f"Máximo de páginas: {max_pages}")
        if scrape_details:
            logger.info("Modo detalle: ACTIVADO")
            if max_detail_properties:
                logger.info(f"Máximo propiedades con detalle: {max_detail_properties}")
        if persist_to_db:
            logger.info("Persistencia en PostgreSQL: ACTIVADO")
        logger.info("=" * 60)
        
        scraper = PortalInmobiliarioSeleniumScraper(
            operacion, 
            tipo, 
            headless=True,
            persist_to_db=persist_to_db
        )
        
        properties = scraper.scrape_all_pages(
            max_pages=max_pages,
            scrape_details=scrape_details,
            max_detail_properties=max_detail_properties
        )
        
        if not properties:
            logger.warning("No se encontraron propiedades")
            return {
                'properties_scraped': 0,
                'pages_processed': 0,
                'status': 'success'
            }
        
        # Inicializar deduplicador
        deduplicator = Deduplicator(registry_path)
        
        # Resetear registro si se solicita
        if reset_duplicates:
            deduplicator.reset_registry()
            logger.info("🗑️  Registro de duplicados reseteado")
        
        # Procesar propiedades con deduplicación
        properties = deduplicator.process_properties(properties)
        
        # Filtrar duplicados si se solicita
        if exclude_duplicates:
            original_count = len(properties)
            properties = deduplicator.filter_duplicates(properties)
            logger.info(f"🚫 Filtradas {original_count - len(properties)} propiedades duplicadas")
        
        # Guardar registro actualizado
        deduplicator.save_registry()
        
        exporter = DataExporter()
        
        if formato == 'txt':
            filepath = exporter.export_to_txt(properties, operacion, tipo)
        elif formato == 'json':
            filepath = exporter.export_to_json(properties, operacion, tipo)
        elif formato == 'csv':
            filepath = exporter.export_to_csv(properties, operacion, tipo)
        
        logger.info("=" * 60)
        logger.info(f"✅ COMPLETADO EXITOSAMENTE")
        logger.info(f"Total de propiedades: {len(properties)}")
        logger.info(f"Archivo generado: {filepath}")
        logger.info("=" * 60)
        
        return {
            'properties_scraped': len(properties),
            'pages_processed': max_pages if max_pages else 'unknown',
            'status': 'success',
            'metadata': {
                'operacion': operacion,
                'tipo': tipo,
                'formato': formato
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=verbose)
        return {
            'properties_scraped': 0,
            'pages_processed': 0,
            'status': 'failed',
            'error': str(e)
        }


def handle_scheduler_command(args):
    """Manejar comandos del scheduler."""
    from scheduler import get_scheduler, shutdown_global_scheduler
    
    if args.scheduler_command == 'start':
        from scheduler_jobs import setup_default_jobs
        
        scheduler = get_scheduler()
        
        # Setup default jobs (SPEC-012)
        setup_default_jobs(scheduler)
        
        scheduler.start()
        logger.info("Scheduler iniciado con jobs default (SPEC-012). Presiona Ctrl+C para detener.")
        
        # Keep running until interrupted
        try:
            while True:
                asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Deteniendo scheduler...")
            shutdown_global_scheduler()
            
    elif args.scheduler_command == 'stop':
        from scheduler import get_scheduler
        scheduler = get_scheduler()
        scheduler.shutdown(wait=True)
        logger.info("Scheduler detenido")
        
    elif args.scheduler_command == 'pause':
        from scheduler import get_scheduler
        scheduler = get_scheduler()
        scheduler.pause()
        logger.info("Scheduler pausado")
        
    elif args.scheduler_command == 'resume':
        from scheduler import get_scheduler
        scheduler = get_scheduler()
        scheduler.resume()
        logger.info("Scheduler reanudado")
        
    elif args.scheduler_command == 'status':
        from scheduler import get_scheduler
        scheduler = get_scheduler()
        state = scheduler.get_scheduler_state()
        jobs = scheduler.get_jobs()
        
        print("\n" + "=" * 60)
        print("SCHEDULER STATUS")
        print("=" * 60)
        print(f"Estado: {state['status'] if state else 'N/A'}")
        print(f"ID: {state['scheduler_id'] if state else 'N/A'}")
        print(f"Total ejecuciones: {state['total_jobs_executed'] if state else 0}")
        print(f"Último heartbeat: {state['last_heartbeat'] if state else 'N/A'}")
        print(f"\nJobs configurados ({len(jobs)}):")
        for job in jobs:
            print(f"  - {job['id']}: {job['name']}")
            print(f"    Próxima ejecución: {job['next_run_time']}")
        print("=" * 60)
        
    elif args.scheduler_command == 'list-jobs':
        from scheduler import get_scheduler
        scheduler = get_scheduler()
        jobs = scheduler.get_jobs()
        
        print("\n" + "=" * 60)
        print("JOBS CONFIGURADOS")
        print("=" * 60)
        for job in jobs:
            print(f"ID: {job['id']}")
            print(f"Nombre: {job['name']}")
            print(f"Trigger: {job['trigger']}")
            print(f"Próxima ejecución: {job['next_run_time']}")
            print("-" * 60)
        
    elif args.scheduler_command == 'add-job':
        from scheduler import get_scheduler
        from scheduler_jobs import create_scraping_job
        
        scheduler = get_scheduler()
        
        # Parse schedule arguments
        schedule_args = {}
        if args.schedule_type == 'interval':
            if args.hours:
                schedule_args['hours'] = args.hours
            if args.minutes:
                schedule_args['minutes'] = args.minutes
        elif args.schedule_type == 'cron':
            if args.day_of_week:
                schedule_args['day_of_week'] = args.day_of_week
            if args.hour:
                schedule_args['hour'] = args.hour
            if args.minute:
                schedule_args['minute'] = args.minute
        
        # Add scraping parameters
        if args.max_pages:
            schedule_args['max_pages'] = args.max_pages
        if args.scrape_details:
            schedule_args['scrape_details'] = True
        if args.max_detail_properties:
            schedule_args['max_detail_properties'] = args.max_detail_properties
        if args.formato:
            schedule_args['formato'] = args.formato
        
        job_id = create_scraping_job(
            scheduler,
            operacion=args.operacion,
            tipo=args.tipo,
            schedule_type=args.schedule_type,
            **schedule_args
        )
        
        logger.info(f"Job agregado: {job_id}")
        
    elif args.scheduler_command == 'remove-job':
        from scheduler import get_scheduler
        scheduler = get_scheduler()
        success = scheduler.remove_job(args.job_id)
        
        if success:
            logger.info(f"Job removido: {args.job_id}")
        else:
            logger.error(f"Job no encontrado: {args.job_id}")
            sys.exit(1)
            
    elif args.scheduler_command == 'setup-default':
        from scheduler import get_scheduler
        from scheduler_jobs import setup_default_jobs
        
        scheduler = get_scheduler()
        setup_default_jobs(scheduler)
        logger.info("Jobs default configurados (SPEC-012):")
        
        jobs = scheduler.get_jobs()
        for job in jobs:
            logger.info(f"  - {job['id']}: {job['trigger']}")


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description='Scraper de propiedades de portalinmobiliario.com',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  # Scraping manual
  python main.py --operacion venta --tipo departamento
  python main.py --operacion arriendo --tipo casa --max-pages 5
  python main.py --operacion venta --tipo oficina --formato json
  python main.py --operacion arriendo --tipo departamento --formato csv --max-pages 10
  python main.py --operacion venta --tipo departamento --scrape-details --max-pages 1
  python main.py --operacion venta --tipo departamento --scrape-details --max-detail-properties 5

  # Scheduler commands
  python main.py --scheduler start
  python main.py --scheduler status
  python main.py --scheduler list-jobs
  python main.py --scheduler add-job --operacion venta --tipo departamento --schedule-type interval --hours 6
  python main.py --scheduler remove-job --job-id scrape_venta_departamento
  python main.py --scheduler setup-default

Operaciones disponibles: venta, arriendo, arriendo-de-temporada
Tipos disponibles: departamento, casa, oficina, terreno, local-comercial, bodega, estacionamiento, parcela
        """
    )
    
    # Add scheduler subcommand
    parser.add_argument(
        '--scheduler',
        type=str,
        choices=['start', 'stop', 'pause', 'resume', 'status', 'list-jobs', 'add-job', 'remove-job', 'setup-default'],
        help='Comando del scheduler (start, stop, pause, resume, status, list-jobs, add-job, remove-job, setup-default)'
    )
    
    # Scheduler-specific arguments
    parser.add_argument(
        '--job-id',
        type=str,
        help='ID del job (para remove-job)'
    )
    
    parser.add_argument(
        '--schedule-type',
        type=str,
        choices=['interval', 'cron'],
        help='Tipo de schedule (interval, cron)'
    )
    
    parser.add_argument(
        '--hours',
        type=int,
        help='Horas para schedule interval'
    )
    
    parser.add_argument(
        '--minutes',
        type=int,
        help='Minutos para schedule interval'
    )
    
    parser.add_argument(
        '--day-of-week',
        type=str,
        help='Día de la semana para schedule cron (mon, tue, wed, thu, fri, sat, sun)'
    )
    
    parser.add_argument(
        '--hour',
        type=int,
        help='Hora para schedule cron'
    )
    
    parser.add_argument(
        '--minute',
        type=int,
        help='Minuto para schedule cron'
    )
    
    parser.add_argument(
        '--operacion',
        type=str,
        required=False,
        choices=Config.OPERACIONES,
        help='Tipo de operación (venta, arriendo, arriendo-de-temporada)'
    )
    
    parser.add_argument(
        '--tipo',
        type=str,
        required=False,
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
    
    parser.add_argument(
        '--scrape-details',
        action='store_true',
        help='Scrapear información adicional de cada propiedad (página de detalle)'
    )
    
    parser.add_argument(
        '--max-detail-properties',
        type=int,
        default=None,
        help='Máximo de propiedades para las cuales scrapear detalle (default: todas)'
    )
    
    parser.add_argument(
        '--include-duplicates',
        action='store_true',
        default=True,
        help='Incluir propiedades duplicadas en la exportación (default: True)'
    )
    
    parser.add_argument(
        '--exclude-duplicates',
        action='store_true',
        help='Excluir propiedades duplicadas de la exportación'
    )
    
    parser.add_argument(
        '--reset-duplicates',
        action='store_true',
        help='Limpiar el registro de duplicados antes de ejecutar'
    )
    
    parser.add_argument(
        '--dedup-stats',
        action='store_true',
        help='Mostrar estadísticas de deduplicación y salir'
    )
    
    parser.add_argument(
        '--registry-path',
        type=str,
        default='data/scraped_ids.json',
        help='Ruta al archivo de registro de duplicados (default: data/scraped_ids.json)'
    )
    
    parser.add_argument(
        '--persist-to-db',
        action='store_true',
        help='Persistir propiedades en PostgreSQL (requiere DATABASE_URL configurado)'
    )
    
    args = parser.parse_args()
    
    # Configurar logging verbose si se solicita
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Route to scheduler command or scraping
    if args.scheduler:
        # Scheduler command mode
        args.scheduler_command = args.scheduler
        handle_scheduler_command(args)
    else:
        # Manual scraping mode
        if not args.operacion or not args.tipo:
            parser.error("--operacion y --tipo son requeridos para scraping manual (usa --help para ver opciones de scheduler)")
        
        try:
            logger.info("=" * 60)
            logger.info("PORTAL INMOBILIARIO SCRAPER")
            logger.info("=" * 60)
            logger.info(f"Operación: {args.operacion}")
            logger.info(f"Tipo: {args.tipo}")
            logger.info(f"Formato: {args.formato}")
            if args.max_pages:
                logger.info(f"Máximo de páginas: {args.max_pages}")
            if args.scrape_details:
                logger.info("Modo detalle: ACTIVADO")
                if args.max_detail_properties:
                    logger.info(f"Máximo propiedades con detalle: {args.max_detail_properties}")
            if args.persist_to_db:
                logger.info("Persistencia en PostgreSQL: ACTIVADO")
            logger.info("=" * 60)
            
            scraper = PortalInmobiliarioSeleniumScraper(
                args.operacion, 
                args.tipo, 
                headless=True,
                persist_to_db=args.persist_to_db
            )
            
            properties = scraper.scrape_all_pages(
                max_pages=args.max_pages,
                scrape_details=args.scrape_details,
                max_detail_properties=args.max_detail_properties
            )
            
            if not properties:
                logger.warning("No se encontraron propiedades")
                sys.exit(0)
            
            # Inicializar deduplicador
            deduplicator = Deduplicator(args.registry_path)
            
            # Mostrar estadísticas y salir si se solicita
            if args.dedup_stats:
                deduplicator.print_stats()
                sys.exit(0)
            
            # Resetear registro si se solicita
            if args.reset_duplicates:
                deduplicator.reset_registry()
                logger.info("🗑️  Registro de duplicados reseteado")
            
            # Procesar propiedades con deduplicación
            properties = deduplicator.process_properties(properties)
            
            # Filtrar duplicados si se solicita
            if args.exclude_duplicates:
                original_count = len(properties)
                properties = deduplicator.filter_duplicates(properties)
                logger.info(f"🚫 Filtradas {original_count - len(properties)} propiedades duplicadas")
            
            # Guardar registro actualizado
            deduplicator.save_registry()
            
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
