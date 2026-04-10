"""
Tests unitarios para el módulo validator
"""

import pytest
from validator import DataValidator, ValidationResult, validate_properties_batch


class TestValidationResult:
    """Tests para la clase ValidationResult"""
    
    def test_default_creation(self):
        """TC-RES-001: Creación con valores por defecto"""
        result = ValidationResult()
        assert result.is_valid is False
        assert result.property_data is None
        assert result.warnings == []
        assert result.errors == []
    
    def test_creation_with_values(self):
        """TC-RES-002: Creación con valores específicos"""
        result = ValidationResult(
            is_valid=True,
            property_data={'id': 'MLC-123'},
            warnings=['warning1'],
            errors=[]
        )
        assert result.is_valid is True
        assert result.property_data == {'id': 'MLC-123'}
        assert result.warnings == ['warning1']


class TestDataValidatorInit:
    """Tests para inicialización de DataValidator"""
    
    def test_init(self):
        """TC-VAL-001: Inicialización correcta"""
        validator = DataValidator()
        assert validator is not None
        assert hasattr(validator, 'logger')


class TestValidateId:
    """Tests para validación de ID"""
    
    def test_valid_id(self):
        """TC-ID-001: ID válido MLC-XXXXXXXX"""
        validator = DataValidator()
        is_valid, error = validator.validate_id("MLC-12345678")
        assert is_valid is True
        assert error == ""
    
    def test_valid_id_long(self):
        """TC-ID-002: ID válido con más de 8 dígitos"""
        validator = DataValidator()
        is_valid, error = validator.validate_id("MLC-123456789012")
        assert is_valid is True
        assert error == ""
    
    def test_invalid_id_format(self):
        """TC-ID-003: ID con formato inválido"""
        validator = DataValidator()
        is_valid, error = validator.validate_id("ABC-12345678")
        assert is_valid is False
        assert "Formato inválido" in error
    
    def test_invalid_id_short(self):
        """TC-ID-004: ID con menos de 8 dígitos"""
        validator = DataValidator()
        is_valid, error = validator.validate_id("MLC-123")
        assert is_valid is False
        assert "Formato inválido" in error
    
    def test_invalid_id_empty(self):
        """TC-ID-005: ID vacío"""
        validator = DataValidator()
        is_valid, error = validator.validate_id("")
        assert is_valid is False
        assert "ID vacío" in error
    
    def test_invalid_id_none(self):
        """TC-ID-006: ID None"""
        validator = DataValidator()
        is_valid, error = validator.validate_id(None)
        assert is_valid is False
        assert "ID vacío" in error
    
    def test_invalid_id_non_string(self):
        """TC-ID-007: ID no es string"""
        validator = DataValidator()
        is_valid, error = validator.validate_id(12345678)
        assert is_valid is False
        assert "debe ser string" in error


class TestValidatePrice:
    """Tests para validación de precios"""
    
    def test_valid_price_uf(self):
        """TC-PRICE-001: Precio UF válido"""
        validator = DataValidator()
        is_valid, data, warning = validator.validate_price("UF 5.500")
        assert is_valid is True
        assert data['moneda'] == 'UF'
        assert data['monto'] == 5500.0
    
    def test_valid_price_uf_no_space(self):
        """TC-PRICE-002: Precio UF sin espacio"""
        validator = DataValidator()
        is_valid, data, warning = validator.validate_price("UF5500")
        assert is_valid is True
        assert data['moneda'] == 'UF'
    
    def test_valid_price_clp(self):
        """TC-PRICE-003: Precio CLP con $"""
        validator = DataValidator()
        is_valid, data, warning = validator.validate_price("$ 150.000.000")
        assert is_valid is True
        assert data['moneda'] == 'CLP'
    
    def test_valid_price_clp_no_space(self):
        """TC-PRICE-004: Precio CLP sin espacio"""
        validator = DataValidator()
        is_valid, data, warning = validator.validate_price("$150000000")
        assert is_valid is True
        assert data['moneda'] == 'CLP'
    
    def test_valid_price_clp_dots(self):
        """TC-PRICE-005: Precio CLP con separadores de miles"""
        validator = DataValidator()
        is_valid, data, warning = validator.validate_price("$ 150.000.000")
        assert is_valid is True
        assert data['moneda'] == 'CLP'
    
    def test_invalid_price_empty(self):
        """TC-PRICE-006: Precio vacío"""
        validator = DataValidator()
        is_valid, data, warning = validator.validate_price("")
        assert is_valid is False
        assert data is None
    
    def test_invalid_price_format(self):
        """TC-PRICE-007: Precio con formato inválido"""
        validator = DataValidator()
        is_valid, data, warning = validator.validate_price("INVALIDO")
        assert is_valid is False
    
    def test_invalid_price_non_string(self):
        """TC-PRICE-008: Precio no es string"""
        validator = DataValidator()
        is_valid, data, warning = validator.validate_price(12345)
        assert is_valid is False
        assert "debe ser string" in warning


