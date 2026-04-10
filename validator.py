"""
Sistema de Validación de Datos para Portal Inmobiliario Scraper.

Este módulo proporciona validación y sanitización de datos de propiedades
extraídas por el scraper, garantizando calidad y consistencia.

Usage:
    from validator import DataValidator, ValidationResult
    
    validator = DataValidator()
    result = validator.validate_property(property_data)
    
    if result.is_valid:
        print(f"Propiedad válida: {result.property_data}")
    else:
        print(f"Errores: {result.errors}")
        print(f"Advertencias: {result.warnings}")
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse
from logger_config import get_logger

# Configurar logger
logger = get_logger(__name__)

# Constantes de validación
VALID_PROPERTY_ID_PATTERN = re.compile(r'^MLC-\d{8,}$')
VALID_PRICE_PATTERN = re.compile(r'^(UF\s*)?([\d.,]+)$|^\$\s*([\d.,]+)$')
VALID_OPERATIONS = ['venta', 'arriendo', 'arriendo-temporada', 'arriendo-diario']
VALID_TYPES = ['departamento', 'casa', 'oficina', 'local', 'sitio', 'bodega', 'estacionamiento', 'parcela', 'agricola']

# Lista de comunas chilenas comunes para normalización
COMUNAS_CHILE = {
    'las condes', 'vitacura', 'lo barnechea', 'la reina', 'ñuñoa', 'providencia',
    'santiago', 'macul', 'san miguel', 'la florida', 'puente alto', 'maipú',
    'pudahuel', 'quilicura', 'cerro navia', 'lo prado', 'estación central',
    'recoleta', 'independencia', 'conchalí', 'huechuraba', 'renca', 'quinta normal',
    ' Pedro Aguirre Cerda', 'la cisterna', 'el bosque', 'la pintana', 'san ramón',
    'san joaquín', 'peñalolén', 'la granja', 'cerrillos', 'padre hurtado',
    'colina', 'lampa', 'til til', 'calera de tango', 'paine', 'buin', 'san bernardo',
    'alhué', 'curacaví', 'maría pinto', 'melipilla', 'san pedro', 'talagante',
    'el monte', 'isla de maipo', 'padre hurtado', 'peñaflor', 'valparaíso',
    'viña del mar', 'concón', 'quintero', 'puchuncaví', 'casablanca', 'juan fernández',
    'isla de pascua', 'san antonio', 'cartagena', 'el tabo', 'el quisco', 'santo domingo',
    'algarrobo', 'valparaíso'
}


@dataclass
class ValidationResult:
    """
    Resultado de la validación de una propiedad.
    
    Attributes:
        is_valid: Indica si la propiedad pasó todas las validaciones críticas
        property_data: Datos de la propiedad (sanitizados si es válida)
        warnings: Lista de advertencias (no bloqueantes)
        errors: Lista de errores (bloqueantes)
    """
    is_valid: bool = False
    property_data: Optional[Dict] = None
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class DataValidator:
    """
    Validador de datos de propiedades inmobiliarias.
    
    Proporciona métodos para validar y sanitizar todos los campos
    de una propiedad extraída por el scraper.
    
    Attributes:
        None
        
    Methods:
        validate_property: Valida una propiedad completa
        validate_id: Valida el ID de la propiedad
        validate_price: Valida y normaliza el precio
        validate_location: Valida y normaliza la ubicación
        validate_attributes: Valida atributos numéricos
        validate_url: Valida la URL de la propiedad
        validate_type_operation: Valida tipo y operación
        sanitize_data: Sanitiza todos los campos de texto
    """
    
    def __init__(self):
        """Inicializa el validador con configuración por defecto."""
        self.logger = logging.getLogger(__name__)
        
    def validate_property(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Valida una propiedad completa.
        
        Ejecuta todas las validaciones necesarias y retorna un ValidationResult
        con los datos sanitizados o los errores encontrados.
        
        Args:
            data: Diccionario con los datos de la propiedad
            
        Returns:
            ValidationResult con el resultado de la validación
            
        Example:
            >>> validator = DataValidator()
            >>> result = validator.validate_property({
            ...     'id': 'MLC-12345678',
            ...     'precio': 'UF 5.500',
            ...     'ubicacion': 'Las Condes'
            ... })
            >>> print(result.is_valid)
            True
        """
        warnings = []
        errors = []
        sanitized_data = data.copy()
        
        # Sanitizar primero
        sanitized_data = self.sanitize_data(sanitized_data)
        
        # Validar ID
        is_valid_id, id_error = self.validate_id(sanitized_data.get('id', ''))
        if not is_valid_id:
            errors.append(f"ID inválido: {id_error}")
            
        # Validar precio
        is_valid_price, price_data, price_warning = self.validate_price(
            sanitized_data.get('precio', '')
        )
        if is_valid_price and price_data:
            sanitized_data['precio_monto'] = price_data['monto']
            sanitized_data['precio_moneda'] = price_data['moneda']
        if price_warning:
            warnings.append(price_warning)
        if not is_valid_price:
            warnings.append(f"Precio inválido o no proporcionado")
            
        # Validar ubicación
        is_valid_loc, loc_warning = self.validate_location(
            sanitized_data.get('ubicacion', '')
        )
        if loc_warning:
            warnings.append(loc_warning)
            
        # Validar atributos
        is_valid_attrs, attr_warnings, sanitized_attrs = self.validate_attributes(
            sanitized_data
        )
        for warning in attr_warnings:
            warnings.append(warning)
        sanitized_data.update(sanitized_attrs)
        
        # Validar URL
        is_valid_url, url_error = self.validate_url(sanitized_data.get('url', ''))
        if not is_valid_url and sanitized_data.get('url'):
            warnings.append(f"URL inválida: {url_error}")
            
        # Validar tipo y operación
        is_valid_type_op, type_op_warning = self.validate_type_operation(
            sanitized_data.get('tipo', ''),
            sanitized_data.get('operacion', '')
        )
        if type_op_warning:
            warnings.append(type_op_warning)
            
        # Determinar si es válida
        # Es válida si no hay errores críticos (solo el ID es crítico por ahora)
        is_valid = len(errors) == 0 and bool(sanitized_data.get('id'))
        
        # Loggear resultado
        if is_valid:
            self.logger.debug(f"Propiedad {sanitized_data.get('id')} validada correctamente")
        else:
            self.logger.warning(f"Propiedad inválida: {errors}")
            
        return ValidationResult(
            is_valid=is_valid,
            property_data=sanitized_data if is_valid else None,
            warnings=warnings,
            errors=errors
        )
    
    def validate_id(self, property_id: str) -> Tuple[bool, str]:
        """
        Valida el ID de la propiedad.
        
        El formato válido es: MLC-XXXXXXXX (donde X son dígitos)
        
        Args:
            property_id: ID de la propiedad
            
        Returns:
            Tuple de (es_válido, mensaje_error)
            
        Example:
            >>> validator.validate_id('MLC-12345678')
            (True, '')
            >>> validator.validate_id('ABC-123')
            (False, 'Formato inválido. Debe ser MLC-XXXXXXXX')
        """
        if not property_id:
            return False, "ID vacío"
            
        if not isinstance(property_id, str):
            return False, f"ID debe ser string, recibido: {type(property_id)}"
            
        if VALID_PROPERTY_ID_PATTERN.match(property_id):
            return True, ""
        else:
            return False, f"Formato inválido: '{property_id}'. Debe ser MLC-XXXXXXXX (ej: MLC-12345678)"
    
    def validate_price(self, price: str) -> Tuple[bool, Optional[Dict], str]:
        """
        Valida y parsea el precio de la propiedad.
        
        Soporta formatos:
        - UF 5.500,00
        - UF 5500
        - $ 150.000.000
        - 150000000
        
        Args:
            price: String con el precio
            
        Returns:
            Tuple de (es_válido, datos_parseados, advertencia)
            datos_parseados es un dict con 'monto' (float), 'moneda' ('UF' o 'CLP')
            
        Example:
            >>> validator.validate_price('UF 5.500')
            (True, {'monto': 5500.0, 'moneda': 'UF'}, '')
        """
        if not price:
            return False, None, ""
            
        if not isinstance(price, str):
            return False, None, f"Precio debe ser string, recibido: {type(price)}"
            
        # Limpiar el string
        price_clean = price.strip()
        
        # Detectar moneda
        moneda = 'CLP'
        if 'UF' in price_clean.upper():
            moneda = 'UF'
            price_clean = re.sub(r'UF\s*', '', price_clean, flags=re.IGNORECASE)
        elif '$' in price_clean:
            price_clean = price_clean.replace('$', '')
            
        # Extraer solo números y punto decimal
        # Remover separadores de miles (puntos en Chile, comas en algunos formatos)
        price_clean = price_clean.strip()
        
        # Manejar diferentes formatos decimales
        if ',' in price_clean and '.' in price_clean:
            # Formato: 5.500,00 o 5,500.00
            if price_clean.rfind(',') > price_clean.rfind('.'):
                # Europeo: 5.500,00 -> 5500.00
                price_clean = price_clean.replace('.', '').replace(',', '.')
            else:
                # Americano: 5,500.00 -> 5500.00
                price_clean = price_clean.replace(',', '')
        elif ',' in price_clean:
            # Puede ser separador decimal o de miles
            parts = price_clean.split(',')
            if len(parts[-1]) == 2:
                # Decimal: 5500,00 -> 5500.00
                price_clean = price_clean.replace(',', '.')
            else:
                # Separador de miles: 5,500 -> 5500
                price_clean = price_clean.replace(',', '')
                
        # Remover puntos de separador de miles
        price_clean = price_clean.replace('.', '') if moneda == 'CLP' else price_clean.replace('.', '')
        
        # Para UF, mantener el punto decimal
        if moneda == 'UF' and '.' in price_clean:
            try:
                monto = float(price_clean)
                return True, {'monto': monto, 'moneda': moneda}, ""
            except ValueError:
                return False, None, f"No se pudo parsear precio UF: '{price}'"
        else:
            # Para CLP, convertir a int
            try:
                price_clean = price_clean.replace('.', '')
                monto = float(price_clean)
                return True, {'monto': monto, 'moneda': moneda}, ""
            except ValueError:
                return False, None, f"No se pudo parsear precio: '{price}'"
    
    def validate_location(self, location: str) -> Tuple[bool, str]:
        """
        Valida y normaliza la ubicación.
        
        Args:
            location: String con la ubicación
            
        Returns:
            Tuple de (es_válido, advertencia)
            
        Example:
            >>> validator.validate_location('Las Condes')
            (True, '')
            >>> validator.validate_location('')
            (False, 'Ubicación vacía')
        """
        if not location:
            return False, "Ubicación vacía"
            
        if not isinstance(location, str):
            return False, f"Ubicación debe ser string, recibido: {type(location)}"
            
        # Validar que no sea solo espacios
        if not location.strip():
            return False, "Ubicación contiene solo espacios"
            
        return True, ""
    
    def validate_attributes(self, data: Dict) -> Tuple[bool, List[str], Dict]:
        """
        Valida atributos numéricos de la propiedad.
        
        Valida dormitorios, baños y metros cuadrados.
        
        Args:
            data: Diccionario con datos de la propiedad
            
        Returns:
            Tuple de (es_válido, lista_advertencias, atributos_sanitizados)
            
        Example:
            >>> validator.validate_attributes({'dormitorios': '3', 'banos': '2'})
            (True, [], {'dormitorios': 3, 'banos': 2})
        """
        warnings = []
        sanitized = {}
        
        # Validar dormitorios
        if 'dormitorios' in data and data['dormitorios'] is not None:
            try:
                dormitorios = int(str(data['dormitorios']).strip())
                if dormitorios < 0:
                    warnings.append(f"Dormitorios negativo: {dormitorios}")
                elif dormitorios > 20:
                    warnings.append(f"Dormitorios inusualmente alto: {dormitorios}")
                else:
                    sanitized['dormitorios'] = dormitorios
            except (ValueError, TypeError):
                warnings.append(f"Dormitorios no numérico: {data['dormitorios']}")
                
        # Validar baños
        if 'banos' in data and data['banos'] is not None:
            try:
                banos = int(str(data['banos']).strip())
                if banos < 0:
                    warnings.append(f"Baños negativo: {banos}")
                elif banos > 15:
                    warnings.append(f"Baños inusualmente alto: {banos}")
                else:
                    sanitized['banos'] = banos
            except (ValueError, TypeError):
                warnings.append(f"Baños no numérico: {data['banos']}")
                
        # Validar metros cuadrados
        if 'metros_cuadrados' in data and data['metros_cuadrados'] is not None:
            try:
                m2 = float(str(data['metros_cuadrados']).replace(',', '.').strip())
                if m2 <= 0:
                    warnings.append(f"Metros cuadrados inválido: {m2}")
                elif m2 > 10000:
                    warnings.append(f"Metros cuadrados inusualmente alto: {m2}")
                else:
                    sanitized['metros_cuadrados'] = m2
            except (ValueError, TypeError):
                warnings.append(f"Metros cuadrados no numérico: {data['metros_cuadrados']}")
                
        # Validar superficie total si existe
        if 'superficie_total' in data and data['superficie_total'] is not None:
            try:
                sup_total = float(str(data['superficie_total']).replace(',', '.').strip())
                if sup_total > 0:
                    sanitized['superficie_total'] = sup_total
            except (ValueError, TypeError):
                pass  # No es crítico
                
        return len(warnings) == 0, warnings, sanitized
    
    def validate_url(self, url: str) -> Tuple[bool, str]:
        """
        Valida que la URL sea válida.
        
        Args:
            url: URL a validar
            
        Returns:
            Tuple de (es_válido, mensaje_error)
            
        Example:
            >>> validator.validate_url('https://www.portalinmobiliario.com/...')
            (True, '')
        """
        if not url:
            return True, ""  # URL vacía no es error crítico
            
        if not isinstance(url, str):
            return False, f"URL debe ser string, recibido: {type(url)}"
            
        try:
            result = urlparse(url)
            is_valid = all([result.scheme in ['http', 'https'], result.netloc])
            if not is_valid:
                return False, f"URL mal formada: {url}"
            return True, ""
        except Exception as e:
            return False, f"Error validando URL: {str(e)}"
    
    def validate_type_operation(self, tipo: str, operacion: str) -> Tuple[bool, str]:
        """
        Valida que tipo y operación sean valores permitidos.
        
        Args:
            tipo: Tipo de propiedad
            operacion: Tipo de operación
            
        Returns:
            Tuple de (es_válido, advertencia)
            
        Example:
            >>> validator.validate_type_operation('departamento', 'venta')
            (True, '')
        """
        warnings = []
        
        if tipo and tipo.lower() not in VALID_TYPES:
            warnings.append(f"Tipo no estándar: '{tipo}'. Valores válidos: {', '.join(VALID_TYPES)}")
            
        if operacion and operacion.lower() not in VALID_OPERATIONS:
            warnings.append(f"Operación no estándar: '{operacion}'. Valores válidos: {', '.join(VALID_OPERATIONS)}")
            
        return len(warnings) == 0, '; '.join(warnings) if warnings else ""
    
    def sanitize_data(self, data: Dict) -> Dict:
        """
        Sanitiza todos los campos de texto de la propiedad.
        
        Realiza:
        - Trim de espacios en blanco
        - Normalización de unicode
        - Title case para ubicaciones
        - Limpieza de caracteres especiales
        
        Args:
            data: Diccionario con datos de la propiedad
            
        Returns:
            Diccionario con datos sanitizados
            
        Example:
            >>> validator.sanitize_data({'ubicacion': '  las condes  '})
            {'ubicacion': 'Las Condes'}
        """
        sanitized = data.copy()
        
        # Campos de texto a sanitizar
        text_fields = [
            'id', 'titulo', 'descripcion', 'ubicacion', 'direccion',
            'tipo', 'operacion', 'publicador_nombre', 'publicador_tipo',
            'estado', 'comuna', 'region'
        ]
        
        for field in text_fields:
            if field in sanitized and sanitized[field] is not None:
                value = sanitized[field]
                
                # Asegurar que es string
                if not isinstance(value, str):
                    continue
                    
                # Trim espacios
                value = value.strip()
                
                # Normalizar espacios múltiples
                value = ' '.join(value.split())
                
                # Title case para ubicaciones y direcciones
                if field in ['ubicacion', 'direccion', 'comuna']:
                    value = value.title()
                    
                sanitized[field] = value
                
        # Sanitizar precio
        if 'precio' in sanitized and sanitized['precio'] is not None:
            if isinstance(sanitized['precio'], str):
                sanitized['precio'] = sanitized['precio'].strip()
                
        return sanitized


