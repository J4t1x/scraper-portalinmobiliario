"""
Database integration for scraper.

This module provides functions to persist scraped properties to PostgreSQL
using SQLAlchemy models with upsert logic to avoid duplicates.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from database import get_engine, session_scope, setup_database
from models import Property, Feature, Image, Publisher, Amenity, Service
from feature_mapper import normalize_key

logger = logging.getLogger(__name__)


def parse_price(price_str: Optional[str]) -> tuple[Optional[int], Optional[str]]:
    """
    Parse price string to integer and currency code.
    
    Args:
        price_str: Price string (e.g., "UF 3.055", "$ 740.000", "USD 1,200")
        
    Returns:
        Tuple of (amount, currency_code) or (None, None) if parsing fails
    """
    if not price_str:
        return None, None
    
    price_str = price_str.strip()
    
    # UF format
    if price_str.startswith('UF'):
        try:
            amount = int(float(price_str.replace('UF', '').replace('.', '').replace(',', '').strip()))
            return amount, 'UF'
        except (ValueError, AttributeError):
            return None, None
    
    # CLP format (starts with $)
    elif price_str.startswith('$'):
        try:
            amount = int(price_str.replace('$', '').replace('.', '').replace(',', '').strip())
            return amount, 'CLP'
        except (ValueError, AttributeError):
            return None, None
    
    # USD format
    elif price_str.startswith('USD'):
        try:
            amount = int(float(price_str.replace('USD', '').replace('.', '').replace(',', '').strip()))
            return amount, 'USD'
        except (ValueError, AttributeError):
            return None, None
    
    return None, None


def parse_publication_date(date_str: Optional[str]) -> Optional[datetime]:
    """
    Parse publication date string to datetime.
    
    Args:
        date_str: Date string in various formats
        
    Returns:
        datetime object or None if parsing fails
    """
    if not date_str:
        return None
    
    # Try common formats
    formats = [
        '%Y-%m-%d',
        '%d-%m-%Y',
        '%Y/%m/%d',
        '%d/%m/%Y',
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    
    return None


def upsert_property(session: Session, property_data: Dict) -> Property:
    """
    Insert or update a property (upsert logic).
    
    Uses the URL as unique identifier. If a property with the same URL exists,
    it updates the existing record; otherwise, creates a new one.
    
    Args:
        session: SQLAlchemy Session
        property_data: Dict with scraped property data
        
    Returns:
        Property instance (created or updated)
        
    Raises:
        SQLAlchemyError: If database operation fails
    """
    url = property_data.get('url')
    
    if not url:
        raise ValueError("Property data must include 'url' field")
    
    # Try to find existing property by URL
    existing = session.query(Property).filter(Property.url == url).first()
    
    if existing:
        # Update existing property
        logger.info(f"Updating existing property: {url}")
        
        # Update basic fields if provided
        if 'titulo' in property_data:
            existing.titulo = property_data['titulo']
        if 'headline' in property_data:
            existing.headline = property_data['headline']
        if 'precio' in property_data:
            existing.precio_original = property_data['precio']
            precio, moneda = parse_price(property_data['precio'])
            if precio:
                existing.precio = precio
            if moneda:
                existing.precio_moneda = moneda
        if 'ubicacion' in property_data:
            existing.direccion = property_data['ubicacion']
        if 'atributos' in property_data:
            existing.atributos = property_data['atributos']
        if 'operacion' in property_data:
            existing.operacion = property_data['operacion']
        if 'tipo' in property_data:
            existing.tipo = property_data['tipo']
        
        # Update detail fields if provided
        if 'descripcion' in property_data:
            existing.descripcion = property_data['descripcion']

        # Update timestamp
        existing.actualizado_en = datetime.utcnow()

        prop = existing
    else:
        # Create new property
        logger.info(f"Creating new property: {url}")

        precio, moneda = parse_price(property_data.get('precio'))

        prop = Property(
            url=url,
            portal_id=property_data.get('id'),
            titulo=property_data.get('titulo'),
            precio=precio,
            precio_moneda=moneda,
            precio_original=property_data.get('precio'),
            operacion=property_data.get('operacion'),
            tipo=property_data.get('tipo'),
            direccion=property_data.get('ubicacion'),
            headline=property_data.get('headline'),
            atributos=property_data.get('atributos'),
            descripcion=property_data.get('descripcion'),
            scrapeado_en=datetime.utcnow()
        )

        session.add(prop)
        session.flush()  # Get the ID without committing

    # -- Extended fields (listado + detalle) -----------------------------
    _apply_extended_fields(prop, property_data)
    
    # Handle features (raw specs) -- prefer features_raw list, fallback to caracteristicas dict
    features_raw = property_data.get('features_raw')
    caracteristicas = property_data.get('caracteristicas')

    if features_raw or caracteristicas:
        session.query(Feature).filter(Feature.property_id == prop.id).delete()

    if isinstance(features_raw, list):
        seen = set()
        for feat in features_raw:
            if not isinstance(feat, dict):
                continue
            key = (feat.get('key') or '').strip()
            value = feat.get('value')
            if not key or value in (None, ''):
                continue
            nk = normalize_key(key)
            if nk in seen:
                continue
            seen.add(nk)
            session.add(Feature(
                property_id=prop.id,
                key=key[:100],
                value=str(value)[:500],
            ))
    elif isinstance(caracteristicas, dict):
        for key, value in caracteristicas.items():
            if value in (None, ''):
                continue
            session.add(Feature(
                property_id=prop.id,
                key=str(key)[:100],
                value=str(value)[:500],
            ))

    # Handle images (list of dicts or list of str URLs)
    imagenes = property_data.get('imagenes')
    if isinstance(imagenes, list):
        session.query(Image).filter(Image.property_id == prop.id).delete()
        for i, img in enumerate(imagenes):
            if isinstance(img, dict):
                url = img.get('url')
                if not url:
                    continue
                session.add(Image(
                    property_id=prop.id,
                    url=url,
                    es_principal=(i == 0),
                    orden=img.get('orden', i),
                    alt=img.get('alt'),
                    resolucion=img.get('resolucion'),
                ))
            elif isinstance(img, str):
                session.add(Image(
                    property_id=prop.id,
                    url=img,
                    es_principal=(i == 0),
                    orden=i,
                ))

    # Handle publisher
    pub_data = property_data.get('publicador')
    if isinstance(pub_data, dict) and (pub_data.get('nombre') or pub_data.get('tipo')):
        session.query(Publisher).filter(Publisher.property_id == prop.id).delete()
        session.add(Publisher(
            property_id=prop.id,
            nombre=pub_data.get('nombre'),
            telefono=pub_data.get('telefono'),
            email=pub_data.get('email'),
            tipo=pub_data.get('tipo'),
            logo_url=pub_data.get('logo_url'),
            perfil_url=pub_data.get('perfil_url'),
            reputacion=pub_data.get('reputacion'),
            publicaciones_activas=pub_data.get('publicaciones_activas'),
            antiguedad_portal=pub_data.get('antiguedad_portal'),
        ))

    # Handle amenities
    amenities = property_data.get('amenities')
    if isinstance(amenities, list):
        session.query(Amenity).filter(Amenity.property_id == prop.id).delete()
        seen = set()
        for a in amenities:
            nombre = a.get('nombre') if isinstance(a, dict) else str(a)
            categoria = a.get('categoria') if isinstance(a, dict) else None
            if not nombre:
                continue
            nk = normalize_key(nombre)
            if nk in seen:
                continue
            seen.add(nk)
            session.add(Amenity(
                property_id=prop.id,
                nombre=nombre[:200],
                categoria=categoria,
            ))

    # Handle services
    servicios = property_data.get('servicios')
    if isinstance(servicios, list):
        session.query(Service).filter(Service.property_id == prop.id).delete()
        seen = set()
        for s in servicios:
            if isinstance(s, dict):
                nombre = s.get('nombre')
                incluido = s.get('incluido')
            else:
                nombre = str(s)
                incluido = None
            if not nombre:
                continue
            nk = normalize_key(nombre)
            if nk in seen:
                continue
            seen.add(nk)
            session.add(Service(
                property_id=prop.id,
                nombre=nombre[:200],
                incluido=incluido,
            ))

    return prop


def _apply_extended_fields(prop: Property, data: Dict) -> None:
    """Apply extended typed fields (from listado + detalle) onto Property.

    Silently ignores keys that don't map to columns. Uses `caracteristicas`
    dict (field -> parsed value) emitted by the feature mapper.
    """
    # Parse relative dates (already ISO strings from scraper)
    def _parse_date(val):
        if not val:
            return None
        if isinstance(val, datetime):
            return val
        for fmt in ('%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S'):
            try:
                return datetime.strptime(val, fmt)
            except (ValueError, TypeError):
                continue
        return None

    # Listado-level extras
    if data.get('precio_anterior') is not None:
        prop.precio_anterior = data['precio_anterior']
    if data.get('thumbnail_url'):
        prop.thumbnail_url = data['thumbnail_url']
    if data.get('num_fotos') is not None:
        prop.num_fotos = data['num_fotos']
    if isinstance(data.get('tags'), list) and data['tags']:
        prop.tags = data['tags']

    # Detalle-level
    if data.get('descripcion_html'):
        prop.descripcion_html = data['descripcion_html']
    if isinstance(data.get('breadcrumbs'), list) and data['breadcrumbs']:
        prop.breadcrumbs = data['breadcrumbs']
    if isinstance(data.get('raw_state'), dict):
        prop.raw_state = data['raw_state']
    if data.get('visitas') is not None:
        prop.visitas = data['visitas']
    if data.get('estado_publicacion'):
        prop.estado_publicacion = data['estado_publicacion']

    fp = _parse_date(data.get('fecha_publicacion'))
    if fp:
        prop.fecha_publicacion = fp
    fa = _parse_date(data.get('fecha_actualizacion'))
    if fa:
        prop.fecha_actualizacion = fa

    # Coordenadas
    coords = data.get('coordenadas') or {}
    if coords.get('lat') is not None:
        prop.lat = coords['lat']
    if coords.get('lng') is not None:
        prop.lng = coords['lng']

    # Características tipadas -> columnas Property
    caracteristicas = data.get('caracteristicas') or {}
    if not isinstance(caracteristicas, dict):
        return

    # Map of caracteristicas_key -> Property attr name. If both match, assign.
    typed_fields = {
        'superficie_total', 'superficie_util', 'superficie_terraza',
        'superficie_terreno', 'dormitorios', 'banos', 'medios_banos',
        'ambientes', 'estacionamientos', 'bodegas', 'piso', 'pisos_edificio',
        'gastos_comunes', 'ano_construccion', 'antiguedad', 'orientacion',
        'vista', 'condicion', 'barrio',
    }
    for field, value in caracteristicas.items():
        if field in typed_fields and value not in (None, ''):
            try:
                setattr(prop, field, value)
            except Exception as e:
                logger.debug(f"No se pudo asignar {field}={value}: {e}")


def persist_properties(properties: List[Dict], database_url: Optional[str] = None) -> dict:
    """
    Persist a list of scraped properties to the database.
    
    Args:
        properties: List of property data dictionaries
        database_url: Optional database URL (uses Config.DATABASE_URL if not provided)
        
    Returns:
        Dictionary with statistics:
        - total: Total number of properties processed
        - inserted: Number of new properties inserted
        - updated: Number of existing properties updated
        - errors: Number of errors encountered
    """
    if not properties:
        return {'total': 0, 'inserted': 0, 'updated': 0, 'errors': 0}
    
    # Setup database if not already initialized
    try:
        setup_database(database_url)
    except Exception as e:
        logger.error(f"Failed to setup database: {e}")
        return {'total': len(properties), 'inserted': 0, 'updated': 0, 'errors': len(properties)}
    
    stats = {'total': len(properties), 'inserted': 0, 'updated': 0, 'errors': 0}
    
    with session_scope() as session:
        for prop_data in properties:
            try:
                url = prop_data.get('url', 'unknown')
                
                # Check if property exists
                existing = session.query(Property).filter(Property.url == url).first()
                
                if existing:
                    stats['updated'] += 1
                else:
                    stats['inserted'] += 1
                
                upsert_property(session, prop_data)
                
            except SQLAlchemyError as e:
                logger.error(f"Error persisting property {prop_data.get('url', 'unknown')}: {e}")
                stats['errors'] += 1
            except Exception as e:
                logger.error(f"Unexpected error persisting property {prop_data.get('url', 'unknown')}: {e}")
                stats['errors'] += 1
    
    logger.info(f"Persisted properties: {stats}")
    return stats


def get_property_by_url(url: str) -> Optional[Property]:
    """
    Get a property by its URL.
    
    Args:
        url: Property URL
        
    Returns:
        Property instance or None if not found
    """
    with session_scope() as session:
        return session.query(Property).filter(Property.url == url).first()


def get_all_properties(limit: Optional[int] = None) -> List[Property]:
    """
    Get all properties from the database.
    
    Args:
        limit: Optional limit on number of results
        
    Returns:
        List of Property instances
    """
    with session_scope() as session:
        query = session.query(Property).order_by(Property.scrapeado_en.desc())
        if limit:
            query = query.limit(limit)
        return query.all()