class TestValidateLocation:
    """Tests para validación de ubicación"""
    
    def test_valid_location(self):
        """TC-LOC-001: Ubicación válida"""
        validator = DataValidator()
        is_valid, warning = validator.validate_location("Las Condes")
        assert is_valid is True
        assert warning == ""
    
    def test_valid_location_full(self):
        """TC-LOC-002: Ubicación completa"""
        validator = DataValidator()
        is_valid, warning = validator.validate_location("Las Condes, Santiago, Chile")
        assert is_valid is True
    
    def test_invalid_location_empty(self):
        """TC-LOC-003: Ubicación vacía"""
        validator = DataValidator()
        is_valid, warning = validator.validate_location("")
        assert is_valid is False
        assert "Ubicación vacía" in warning
    
    def test_invalid_location_whitespace(self):
        """TC-LOC-004: Ubicación solo espacios"""
        validator = DataValidator()
        is_valid, warning = validator.validate_location("   ")
        assert is_valid is False
        assert "solo espacios" in warning
    
    def test_invalid_location_none(self):
        """TC-LOC-005: Ubicación None"""
        validator = DataValidator()
        is_valid, warning = validator.validate_location(None)
        assert is_valid is False
        assert "Ubicación vacía" in warning
    
    def test_invalid_location_non_string(self):
        """TC-LOC-006: Ubicación no es string"""
        validator = DataValidator()
        is_valid, warning = validator.validate_location(123)
        assert is_valid is False
        assert "debe ser string" in warning


class TestValidateAttributes:
    """Tests para validación de atributos"""
    
    def test_valid_attributes(self):
        """TC-ATTR-001: Atributos válidos"""
        validator = DataValidator()
        data = {'dormitorios': 3, 'banos': 2, 'metros_cuadrados': 85}
        is_valid, warnings, sanitized = validator.validate_attributes(data)
        assert is_valid is True
        assert warnings == []
        assert sanitized['dormitorios'] == 3
        assert sanitized['banos'] == 2
        assert sanitized['metros_cuadrados'] == 85.0
    
    def test_valid_attributes_string(self):
        """TC-ATTR-002: Atributos como strings"""
        validator = DataValidator()
        data = {'dormitorios': '3', 'banos': '2', 'metros_cuadrados': '85,5'}
        is_valid, warnings, sanitized = validator.validate_attributes(data)
        assert sanitized['dormitorios'] == 3
        assert sanitized['banos'] == 2
        assert sanitized['metros_cuadrados'] == 85.5
    
    def test_warning_negative_dormitorios(self):
        """TC-ATTR-003: Dormitorios negativos"""
        validator = DataValidator()
        data = {'dormitorios': -1}
        is_valid, warnings, sanitized = validator.validate_attributes(data)
        assert "negativo" in warnings[0]
    
    def test_warning_high_dormitorios(self):
        """TC-ATTR-004: Dormitorios inusualmente alto"""
        validator = DataValidator()
        data = {'dormitorios': 25}
        is_valid, warnings, sanitized = validator.validate_attributes(data)
        assert "inusualmente alto" in warnings[0]
    
    def test_warning_high_banos(self):
        """TC-ATTR-005: Baños inusualmente alto"""
        validator = DataValidator()
        data = {'banos': 20}
        is_valid, warnings, sanitized = validator.validate_attributes(data)
        assert "inusualmente alto" in warnings[0]
    
    def test_warning_invalid_m2(self):
        """TC-ATTR-006: Metros cuadrados inválidos"""
        validator = DataValidator()
        data = {'metros_cuadrados': -10}
        is_valid, warnings, sanitized = validator.validate_attributes(data)
        assert "inválido" in warnings[0]
    
    def test_warning_high_m2(self):
        """TC-ATTR-007: Metros cuadrados inusualmente altos"""
        validator = DataValidator()
        data = {'metros_cuadrados': 50000}
        is_valid, warnings, sanitized = validator.validate_attributes(data)
        assert "inusualmente alto" in warnings[0]
    
    def test_non_numeric_dormitorios(self):
        """TC-ATTR-008: Dormitorios no numérico"""
        validator = DataValidator()
        data = {'dormitorios': 'tres'}
        is_valid, warnings, sanitized = validator.validate_attributes(data)
        assert "no numérico" in warnings[0]


