"""
Feature mapper: normalize Portal Inmobiliario spec keys into typed property fields.

The PDP shows dozens of key/value specs (Superficie total, Dormitorios, Año
construcción, Orientación, etc.). This module centralizes:

  * Key normalization (accent/case-insensitive).
  * Mapping of well-known keys to typed `Property` columns.
  * Parsing of numeric values (m², years, counts, money).

Unknown keys are preserved as raw features (see `Feature` table) so no data
is lost.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, Optional, Tuple


__all__ = [
    "normalize_key",
    "parse_int",
    "parse_float",
    "parse_money",
    "map_feature",
]


def _strip_accents(text: str) -> str:
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )


def normalize_key(key: str) -> str:
    """Lowercase, strip accents and collapse whitespace/punctuation."""
    if not key:
        return ''
    k = _strip_accents(key).lower().strip()
    k = re.sub(r'[^a-z0-9]+', '_', k).strip('_')
    return k


_INT_RE = re.compile(r'-?\d[\d\.\,]*')


def parse_int(value: Any) -> Optional[int]:
    """Extract first integer from a string (handles ES thousand separators)."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    m = _INT_RE.search(str(value))
    if not m:
        return None
    raw = m.group(0).replace('.', '').replace(',', '')
    try:
        return int(raw)
    except ValueError:
        return None


def parse_float(value: Any) -> Optional[float]:
    """Extract first float. Handles "120,5", "120.5", "1.200,5"."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value)
    m = re.search(r'-?\d[\d\.\,]*', s)
    if not m:
        return None
    raw = m.group(0)
    # If contains both '.' and ',' -> the rightmost is the decimal separator.
    if '.' in raw and ',' in raw:
        if raw.rfind(',') > raw.rfind('.'):
            # European: 1.200,50 -> 1200.50
            raw = raw.replace('.', '').replace(',', '.')
        else:
            # US: 1,200.50 -> 1200.50
            raw = raw.replace(',', '')
    elif ',' in raw:
        # Could be decimal (e.g. "120,5") or thousands. Assume decimal if 1-2 digits after comma.
        parts = raw.split(',')
        if len(parts[-1]) <= 2:
            raw = raw.replace(',', '.')
        else:
            raw = raw.replace(',', '')
    try:
        return float(raw)
    except ValueError:
        return None


def parse_money(value: Any) -> Optional[int]:
    """Parse monetary amount ignoring currency symbols."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    s = re.sub(r'[^\d]', '', str(value).split(',')[0])
    return int(s) if s else None


# Map of normalized_key -> (property_field, parser)
# Use tuples because some keys alias the same field.
_KEY_MAP: Dict[str, Tuple[str, Any]] = {
    # Surfaces
    'superficie_total': ('superficie_total', parse_float),
    'superficie_util': ('superficie_util', parse_float),
    'superficie_cubierta': ('superficie_util', parse_float),
    'superficies_total': ('superficie_total', parse_float),
    'superficie_de_terraza': ('superficie_terraza', parse_float),
    'superficie_terraza': ('superficie_terraza', parse_float),
    'superficie_del_terreno': ('superficie_terreno', parse_float),
    'superficie_de_terreno': ('superficie_terreno', parse_float),
    'superficie_terreno': ('superficie_terreno', parse_float),
    # Counts
    'dormitorios': ('dormitorios', parse_int),
    'habitaciones': ('dormitorios', parse_int),
    'banos': ('banos', parse_int),
    'cantidad_de_banos': ('banos', parse_int),
    'medios_banos': ('medios_banos', parse_int),
    'toilettes': ('medios_banos', parse_int),
    'ambientes': ('ambientes', parse_int),
    'cantidad_de_ambientes': ('ambientes', parse_int),
    'estacionamientos': ('estacionamientos', parse_int),
    'cocheras': ('estacionamientos', parse_int),
    'cantidad_de_estacionamientos': ('estacionamientos', parse_int),
    'bodegas': ('bodegas', parse_int),
    'cantidad_de_bodegas': ('bodegas', parse_int),
    # Floors
    'numero_de_piso_de_la_unidad': ('piso', parse_int),
    'piso_de_la_unidad': ('piso', parse_int),
    'piso': ('piso', parse_int),
    'cantidad_de_pisos': ('pisos_edificio', parse_int),
    'pisos_del_edificio': ('pisos_edificio', parse_int),
    # Pricing
    'gastos_comunes': ('gastos_comunes', parse_money),
    'expensas': ('gastos_comunes', parse_money),
    # Building
    'ano_de_construccion': ('ano_construccion', parse_int),
    'anio_de_construccion': ('ano_construccion', parse_int),
    'ano_construccion': ('ano_construccion', parse_int),
    'antiguedad': ('antiguedad', parse_int),
    'orientacion': ('orientacion', str),
    'vista': ('vista', str),
    'condicion_del_item': ('condicion', str),
    'condicion': ('condicion', str),
}


def map_feature(key: str, value: Any) -> Optional[Tuple[str, Any]]:
    """
    Return (property_field, parsed_value) if the key is known, else None.

    `value` is passed through the associated parser (or returned as str).
    """
    nk = normalize_key(key)
    mapping = _KEY_MAP.get(nk)
    if not mapping:
        return None
    field, parser = mapping
    if parser is str:
        parsed = str(value).strip() if value is not None else None
    else:
        parsed = parser(value)
    if parsed is None or parsed == '':
        return None
    return field, parsed
