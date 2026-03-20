import os
import json
from datetime import datetime
from typing import List, Dict
from config import Config
import logging

logger = logging.getLogger(__name__)


class DataExporter:
    """Exportador de datos a diferentes formatos"""
    
    def __init__(self):
        """Inicializa el exportador y crea directorio de salida"""
        os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
    
    def _generate_filename(self, operacion: str, tipo: str, extension: str) -> str:
        """
        Genera nombre de archivo con timestamp
        
        Args:
            operacion: Tipo de operación
            tipo: Tipo de propiedad
            extension: Extensión del archivo
            
        Returns:
            Nombre de archivo completo
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{operacion}_{tipo}_{timestamp}.{extension}"
        return os.path.join(Config.OUTPUT_DIR, filename)
    
    def export_to_txt(self, properties: List[Dict[str, str]], operacion: str, tipo: str) -> str:
        """
        Exporta propiedades a archivo TXT (JSON-like, una por línea)
        
        Args:
            properties: Lista de propiedades
            operacion: Tipo de operación
            tipo: Tipo de propiedad
            
        Returns:
            Path del archivo creado
        """
        filepath = self._generate_filename(operacion, tipo, "txt")
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                for prop in properties:
                    f.write(json.dumps(prop, ensure_ascii=False) + '\n')
            
            logger.info(f"Exportado a TXT: {filepath} ({len(properties)} propiedades)")
            return filepath
            
        except Exception as e:
            logger.error(f"Error exportando a TXT: {e}")
            raise
    
    def export_to_json(self, properties: List[Dict[str, str]], operacion: str, tipo: str) -> str:
        """
        Exporta propiedades a archivo JSON
        
        Args:
            properties: Lista de propiedades
            operacion: Tipo de operación
            tipo: Tipo de propiedad
            
        Returns:
            Path del archivo creado
        """
        filepath = self._generate_filename(operacion, tipo, "json")
        
        try:
            data = {
                "metadata": {
                    "operacion": operacion,
                    "tipo": tipo,
                    "total": len(properties),
                    "fecha_scraping": datetime.now().isoformat()
                },
                "propiedades": properties
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Exportado a JSON: {filepath} ({len(properties)} propiedades)")
            return filepath
            
        except Exception as e:
            logger.error(f"Error exportando a JSON: {e}")
            raise
    
    def export_to_csv(self, properties: List[Dict[str, str]], operacion: str, tipo: str) -> str:
        """
        Exporta propiedades a archivo CSV
        
        Args:
            properties: Lista de propiedades
            operacion: Tipo de operación
            tipo: Tipo de propiedad
            
        Returns:
            Path del archivo creado
        """
        filepath = self._generate_filename(operacion, tipo, "csv")
        
        try:
            import csv
            
            if not properties:
                logger.warning("No hay propiedades para exportar")
                return filepath
            
            fieldnames = properties[0].keys()
            
            with open(filepath, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(properties)
            
            logger.info(f"Exportado a CSV: {filepath} ({len(properties)} propiedades)")
            return filepath
            
        except Exception as e:
            logger.error(f"Error exportando a CSV: {e}")
            raise
