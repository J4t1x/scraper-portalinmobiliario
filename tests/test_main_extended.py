"""Extended tests for main.py to increase coverage from 19% to > 80%"""

import pytest
from unittest.mock import patch, MagicMock, mock_open
import sys


class TestMainFunctions:
    """Tests para funciones principales de main.py"""
    
    @patch('main.PortalInmobiliarioSeleniumScraper')
    @patch('main.Deduplicator')
    @patch('main.DataExporter')
    @patch('main.logger')
    def test_run_scraping_export_txt(self, mock_logger, mock_exporter, mock_dedup, mock_scraper_class):
        """Test exportación a formato TXT"""
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
        result = run_scraping('venta', 'departamento', formato='txt')
        
        assert result['properties_scraped'] == 1
        mock_exporter_instance.export_to_txt.assert_called_once()
    
    @patch('main.PortalInmobiliarioSeleniumScraper')
    @patch('main.Deduplicator')
    @patch('main.DataExporter')
    @patch('main.logger')
    def test_run_scraping_export_json(self, mock_logger, mock_exporter, mock_dedup, mock_scraper_class):
        """Test exportación a formato JSON"""
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
        result = run_scraping('venta', 'departamento', formato='json')
        
        assert result['properties_scraped'] == 1
        mock_exporter_instance.export_to_json.assert_called_once()
    
    @patch('main.PortalInmobiliarioSeleniumScraper')
    @patch('main.Deduplicator')
    @patch('main.DataExporter')
    @patch('main.logger')
    def test_run_scraping_export_csv(self, mock_logger, mock_exporter, mock_dedup, mock_scraper_class):
        """Test exportación a formato CSV"""
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
        result = run_scraping('venta', 'departamento', formato='csv')
        
        assert result['properties_scraped'] == 1
        mock_exporter_instance.export_to_csv.assert_called_once()
    
    @patch('main.PortalInmobiliarioSeleniumScraper')
    @patch('main.Deduplicator')
    @patch('main.DataExporter')
    @patch('main.logger')
    def test_run_scraping_with_verbose(self, mock_logger, mock_exporter, mock_dedup, mock_scraper_class):
        """Test modo verbose"""
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
        result = run_scraping('venta', 'departamento', verbose=True)
        
        assert result['properties_scraped'] == 1
    
    @patch('main.PortalInmobiliarioSeleniumScraper')
    @patch('main.Deduplicator')
    @patch('main.DataExporter')
    @patch('main.logger')
    def test_run_scraping_exclude_duplicates(self, mock_logger, mock_exporter, mock_dedup, mock_scraper_class):
        """Test exclude_duplicates"""
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
        mock_ded_instance.filter_duplicates.return_value = [
            {'id': 'MLC-12345678', 'titulo': 'Test'}
        ]
        mock_dedup.return_value = mock_ded_instance
        
        mock_exporter_instance = MagicMock()
        mock_exporter.return_value = mock_exporter_instance
        
        from main import run_scraping
        result = run_scraping('venta', 'departamento', exclude_duplicates=True)
        
        assert result['properties_scraped'] == 1
    
    @patch('main.PortalInmobiliarioSeleniumScraper')
    @patch('main.Deduplicator')
    @patch('main.DataExporter')
    @patch('main.logger')
    def test_run_scraping_custom_registry_path(self, mock_logger, mock_exporter, mock_dedup, mock_scraper_class):
        """Test custom registry path"""
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
        result = run_scraping('venta', 'departamento', registry_path='/custom/path.json')
        
        assert result['properties_scraped'] == 1
        mock_dedup.assert_called_once_with('/custom/path.json')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
