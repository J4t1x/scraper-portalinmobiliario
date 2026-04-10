import os
import json
from datetime import datetime
from typing import List, Dict, Any
from config import Config
from logger_config import get_logger

logger = get_logger(__name__)


class DataExporter:
    """Exportador de datos a diferentes formatos"""
    
    def __init__(self):
        """Inicializa el exportador y crea directorio de salida"""
        os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
    
    def flatten_property(self, prop: Dict[str, Any]) -> Dict[str, str]:
        """
        Aplana un diccionario de propiedad con campos anidados
        para exportación CSV.
        
        Args:
            prop: Diccionario de propiedad con posibles campos anidados
            
        Returns:
            Diccionario aplanado con solo valores string
        """
        flat = {}
        
        # Campos de detalle que pueden venir del scraper de detalle
        detail_fields = ['descripcion', 'caracteristicas', 'publicador', 'imagenes', 
                        'coordenadas', 'fecha_publicacion']
        
        # Copiar campos simples
        for key, value in prop.items():
            if value is None:
                flat[key] = ""
            elif isinstance(value, dict):
                # Aplanar diccionarios anidados (caracteristicas, publicador, coordenadas)
                for sub_key, sub_value in value.items():
                    flat[f"{key}_{sub_key}"] = str(sub_value) if sub_value is not None else ""
            elif isinstance(value, list):
                # Convertir listas a string separado por pipe | para mejor compatibilidad
                flat[key] = " | ".join(str(v) for v in value) if value else ""
            else:
                flat[key] = str(value)
        
        return flat
    
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
    
    def export_to_txt(self, properties: List[Dict[str, Any]], operacion: str, tipo: str) -> str:
        """
        Exporta propiedades a archivo TXT con formato legible incluyendo detalles
        
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
                f.write("=" * 80 + "\n")
                f.write(f"PROPIEDADES - {operacion.upper()} - {tipo.upper()}\n")
                f.write(f"Total: {len(properties)} propiedades\n")
                f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + "\n\n")
                
                for i, prop in enumerate(properties, 1):
                    f.write(f"\n{'='*80}\n")
                    f.write(f"PROPIEDAD #{i}\n")
                    f.write(f"{'='*80}\n\n")
                    
                    # Información básica
                    f.write("📍 INFORMACIÓN BÁSICA\n")
                    f.write("-" * 40 + "\n")
                    basic_fields = ['titulo', 'precio', 'precio_uf', 'ubicacion', 'url', 
                                   'metros_cuadrados', 'dormitorios', 'banos', 'operacion', 'tipo']
                    for field in basic_fields:
                        value = prop.get(field, 'N/A')
                        if value and value != 'N/A':
                            f.write(f"{field.replace('_', ' ').title()}: {value}\n")
                    
                    # Detalles (si existen)
                    has_details = any(prop.get(field) for field in ['descripcion', 'caracteristicas', 
                                                                   'publicador', 'imagenes', 'coordenadas'])
                    
                    if has_details:
                        f.write(f"\n📋 DETALLES DE LA PROPIEDAD\n")
                        f.write("-" * 40 + "\n")
                        
                        # Descripción
                        descripcion = prop.get('descripcion')
                        if descripcion:
                            f.write(f"\n📝 Descripción:\n")
                            # Wrap description text
                            words = descripcion.split()
                            line = ""
                            for word in words:
                                if len(line) + len(word) + 1 <= 70:
                                    line += word + " "
                                else:
                                    f.write(f"  {line.strip()}\n")
                                    line = word + " "
                            if line:
                                f.write(f"  {line.strip()}\n")
                        
                        # Características
                        caracteristicas = prop.get('caracteristicas', {})
                        if caracteristicas:
                            f.write(f"\n🔧 Características:\n")
                            for key, value in caracteristicas.items():
                                f.write(f"  • {key.replace('_', ' ').title()}: {value}\n")
                        
                        # Publicador
                        publicador = prop.get('publicador', {})
                        if publicador:
                            f.write(f"\n👤 Publicador:\n")
                            for key, value in publicador.items():
                                if value:
                                    f.write(f"  • {key.replace('_', ' ').title()}: {value}\n")
                        
                        # Coordenadas
                        coordenadas = prop.get('coordenadas', {})
                        if coordenadas:
                            f.write(f"\n📍 Ubicación (GPS):\n")
                            if 'lat' in coordenadas:
                                f.write(f"  • Latitud: {coordenadas['lat']}\n")
                            if 'lng' in coordenadas:
                                f.write(f"  • Longitud: {coordenadas['lng']}\n")
                        
                        # Imágenes
                        imagenes = prop.get('imagenes', [])
                        if imagenes:
                            f.write(f"\n📸 Imágenes ({len(imagenes)}):\n")
                            for img_url in imagenes[:5]:  # Mostrar máximo 5
                                f.write(f"  • {img_url}\n")
                            if len(imagenes) > 5:
                                f.write(f"  ... y {len(imagenes) - 5} más\n")
                        
                        # Fecha de publicación
                        fecha = prop.get('fecha_publicacion')
                        if fecha:
                            f.write(f"\n📅 Fecha de Publicación: {fecha}\n")
                    
                    f.write("\n")
                
                # Footer
                f.write(f"\n{'='*80}\n")
                f.write("FIN DEL LISTADO\n")
                f.write(f"{'='*80}\n")
            
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
    
    def export_to_csv(self, properties: List[Dict[str, Any]], operacion: str, tipo: str, 
                      flatten_nested: bool = True) -> str:
        """
        Exporta propiedades a archivo CSV
        
        Args:
            properties: Lista de propiedades
            operacion: Tipo de operación
            tipo: Tipo de propiedad
            flatten_nested: Si es True, aplana campos anidados (dicts y lists)
            
        Returns:
            Path del archivo creado
        """
        filepath = self._generate_filename(operacion, tipo, "csv")
        
        try:
            import csv
            
            if not properties:
                logger.warning("No hay propiedades para exportar")
                return filepath
            
            # Preparar datos según el modo
            if flatten_nested:
                flat_properties = [self.flatten_property(prop) for prop in properties]
                fieldnames = flat_properties[0].keys()
                data_to_write = flat_properties
            else:
                fieldnames = properties[0].keys()
                data_to_write = properties
            
            with open(filepath, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data_to_write)
            
            logger.info(f"Exportado a CSV: {filepath} ({len(properties)} propiedades)")
            return filepath
            
        except Exception as e:
            logger.error(f"Error exportando a CSV: {e}")
            raise
