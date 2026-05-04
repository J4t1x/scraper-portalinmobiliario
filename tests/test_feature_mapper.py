"""Tests for feature_mapper normalization and mapping."""

import pytest

from feature_mapper import (
    normalize_key,
    parse_int,
    parse_float,
    parse_money,
    map_feature,
)


class TestNormalizeKey:
    def test_removes_accents(self):
        assert normalize_key('Año de construcción') == 'ano_de_construccion'

    def test_lowercase_and_snake(self):
        assert normalize_key('Superficie Total') == 'superficie_total'

    def test_collapses_whitespace_and_punct(self):
        assert normalize_key('Gastos   comunes (CLP):') == 'gastos_comunes_clp'

    def test_empty(self):
        assert normalize_key('') == ''
        assert normalize_key(None or '') == ''


class TestParsers:
    @pytest.mark.parametrize("value,expected", [
        ('3', 3),
        ('3 dormitorios', 3),
        ('1.200 m²', 1200),
        ('120,50', 12050),  # parse_int strips both
        (None, None),
        ('sin datos', None),
        (42, 42),
    ])
    def test_parse_int(self, value, expected):
        assert parse_int(value) == expected

    @pytest.mark.parametrize("value,expected", [
        ('120,5', 120.5),
        ('1.200,50', 1200.5),
        ('1,200.50', 1200.5),
        ('80 m²', 80.0),
        (None, None),
    ])
    def test_parse_float(self, value, expected):
        assert parse_float(value) == expected

    @pytest.mark.parametrize("value,expected", [
        ('$ 150.000', 150000),
        ('UF 5.500', 5500),
        ('$1.200.000 CLP', 1200000),
        (None, None),
    ])
    def test_parse_money(self, value, expected):
        assert parse_money(value) == expected


class TestMapFeature:
    def test_superficie_total(self):
        result = map_feature('Superficie total', '80 m²')
        assert result == ('superficie_total', 80.0)

    def test_ano_construccion_with_accent(self):
        result = map_feature('Año de construcción', '2018')
        assert result == ('ano_construccion', 2018)

    def test_dormitorios_alias(self):
        assert map_feature('Habitaciones', '3') == ('dormitorios', 3)

    def test_gastos_comunes(self):
        result = map_feature('Gastos comunes', '$ 150.000')
        assert result == ('gastos_comunes', 150000)

    def test_orientacion_string(self):
        assert map_feature('Orientación', 'Norte') == ('orientacion', 'Norte')

    def test_unknown_key_returns_none(self):
        assert map_feature('Campo Desconocido', 'Valor') is None

    def test_empty_value_returns_none(self):
        assert map_feature('Superficie total', '') is None
        assert map_feature('Dormitorios', None) is None
