"""
Data Loader - Lectura de archivos JSON desde output/

Este módulo implementa la carga de datos de propiedades inmobiliarias
desde archivos JSON generados por el scraper, con soporte para filtros,
estadísticas y paginación.
"""

from pathlib import Path
import json
import re
from typing import List, Dict, Optional
from datetime import datetime
from logger_config import get_logger

logger = get_logger(__name__)


class JSONDataLoader:
    """Cargador de datos desde archivos JSON de propiedades inmobiliarias"""
    
    def __init__(self, output_dir: str = 'output'):
        """
        Inicializa el cargador de datos.

        Args:
            output_dir: Directorio donde se encuentran los archivos JSON

        Raises:
            FileNotFoundError: Si el directorio no existe
        """
        self.output_dir = Path(output_dir)
        if not self.output_dir.exists():
            raise FileNotFoundError(f"Directorio {output_dir} no existe")
        logger.info(f"DataLoader inicializado con directorio: {output_dir}")

    def list_json_files(self) -> List[Dict]:
        """
        Listar todos los archivos JSON disponibles con metadata.

        Returns:
            Lista de diccionarios con información de cada archivo:
            - filename: Nombre del archivo
            - filepath: Ruta completa del archivo
            - size: Tamaño en bytes
            - modified: Fecha de modificación
            - metadata: Metadata del archivo (operacion, tipo, total, fecha_scraping)
        """
        files_info = []

        for json_file in sorted(self.output_dir.glob('*.json'), reverse=True):
            try:
                # Obtener metadata básica del archivo
                stat = json_file.stat()
                modified = datetime.fromtimestamp(stat.st_mtime)

                # Leer metadata del JSON
                metadata = {}
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        metadata = data.get('metadata', {})
                except json.JSONDecodeError:
                    logger.warning(f"Error parseando metadata de {json_file.name}")

                files_info.append({
                    'filename': json_file.name,
                    'filepath': str(json_file),
                    'size': stat.st_size,
                    'modified': modified.isoformat(),
                    'metadata': metadata
                })
            except Exception as e:
                logger.warning(f"Error leyendo info de {json_file.name}: {e}")

        logger.info(f"Encontrados {len(files_info)} archivos JSON")
        return files_info

    def get_latest_json_file(self) -> Optional[Dict]:
        """
        Obtener el archivo JSON más reciente.

        Returns:
            Diccionario con información del archivo más reciente o None si no hay archivos
        """
        files = self.list_json_files()
        if files:
            return files[0]  # Ya están ordenados por fecha descendente
        return None
    
    def load_specific_json_file(self, filename: str) -> List[Dict]:
        """
        Cargar propiedades de un archivo JSON específico.

        Args:
            filename: Nombre del archivo JSON a cargar

        Returns:
            Lista de propiedades del archivo especificado

        Raises:
            FileNotFoundError: Si el archivo no existe
            json.JSONDecodeError: Si el archivo JSON es inválido
        """
        json_file = self.output_dir / filename

        if not json_file.exists():
            raise FileNotFoundError(f"Archivo {filename} no existe en {self.output_dir}")

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                properties = data.get('propiedades', [])
                logger.info(f"Cargado {filename}: {len(properties)} propiedades")
                return properties
        except json.JSONDecodeError as e:
            logger.error(f"Error parseando {filename}: {e}")
            raise

    def load_all_json_files(self) -> List[Dict]:
        """
        Cargar todos los archivos JSON del directorio output/.

        Returns:
            Lista de todas las propiedades combinadas de todos los archivos JSON

        Raises:
            json.JSONDecodeError: Si un archivo JSON es inválido (logged y continúa)
        """
        all_properties = []
        files_loaded = 0
        files_error = 0

        for json_file in self.output_dir.glob('*.json'):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    properties = data.get('propiedades', [])
                    all_properties.extend(properties)
                    files_loaded += 1
                    logger.debug(f"Cargado {json_file.name}: {len(properties)} propiedades")
            except json.JSONDecodeError as e:
                files_error += 1
                logger.warning(f"Error parseando {json_file.name}: {e}")
            except Exception as e:
                files_error += 1
                logger.warning(f"Error leyendo {json_file.name}: {e}")

        logger.info(f"Cargados {len(all_properties)} propiedades de {files_loaded} archivos ({files_error} errores)")
        return all_properties
    
    def load_by_filters(
        self,
        operacion: Optional[str] = None,
        tipo: Optional[str] = None,
        precio_min: Optional[float] = None,
        precio_max: Optional[float] = None,
        search: Optional[str] = None
    ) -> List[Dict]:
        """
        Cargar propiedades con filtros aplicados.
        
        Args:
            operacion: Filtrar por operación (venta, arriendo, arriendo-de-temporada)
            tipo: Filtrar por tipo (departamento, casa, oficina, etc.)
            precio_min: Precio mínimo en CLP
            precio_max: Precio máximo en CLP
            search: Búsqueda por texto en título y ubicación
            
        Returns:
            Lista de propiedades filtradas
        """
        all_properties = self.load_all_json_files()
        
        if not all_properties:
            logger.warning("No se encontraron propiedades para filtrar")
            return []
        
        filtered = []
        
        for prop in all_properties:
            # Filtro por operación
            if operacion and prop.get('operacion') != operacion:
                continue
            
            # Filtro por tipo
            if tipo and prop.get('tipo') != tipo:
                continue
            
            # Filtro por rango de precio (solo para precios en CLP)
            precio_clp = self._extract_price_clp(prop.get('precio', ''))
            # Si estamos filtrando por precio y la propiedad está en UF, excluirla
            if (precio_min is not None or precio_max is not None) and precio_clp is None:
                continue
            if precio_min is not None and precio_clp < precio_min:
                continue
            if precio_max is not None and precio_clp > precio_max:
                continue
            
            # Búsqueda por texto
            if search:
                search_lower = search.lower()
                titulo = prop.get('titulo', '').lower()
                ubicacion = prop.get('ubicacion', '').lower()
                if search_lower not in titulo and search_lower not in ubicacion:
                    continue
            
            filtered.append(prop)
        
        logger.info(f"Filtradas {len(filtered)} propiedades (de {len(all_properties)} totales)")
        return filtered
    
    def get_stats(self) -> Dict:
        """
        Obtener estadísticas de los datos cargados.
        
        Returns:
            Diccionario con estadísticas:
            - total: Total de propiedades
            - by_operacion: Distribución por operación
            - by_tipo: Distribución por tipo
            - files_loaded: Cantidad de archivos JSON procesados
        """
        all_properties = self.load_all_json_files()
        
        stats = {
            'total': len(all_properties),
            'by_operacion': {},
            'by_tipo': {},
            'files_loaded': len(list(self.output_dir.glob('*.json')))
        }
        
        # Calcular distribución por operación
        for prop in all_properties:
            operacion = prop.get('operacion', 'desconocido')
            stats['by_operacion'][operacion] = stats['by_operacion'].get(operacion, 0) + 1
            
            tipo = prop.get('tipo', 'desconocido')
            stats['by_tipo'][tipo] = stats['by_tipo'].get(tipo, 0) + 1
        
        logger.info(f"Estadísticas: {stats['total']} propiedades, {stats['files_loaded']} archivos")
        return stats
    
    def paginate(
        self,
        properties: List[Dict],
        page: int = 1,
        per_page: int = 20
    ) -> Dict:
        """
        Paginar resultados de propiedades.
        
        Args:
            properties: Lista de propiedades a paginar
            page: Número de página (1-indexed)
            per_page: Cantidad de propiedades por página
            
        Returns:
            Diccionario con:
            - data: Propiedades de la página actual
            - page: Página actual
            - per_page: Propiedades por página
            - total: Total de propiedades
            - total_pages: Total de páginas
            - has_next: Hay página siguiente
            - has_prev: Hay página anterior
        """
        total = len(properties)
        total_pages = (total + per_page - 1) // per_page
        
        # Validar página
        if page < 1:
            page = 1
        if page > total_pages:
            page = total_pages
        
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        page_data = properties[start_idx:end_idx]
        
        result = {
            'data': page_data,
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
        
        logger.debug(f"Paginación: página {page}/{total_pages}, {len(page_data)} propiedades")
        return result
    
    def get_advanced_stats(self) -> Dict:
        """
        Obtener estadísticas avanzadas con KPIs adicionales.
        
        Returns:
            Diccionario con estadísticas avanzadas:
            - basic: Estadísticas básicas (total, by_operacion, by_tipo, files_loaded)
            - prices: Estadísticas de precios (avg, min, max, by_operacion, by_tipo)
            - completeness: Métricas de completitud de datos
            - temporal: Distribución temporal de scraping
            - publishers: Top publicadores
            - by_comuna: Distribución por comuna
            - price_ranges: Distribución por rangos de precio
        """
        all_properties = self.load_all_json_files()
        
        stats = {
            'basic': {
                'total': len(all_properties),
                'by_operacion': {},
                'by_tipo': {},
                'files_loaded': len(list(self.output_dir.glob('*.json')))
            },
            'prices': self._calculate_price_stats(all_properties),
            'completeness': self._calculate_completeness(all_properties),
            'temporal': self._calculate_temporal_distribution(all_properties),
            'publishers': self._calculate_top_publishers(all_properties),
            'by_comuna': {},
            'price_ranges': self._calculate_price_ranges(all_properties)
        }
        
        # Calcular distribución por operación y tipo
        for prop in all_properties:
            operacion = prop.get('operacion', 'desconocido')
            stats['basic']['by_operacion'][operacion] = stats['basic']['by_operacion'].get(operacion, 0) + 1
            
            tipo = prop.get('tipo', 'desconocido')
            stats['basic']['by_tipo'][tipo] = stats['basic']['by_tipo'].get(tipo, 0) + 1
            
            comuna = prop.get('ubicacion', prop.get('comuna', 'desconocido'))
            stats['by_comuna'][comuna] = stats['by_comuna'].get(comuna, 0) + 1
        
        logger.info(f"Estadísticas avanzadas: {stats['basic']['total']} propiedades")
        return stats
    
    def _calculate_price_stats(self, properties: List[Dict]) -> Dict:
        """Calcular estadísticas de precios."""
        prices_clp = []
        prices_by_operacion = {}
        prices_by_tipo = {}
        
        for prop in properties:
            price_clp = self._extract_price_clp(prop.get('precio', ''))
            if price_clp:
                prices_clp.append(price_clp)
                
                # Por operación
                operacion = prop.get('operacion', 'desconocido')
                if operacion not in prices_by_operacion:
                    prices_by_operacion[operacion] = []
                prices_by_operacion[operacion].append(price_clp)
                
                # Por tipo
                tipo = prop.get('tipo', 'desconocido')
                if tipo not in prices_by_tipo:
                    prices_by_tipo[tipo] = []
                prices_by_tipo[tipo].append(price_clp)
        
        if not prices_clp:
            return {
                'avg': 0,
                'min': 0,
                'max': 0,
                'median': 0,
                'by_operacion': {},
                'by_tipo': {},
                'total_with_price': 0
            }
        
        prices_clp.sort()
        median_idx = len(prices_clp) // 2
        
        return {
            'avg': sum(prices_clp) / len(prices_clp),
            'min': min(prices_clp),
            'max': max(prices_clp),
            'median': prices_clp[median_idx],
            'by_operacion': {op: sum(prices) / len(prices) for op, prices in prices_by_operacion.items()},
            'by_tipo': {tipo: sum(prices) / len(prices) for tipo, prices in prices_by_tipo.items()},
            'total_with_price': len(prices_clp)
        }
    
    def _calculate_completeness(self, properties: List[Dict]) -> Dict:
        """Calcular métricas de completitud de datos."""
        total = len(properties)
        if total == 0:
            return {'overall': 0, 'fields': {}}
        
        fields_to_check = [
            'titulo', 'precio', 'ubicacion', 'descripcion',
            'features', 'imagenes', 'publisher', 'coordenadas'
        ]
        
        field_completeness = {}
        for field in fields_to_check:
            count = sum(1 for prop in properties if prop.get(field))
            field_completeness[field] = (count / total) * 100
        
        overall = sum(field_completeness.values()) / len(fields_to_check)
        
        return {
            'overall': overall,
            'fields': field_completeness,
            'with_images': sum(1 for prop in properties if prop.get('imagenes')),
            'with_description': sum(1 for prop in properties if prop.get('descripcion')),
            'with_coordinates': sum(1 for prop in properties if prop.get('coordenadas'))
        }
    
    def _calculate_temporal_distribution(self, properties: List[Dict]) -> Dict:
        """Calcular distribución temporal de scraping."""
        by_date = {}
        
        for prop in properties:
            date_str = prop.get('scrapeado_en', prop.get('fecha_scraping'))
            if date_str:
                try:
                    # Extraer solo la fecha (YYYY-MM-DD)
                    date_only = date_str.split('T')[0] if 'T' in date_str else date_str.split(' ')[0]
                    by_date[date_only] = by_date.get(date_only, 0) + 1
                except Exception:
                    pass
        
        # Ordenar por fecha
        sorted_dates = sorted(by_date.items())
        
        return {
            'by_date': dict(sorted_dates),
            'total_dates': len(by_date),
            'latest_date': sorted_dates[-1][0] if sorted_dates else None,
            'oldest_date': sorted_dates[0][0] if sorted_dates else None
        }
    
    def _calculate_top_publishers(self, properties: List[Dict], limit: int = 10) -> Dict:
        """Calcular top publicadores."""
        publishers = {}
        
        for prop in properties:
            publisher = prop.get('publisher')
            if publisher:
                if isinstance(publisher, dict):
                    name = publisher.get('nombre', 'Desconocido')
                else:
                    name = str(publisher)
                publishers[name] = publishers.get(name, 0) + 1
        
        # Ordenar y limitar
        sorted_publishers = sorted(publishers.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        return {
            'top': dict(sorted_publishers),
            'total_publishers': len(publishers),
            'total_with_publisher': sum(publishers.values())
        }
    
    def _calculate_price_ranges(self, properties: List[Dict]) -> Dict:
        """Calcular distribución por rangos de precio."""
        ranges = {
            '0-50M': 0,
            '50M-100M': 0,
            '100M-150M': 0,
            '150M-200M': 0,
            '200M+': 0
        }
        
        for prop in properties:
            price_clp = self._extract_price_clp(prop.get('precio', ''))
            if price_clp:
                if price_clp < 50_000_000:
                    ranges['0-50M'] += 1
                elif price_clp < 100_000_000:
                    ranges['50M-100M'] += 1
                elif price_clp < 150_000_000:
                    ranges['100M-150M'] += 1
                elif price_clp < 200_000_000:
                    ranges['150M-200M'] += 1
                else:
                    ranges['200M+'] += 1
        
        return ranges
    
    def _extract_price_clp(self, price_str: str) -> Optional[float]:
        """
        Extraer precio en CLP desde un string de precio.
        
        Args:
            price_str: String de precio (ej: "UF 3.000", "$ 150.000.000")
            
        Returns:
            Precio en CLP o None si no se puede convertir
        """
        if not price_str:
            return None
        
        # Si es en UF, no convertir (requiere tasa de cambio)
        if 'UF' in price_str.upper():
            return None
        
        # Extraer números del string
        price_clean = re.sub(r'[^\d]', '', price_str)
        
        if not price_clean:
            return None
        
        try:
            return float(price_clean)
        except ValueError:
            return None