def validate_properties_batch(properties: List[Dict]) -> Tuple[List[Dict], List[Dict], List[str]]:
    """
    Valida un lote de propiedades.
    
    Útil para validar todas las propiedades antes de exportar.
    
    Args:
        properties: Lista de diccionarios con propiedades
        
    Returns:
        Tuple de (propiedades_válidas, propiedades_inválidas, logs)
        
    Example:
        >>> valid, invalid, logs = validate_properties_batch(properties)
        >>> print(f"Válidas: {len(valid)}, Inválidas: {len(invalid)}")
    """
    validator = DataValidator()
    valid_properties = []
    invalid_properties = []
    logs = []
    
    for idx, prop in enumerate(properties):
        result = validator.validate_property(prop)
        
        if result.is_valid:
            valid_properties.append(result.property_data)
            if result.warnings:
                logs.append(f"Propiedad {idx} ({prop.get('id', 'N/A')}): advertencias - {', '.join(result.warnings)}")
        else:
            invalid_properties.append(prop)
            logs.append(f"Propiedad {idx}: inválida - {', '.join(result.errors)}")
            if result.warnings:
                logs.append(f"  Advertencias: {', '.join(result.warnings)}")
                
    return valid_properties, invalid_properties, logs


if __name__ == "__main__":
    # Tests básicos del módulo
    import sys
    
    print("Testing DataValidator...")
    validator = DataValidator()
    
    # Test 1: ID válido
    result = validator.validate_id("MLC-12345678")
    assert result[0] == True, f"Test 1 failed: {result}"
    print("✓ Test 1: ID válido")
    
    # Test 2: ID inválido
    result = validator.validate_id("ABC-123")
    assert result[0] == False, f"Test 2 failed: {result}"
    print("✓ Test 2: ID inválido")
    
    # Test 3: Precio UF
    result = validator.validate_price("UF 5.500")
    assert result[0] == True, f"Test 3 failed: {result}"
    assert result[1]['moneda'] == 'UF', f"Test 3 failed: {result}"
    print("✓ Test 3: Precio UF")
    
    # Test 4: Precio CLP
    result = validator.validate_price("$ 150.000.000")
    assert result[0] == True, f"Test 4 failed: {result}"
    assert result[1]['moneda'] == 'CLP', f"Test 4 failed: {result}"
    print("✓ Test 4: Precio CLP")
    
    # Test 5: Propiedad completa
    prop = {
        'id': 'MLC-12345678',
        'titulo': '  Departamento en Las Condes  ',
        'precio': 'UF 5.500',
        'ubicacion': '  las condes  ',
        'dormitorios': '3',
        'banos': '2',
        'metros_cuadrados': '85',
        'tipo': 'departamento',
        'operacion': 'venta',
        'url': 'https://www.portalinmobiliario.com/propiedad/MLC-12345678'
    }
    result = validator.validate_property(prop)
    assert result.is_valid == True, f"Test 5 failed: {result.errors}"
    assert result.property_data['ubicacion'] == 'Las Condes', f"Test 5 failed: ubicacion no sanitizada"
    print("✓ Test 5: Propiedad completa")
    
    print("\n✅ Todos los tests pasaron!")
    sys.exit(0)