class TestValidateUrl:
    """Tests para validación de URL"""
    
    def test_valid_url_https(self):
        """TC-URL-001: URL HTTPS válida"""
        validator = DataValidator()
        is_valid, error = validator.validate_url("https://www.portalinmobiliario.com/MLC-12345678")
        assert is_valid is True
        assert error == ""
    
    def test_valid_url_http(self):
        """TC-URL-002: URL HTTP válida"""
        validator = DataValidator()
        is_valid, error = validator.validate_url("http://example.com/property")
        assert is_valid is True
    
    def test_empty_url(self):
        """TC-URL-003: URL vacía (no es error crítico)"""
        validator = DataValidator()
        is_valid, error = validator.validate_url("")
        assert is_valid is True  # URL vacía no es error crítico
    
    def test_invalid_url_no_scheme(self):
        """TC-URL-004: URL sin esquema"""
        validator = DataValidator()
        is_valid, error = validator.validate_url("www.portalinmobiliario.com/property")
        assert is_valid is False
    
    def test_invalid_url_malformed(self):
        """TC-URL-005: URL mal formada"""
        validator = DataValidator()
        is_valid, error = validator.validate_url("not-a-url")
        assert is_valid is False


class TestValidateTypeOperation:
    """Tests para validación de tipo y operación"""
    
    def test_valid_type_operation(self):
        """TC-TYPE-001: Tipo y operación válidos"""
        validator = DataValidator()
        is_valid, warning = validator.validate_type_operation('departamento', 'venta')
        assert is_valid is True
        assert warning == ""
    
    def test_valid_arriendo(self):
        """TC-TYPE-002: Operación arriendo válida"""
        validator = DataValidator()
        is_valid, warning = validator.validate_type_operation('casa', 'arriendo')
        assert is_valid is True
    
    def test_warning_invalid_type(self):
        """TC-TYPE-003: Tipo no estándar"""
        validator = DataValidator()
        is_valid, warning = validator.validate_type_operation('castillo', 'venta')
        assert is_valid is False
        assert "Tipo no estándar" in warning
    
    def test_warning_invalid_operation(self):
        """TC-TYPE-004: Operación no estándar"""
        validator = DataValidator()
        is_valid, warning = validator.validate_type_operation('departamento', 'permuta')
        assert is_valid is False
        assert "Operación no estándar" in warning
    
    def test_empty_type_operation(self):
        """TC-TYPE-005: Tipo y operación vacíos"""
        validator = DataValidator()
        is_valid, warning = validator.validate_type_operation('', '')
        assert is_valid is True  # Vacíos no generan warning


