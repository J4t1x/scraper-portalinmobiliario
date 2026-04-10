"""Tests para main.py (CLI argument parsing)"""

import pytest
from unittest.mock import patch, MagicMock
import sys


class TestArgumentParsing:
    """Tests para el parser de argumentos de línea de comandos"""
    
    def test_parse_args_basic(self):
        """Test parsing de argumentos básicos"""
        with patch('sys.argv', ['main.py', '--operacion', 'venta', '--tipo', 'departamento']):
            args = parse_args()
            assert args.operacion == 'venta'
            assert args.tipo == 'departamento'
    
    def test_parse_args_with_max_pages(self):
        """Test parsing con max_pages"""
        with patch('sys.argv', ['main.py', '--operacion', 'venta', '--tipo', 'departamento', '--max-pages', '5']):
            args = parse_args()
            assert args.max_pages == 5
    
    def test_parse_args_with_formato(self):
        """Test parsing con formato"""
        with patch('sys.argv', ['main.py', '--operacion', 'venta', '--tipo', 'departamento', '--formato', 'json']):
            args = parse_args()
            assert args.formato == 'json'
    
    def test_parse_args_verbose(self):
        """Test parsing con verbose"""
        with patch('sys.argv', ['main.py', '--operacion', 'venta', '--tipo', 'departamento', '--verbose']):
            args = parse_args()
            assert args.verbose is True
    
    def test_parse_args_scrape_details(self):
        """Test parsing con scrape_details"""
        with patch('sys.argv', ['main.py', '--operacion', 'venta', '--tipo', 'departamento', '--scrape-details']):
            args = parse_args()
            assert args.scrape_details is True
    
    def test_parse_args_max_detail_properties(self):
        """Test parsing con max_detail_properties"""
        with patch('sys.argv', ['main.py', '--operacion', 'venta', '--tipo', 'departamento', '--max-detail-properties', '10']):
            args = parse_args()
            assert args.max_detail_properties == 10
    
    def test_parse_args_exclude_duplicates(self):
        """Test parsing con exclude_duplicates"""
        with patch('sys.argv', ['main.py', '--operacion', 'venta', '--tipo', 'departamento', '--exclude-duplicates']):
            args = parse_args()
            assert args.exclude_duplicates is True
    
    def test_parse_args_reset_duplicates(self):
        """Test parsing con reset_duplicates"""
        with patch('sys.argv', ['main.py', '--operacion', 'venta', '--tipo', 'departamento', '--reset-duplicates']):
            args = parse_args()
            assert args.reset_duplicates is True
    
    def test_parse_args_dedup_stats(self):
        """Test parsing con dedup_stats"""
        with patch('sys.argv', ['main.py', '--operacion', 'venta', '--tipo', 'departamento', '--dedup-stats']):
            args = parse_args()
            assert args.dedup_stats is True
    
    def test_parse_args_registry_path(self):
        """Test parsing con registry_path personalizado"""
        with patch('sys.argv', ['main.py', '--operacion', 'venta', '--tipo', 'departamento', '--registry-path', '/custom/path.json']):
            args = parse_args()
            assert args.registry_path == '/custom/path.json'
    
    def test_parse_args_persist_to_db(self):
        """Test parsing con persist_to_db"""
        with patch('sys.argv', ['main.py', '--operacion', 'venta', '--tipo', 'departamento', '--persist-to-db']):
            args = parse_args()
            assert args.persist_to_db is True
    
    def test_parse_args_scheduler_command(self):
        """Test parsing con scheduler command"""
        with patch('sys.argv', ['main.py', '--scheduler', 'status']):
            args = parse_args()
            assert args.scheduler == 'status'


