"""
Data validator module for validating property data before migration.

Validates required fields, data types, and value formats.
"""

import re
from typing import Dict, Tuple, List
from datetime import datetime


class DataValidator:
    """
    Validator for property data.
    
    Validates required fields, data types, and value formats
    before insertion into PostgreSQL.
    """
    
    # Required fields for basic property
    REQUIRED_FIELDS = [
        'id',
        'titulo',
        'precio',
        'ubicacion',
        'url',
        'operacion',
        'tipo'
    ]
    
    # Valid operation types
    VALID_OPERATIONS = {
        'venta',
        'arriendo',
        'arriendo-de-temporada'
    }
    
    # Valid property types
    VALID_TYPES = {
        'departamento',
        'casa',
        'oficina',
        'terreno',
        'local-comercial',
        'bodega',
        'estacionamiento',
        'parcela'
    }
    
    @staticmethod
    def validate_property(prop: Dict) -> Tuple[bool, List[str]]:
        """
        Validate a single property.
        
        Args:
            prop: Property dictionary
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check required fields
        for field in DataValidator.REQUIRED_FIELDS:
            if field not in prop or prop[field] is None:
                errors.append(f"Missing required field: {field}")
            elif not isinstance(prop[field], str) or not prop[field].strip():
                errors.append(f"Empty required field: {field}")
        
        # Validate operation type
        if 'operacion' in prop and prop['operacion']:
            if prop['operacion'] not in DataValidator.VALID_OPERATIONS:
                errors.append(
                    f"Invalid operation: {prop['operacion']}. "
                    f"Valid: {DataValidator.VALID_OPERATIONS}"
                )
        
        # Validate property type
        if 'tipo' in prop and prop['tipo']:
            if prop['tipo'] not in DataValidator.VALID_TYPES:
                errors.append(
                    f"Invalid property type: {prop['tipo']}. "
                    f"Valid: {DataValidator.VALID_TYPES}"
                )
        
        # Validate price format
        if 'precio' in prop and prop['precio']:
            if not DataValidator._is_valid_price(prop['precio']):
                errors.append(f"Invalid price format: {prop['precio']}")
        
        # Validate URL format
        if 'url' in prop and prop['url']:
            if not DataValidator._is_valid_url(prop['url']):
                errors.append(f"Invalid URL: {prop['url']}")
        
        # Validate publication date if present
        if 'fecha_publicacion' in prop and prop['fecha_publicacion']:
            if not DataValidator._is_valid_date(prop['fecha_publicacion']):
                errors.append(f"Invalid date format: {prop['fecha_publicacion']}")
        
        # Validate coordinates if present
        if 'coordenadas' in prop and prop['coordenadas']:
            if isinstance(prop['coordenadas'], dict):
                if 'lat' in prop['coordenadas'] and not DataValidator._is_valid_coordinate(
                    prop['coordenadas']['lat']
                ):
                    errors.append(f"Invalid latitude: {prop['coordenadas']['lat']}")
                if 'lng' in prop['coordenadas'] and not DataValidator._is_valid_coordinate(
                    prop['coordenadas']['lng']
                ):
                    errors.append(f"Invalid longitude: {prop['coordenadas']['lng']}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _is_valid_price(precio: str) -> bool:
        """
        Validate price format.
        
        Accepts formats like:
        - UF 3.055
        - $ 740.000
        - USD 1,200
        
        Args:
            precio: Price string
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(precio, str):
            return False
        
        patterns = [
            r'^UF\s+[\d.,]+$',      # UF format
            r'^\$\s+[\d.,]+$',      # CLP format
            r'^USD\s+[\d.,]+$',     # USD format
        ]
        
        return any(re.match(p, precio.strip()) for p in patterns)
    
    @staticmethod
    def _is_valid_url(url: str) -> bool:
        """
        Validate URL format.
        
        Args:
            url: URL string
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(url, str):
            return False
        
        # Basic URL validation
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return re.match(pattern, url) is not None
    
    @staticmethod
    def _is_valid_date(date_str: str) -> bool:
        """
        Validate date format (ISO 8601: YYYY-MM-DD).
        
        Args:
            date_str: Date string
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(date_str, str):
            return False
        
        try:
            datetime.fromisoformat(date_str)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def _is_valid_coordinate(coord) -> bool:
        """
        Validate coordinate (latitude or longitude).
        
        Args:
            coord: Coordinate value (int, float, or string)
            
        Returns:
            True if valid, False otherwise
        """
        try:
            value = float(coord)
            # Latitude: -90 to 90, Longitude: -180 to 180
            return -180 <= value <= 180
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_batch(properties: List[Dict]) -> Tuple[int, int, List[Dict]]:
        """
        Validate a batch of properties.
        
        Args:
            properties: List of property dictionaries
            
        Returns:
            Tuple of (valid_count, invalid_count, invalid_properties)
            invalid_properties is a list of dicts with property and errors
        """
        valid_count = 0
        invalid_count = 0
        invalid_properties = []
        
        for prop in properties:
            is_valid, errors = DataValidator.validate_property(prop)
            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1
                invalid_properties.append({
                    'property': prop,
                    'errors': errors
                })
        
        return valid_count, invalid_count, invalid_properties
    
    @staticmethod
    def normalize_property(prop: Dict) -> Dict:
        """
        Normalize property data for database insertion.
        
        Converts data types and formats to match database schema.
        
        Args:
            prop: Property dictionary from scraper
            
        Returns:
            Normalized property dictionary
        """
        normalized = prop.copy()
        
        # Normalize price
        if 'precio' in prop and prop['precio']:
            normalized['precio_original'] = prop['precio']
            # Parse numeric value (optional, for future use)
        
        # Parse date
        if 'fecha_publicacion' in prop and prop['fecha_publicacion']:
            try:
                normalized['fecha_publicacion'] = datetime.fromisoformat(
                    prop['fecha_publicacion']
                )
            except ValueError:
                # Keep original if parsing fails
                pass
        
        return normalized
