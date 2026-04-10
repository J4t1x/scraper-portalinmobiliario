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