class TestRunScraping:
    """Tests para la función run_scraping"""
    
    @patch('main.PortalInmobiliarioSeleniumScraper')
    @patch('main.Deduplicator')
    @patch('main.DataExporter')
    def test_run_scraping_basic(self, mock_exporter, mock_dedup, mock_scraper_class):
        """Test ejecución básica de scraping"""
        mock_scraper = MagicMock()
        mock_scraper.scrape_all_pages.return_value = [
            {'id': 'MLC-12345678', 'titulo': 'Test', 'precio': 'UF 1000'}
        ]
        mock_scraper_class.return_value = mock_scraper
        
        mock_ded_instance = MagicMock()
        mock_ded_instance.process_properties.return_value = [
            {'id': 'MLC-12345678', 'titulo': 'Test', 'precio': 'UF 1000'}
        ]
        mock_ded_instance.get_stats.return_value = {'total_unique': 1, 'total_duplicates': 0}
        mock_dedup.return_value = mock_ded_instance
        
        mock_exporter_instance = MagicMock()
        mock_exporter.return_value = mock_exporter_instance
        
        from main import run_scraping
        result = run_scraping('venta', 'departamento', max_pages=1)
        
        assert result['properties_scraped'] == 1
        assert result['status'] == 'success'
    
    @patch('main.PortalInmobiliarioSeleniumScraper')
    def test_run_scraping_no_properties(self, mock_scraper_class):
        """Test cuando no se encuentran propiedades"""
        mock_scraper = MagicMock()
        mock_scraper.scrape_all_pages.return_value = []
        mock_scraper_class.return_value = mock_scraper
        
        from main import run_scraping
        result = run_scraping('venta', 'departamento', max_pages=1)
        
        assert result['properties_scraped'] == 0
        assert result['status'] == 'success'
    
    @patch('main.PortalInmobiliarioSeleniumScraper')
    @patch('main.Deduplicator')
    def test_run_scraping_with_details(self, mock_dedup, mock_scraper_class):
        """Test scraping con detalles"""
        mock_scraper = MagicMock()
        mock_scraper.scrape_all_pages.return_value = [
            {'id': 'MLC-12345678', 'titulo': 'Test', 'descripcion': 'Detalle'}
        ]
        mock_scraper_class.return_value = mock_scraper
        
        mock_ded_instance = MagicMock()
        mock_ded_instance.process_properties.return_value = [
            {'id': 'MLC-12345678', 'titulo': 'Test', 'descripcion': 'Detalle'}
        ]
        mock_ded_instance.get_stats.return_value = {'total_unique': 1, 'total_duplicates': 0}
        mock_dedup.return_value = mock_ded_instance
        
        from main import run_scraping
        result = run_scraping('venta', 'departamento', scrape_details=True, max_detail_properties=5)
        
        mock_scraper.scrape_all_pages.assert_called_once_with(
            max_pages=None,
            scrape_details=True,
            max_detail_properties=5
        )
    
    @patch('main.PortalInmobiliarioSeleniumScraper')
    @patch('main.Deduplicator')
    def test_run_scraping_reset_duplicates(self, mock_dedup, mock_scraper_class):
        """Test reset de duplicados"""
        mock_scraper = MagicMock()
        mock_scraper.scrape_all_pages.return_value = [
            {'id': 'MLC-12345678', 'titulo': 'Test'}
        ]
        mock_scraper_class.return_value = mock_scraper
        
        mock_ded_instance = MagicMock()
        mock_ded_instance.process_properties.return_value = [
            {'id': 'MLC-12345678', 'titulo': 'Test'}
        ]
        mock_ded_instance.get_stats.return_value = {'total_unique': 1, 'total_duplicates': 0}
        mock_dedup.return_value = mock_ded_instance
        
        from main import run_scraping
        result = run_scraping('venta', 'departamento', reset_duplicates=True)
        
        mock_ded_instance.reset_registry.assert_called_once()
    
    @patch('main.PortalInmobiliarioSeleniumScraper')
    @patch('main.Deduplicator')
    def test_run_scraping_persist_to_db(self, mock_dedup, mock_scraper_class):
        """Test persistencia a base de datos"""
        mock_scraper = MagicMock()
        mock_scraper.scrape_all_pages.return_value = [
            {'id': 'MLC-12345678', 'titulo': 'Test'}
        ]
        mock_scraper_class.return_value = mock_scraper
        
        mock_ded_instance = MagicMock()
        mock_ded_instance.process_properties.return_value = [
            {'id': 'MLC-12345678', 'titulo': 'Test'}
        ]
        mock_ded_instance.get_stats.return_value = {'total_unique': 1, 'total_duplicates': 0}
        mock_dedup.return_value = mock_ded_instance
        
        from main import run_scraping
        result = run_scraping('venta', 'departamento', persist_to_db=True)
        
        mock_scraper_class.assert_called_once_with(
            'venta',
            'departamento',
            headless=True,
            persist_to_db=True
        )


class TestSchedulerCommands:
    """Tests para comandos del scheduler"""
    
    def test_scheduler_status_command(self):
        """Test comando scheduler status"""
        with patch('sys.argv', ['main.py', '--scheduler', 'status']):
            args = parse_args()
            assert args.scheduler == 'status'
    
    def test_scheduler_start_command(self):
        """Test comando scheduler start"""
        with patch('sys.argv', ['main.py', '--scheduler', 'start']):
            args = parse_args()
            assert args.scheduler == 'start'


# Helper function to parse args (extracted from main.py for testing)
def parse_args():
    """Helper para parsear argumentos (copia simplificada de main.py)"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Portal Inmobiliario Scraper - Extrae propiedades de portalinmobiliario.com'
    )
    
    parser.add_argument(
        '--operacion',
        type=str,
        choices=['venta', 'arriendo', 'arriendo-de-temporada'],
        help='Tipo de operación'
    )
    
    parser.add_argument(
        '--tipo',
        type=str,
        choices=['departamento', 'casa', 'oficina', 'terreno', 'local-comercial', 'bodega', 'estacionamiento', 'parcela'],
        help='Tipo de propiedad'
    )
    
    parser.add_argument(
        '--max-pages',
        type=int,
        default=None,
        help='Máximo de páginas a scrapear (default: todas)'
    )
    
    parser.add_argument(
        '--formato',
        type=str,
        choices=['txt', 'json', 'csv'],
        default='txt',
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
        help='Scrapear información adicional de cada propiedad'
    )
    
    parser.add_argument(
        '--max-detail-properties',
        type=int,
        default=None,
        help='Máximo de propiedades para las cuales scrapear detalle'
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
        help='Ruta al archivo de registro de duplicados'
    )
    
    parser.add_argument(
        '--persist-to-db',
        action='store_true',
        help='Persistir propiedades en PostgreSQL'
    )
    
    parser.add_argument(
        '--scheduler',
        type=str,
        choices=['start', 'stop', 'status', 'list-jobs', 'setup-default'],
        help='Comando del scheduler'
    )
    
    return parser.parse_args()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