class TestSanitizeData:
    """Tests para sanitización de datos"""
    
    def test_sanitize_whitespace(self):
        """TC-SAN-001: Sanitizar espacios"""
        validator = DataValidator()
        data = {'titulo': '  Departamento  en  Las Condes  '}
        sanitized = validator.sanitize_data(data)
        assert sanitized['titulo'] == 'Departamento en Las Condes'
    
    def test_sanitize_title_case(self):
        """TC-SAN-002: Title case para ubicación"""
        validator = DataValidator()
        data = {'ubicacion': '  las condes  '}
        sanitized = validator.sanitize_data(data)
        assert sanitized['ubicacion'] == 'Las Condes'
    
    def test_sanitize_title_case_direccion(self):
        """TC-SAN-003: Title case para dirección"""
        validator = DataValidator()
        data = {'direccion': '  avenida providencia 1234  '}
        sanitized = validator.sanitize_data(data)
        assert sanitized['direccion'] == 'Avenida Providencia 1234'
    
    def test_sanitize_non_string_fields(self):
        """TC-SAN-004: Campos no string se mantienen"""
        validator = DataValidator()
        data = {'dormitorios': 3, 'precio': 100000}
        sanitized = validator.sanitize_data(data)
        assert sanitized['dormitorios'] == 3
        assert sanitized['precio'] == 100000
    
    def test_sanitize_price(self):
        """TC-SAN-005: Sanitizar precio"""
        validator = DataValidator()
        data = {'precio': '  UF 5.500  '}
        sanitized = validator.sanitize_data(data)
        assert sanitized['precio'] == 'UF 5.500'


class TestValidateProperty:
    """Tests para validación completa de propiedad"""
    
    def test_valid_property(self, sample_property):
        """TC-PROP-001: Propiedad válida completa"""
        validator = DataValidator()
        result = validator.validate_property(sample_property)
        assert result.is_valid is True
        assert result.property_data is not None
        assert result.errors == []
    
    def test_invalid_property_no_id(self, invalid_property_no_id):
        """TC-PROP-002: Propiedad sin ID"""
        validator = DataValidator()
        result = validator.validate_property(invalid_property_no_id)
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any('ID' in e for e in result.errors)
    
    def test_invalid_property_bad_price(self, invalid_property_bad_price):
        """TC-PROP-003: Propiedad con precio inválido - warning, no bloquea"""
        validator = DataValidator()
        result = validator.validate_property(invalid_property_bad_price)
        # El precio inválido genera warning, pero ID válido permite que sea válida
        assert result.is_valid is True
        assert any('precio' in w.lower() or 'parsear' in w.lower() for w in result.warnings)
    
    def test_sanitization_in_property_validation(self, sample_property):
        """TC-PROP-004: Sanitización durante validación"""
        validator = DataValidator()
        sample_property['ubicacion'] = '  las condes  '
        result = validator.validate_property(sample_property)
        assert result.is_valid is True
        assert result.property_data['ubicacion'] == 'Las Condes'


class TestValidatePropertiesBatch:
    """Tests para validación en lote"""
    
    def test_batch_all_valid(self, sample_properties_list):
        """TC-BATCH-001: Lote con propiedades válidas"""
        valid, invalid, logs = validate_properties_batch(sample_properties_list)
        assert len(valid) == 3
        assert len(invalid) == 0
        assert len(logs) == 0
    
    def test_batch_with_invalid(self):
        """TC-BATCH-002: Lote con propiedades válidas e inválidas"""
        properties = [
            {'id': 'MLC-11111111', 'precio': 'UF 3.000', 'ubicacion': 'Santiago'},
            {'id': '', 'precio': 'UF 4.000', 'ubicacion': 'Santiago'},  # Inválida - sin ID
            {'id': 'MLC-33333333', 'precio': 'INVALIDO', 'ubicacion': ''}  # Válida - ID ok, precio warning
        ]
        valid, invalid, logs = validate_properties_batch(properties)
        assert len(valid) == 2  # 2 con ID válido (precio inválido no bloquea)
        assert len(invalid) == 1  # 1 sin ID
        assert len(logs) > 0  # Logs de warnings e invalid
    
    def test_batch_empty(self):
        """TC-BATCH-003: Lote vacío"""
        valid, invalid, logs = validate_properties_batch([])
        assert len(valid) == 0
        assert len(invalid) == 0
        assert len(logs) == 0
    
    def test_batch_with_warnings(self):
        """TC-BATCH-004: Lote con advertencias"""
        properties = [
            {'id': 'MLC-11111111', 'precio': 'UF 3.000', 'ubicacion': 'Santiago', 'dormitorios': 50}
        ]
        valid, invalid, logs = validate_properties_batch(properties)
        assert len(valid) == 1
        assert len(logs) == 1  # Log de advertencia por dormitorios
        assert 'advertencias' in logs[0]
