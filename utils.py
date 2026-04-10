"""
Utilidades para el scraper
"""

import json
from typing import List, Dict
from logger_config import get_logger

logger = get_logger(__name__)


def load_properties_from_txt(filepath: str) -> List[Dict[str, str]]:
    """
    Carga propiedades desde archivo TXT (JSON-like)
    
    Args:
        filepath: Path del archivo
        
    Returns:
        Lista de propiedades
    """
    properties = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        prop = json.loads(line)
                        properties.append(prop)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Error parseando línea: {e}")
                        continue
        
        logger.info(f"Cargadas {len(properties)} propiedades desde {filepath}")
        return properties
        
    except Exception as e:
        logger.error(f"Error cargando archivo: {e}")
        raise


def load_properties_from_json(filepath: str) -> List[Dict[str, str]]:
    """
    Carga propiedades desde archivo JSON
    
    Args:
        filepath: Path del archivo
        
    Returns:
        Lista de propiedades
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        properties = data.get('propiedades', [])
        logger.info(f"Cargadas {len(properties)} propiedades desde {filepath}")
        return properties
        
    except Exception as e:
        logger.error(f"Error cargando archivo JSON: {e}")
        raise


def print_property_summary(properties: List[Dict[str, str]]) -> None:
    """
    Imprime resumen de propiedades
    
    Args:
        properties: Lista de propiedades
    """
    if not properties:
        print("No hay propiedades para mostrar")
        return
    
    print(f"\n{'=' * 80}")
    print(f"RESUMEN DE PROPIEDADES ({len(properties)} total)")
    print(f"{'=' * 80}\n")
    
    for i, prop in enumerate(properties[:10], 1):
        print(f"{i}. {prop.get('titulo', 'N/A')}")
        print(f"   Precio: ${prop.get('precio', 'N/A')}")
        print(f"   Ubicación: {prop.get('ubicacion', 'N/A')}")
        print(f"   URL: {prop.get('url', 'N/A')}")
        print()
    
    if len(properties) > 10:
        print(f"... y {len(properties) - 10} propiedades más\n")
    
    print(f"{'=' * 80}\n")


def get_price_statistics(properties: List[Dict[str, str]]) -> Dict[str, any]:
    """
    Calcula estadísticas de precios
    
    Args:
        properties: Lista de propiedades
        
    Returns:
        Diccionario con estadísticas
    """
    prices = []
    
    for prop in properties:
        precio_str = prop.get('precio', '').replace('.', '').replace(',', '')
        try:
            precio = float(precio_str)
            prices.append(precio)
        except ValueError:
            continue
    
    if not prices:
        return {
            'total': 0,
            'min': 0,
            'max': 0,
            'avg': 0
        }
    
    return {
        'total': len(prices),
        'min': min(prices),
        'max': max(prices),
        'avg': sum(prices) / len(prices)
    }
