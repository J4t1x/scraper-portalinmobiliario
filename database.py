"""
Database configuration and session management for PostgreSQL.

This module provides SQLAlchemy engine configuration, session management,
and database utilities for the scraper.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError, SQLAlchemyError, IntegrityError
from config import Config

logger = logging.getLogger(__name__)

# Global engine and session factory
_engine: Optional = None
_SessionLocal: Optional = None


def setup_database(database_url: Optional[str] = None) -> 'Engine':
    """
    Configure PostgreSQL connection and create engine.
    
    Args:
        database_url: PostgreSQL connection URL. If None, uses Config.DATABASE_URL
        
    Returns:
        SQLAlchemy Engine
        
    Raises:
        OperationalError: If cannot connect to database
        ValueError: If DATABASE_URL is not configured
    """
    global _engine, _SessionLocal
    
    if database_url is None:
        database_url = Config.DATABASE_URL
    
    if not database_url:
        raise ValueError("DATABASE_URL is not configured. Please set it in .env or environment variables.")
    
    try:
        _engine = create_engine(
            database_url,
            pool_size=Config.DB_POOL_SIZE,
            max_overflow=Config.DB_MAX_OVERFLOW,
            pool_timeout=Config.DB_POOL_TIMEOUT,
            pool_pre_ping=True,  # Verify connections before using
            echo=False  # Set to True for SQL query logging
        )
        
        _SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)
        
        logger.info(f"Database engine created successfully for: {database_url.split('@')[1] if '@' in database_url else 'local'}")
        return _engine
        
    except OperationalError as e:
        logger.error(f"Failed to connect to database: {e}")
        raise
    except Exception as e:
        logger.error(f"Error creating database engine: {e}")
        raise


def get_engine() -> 'Engine':
    """
    Get the database engine, creating it if necessary.
    
    Returns:
        SQLAlchemy Engine
    """
    global _engine
    
    if _engine is None:
        return setup_database()
    
    return _engine


def get_session() -> Session:
    """
    Get a database session.
    
    Returns:
        SQLAlchemy Session
        
    Note:
        Always close the session after use using session.close()
        or use as a context manager:
        with get_session() as session:
            ...
    """
    global _SessionLocal
    
    if _SessionLocal is None:
        setup_database()
    
    return _SessionLocal()


def create_tables() -> None:
    """
    Create all tables from models.
    
    Note:
        This is typically done via Alembic migrations.
        Use this only for development/testing.
    """
    from models import Base
    
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    logger.info("All tables created successfully")


def test_connection() -> bool:
    """
    Test database connection.
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("Database connection test successful")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False


def close_database() -> None:
    """
    Close database engine and dispose all connections.
    """
    global _engine, _SessionLocal
    
    if _engine:
        _engine.dispose()
        _engine = None
        logger.info("Database engine disposed")
    
    _SessionLocal = None


class DatabaseSession:
    """
    Context manager for database sessions.
    
    Usage:
        with DatabaseSession() as session:
            session.query(Model).all()
    """
    
    def __enter__(self) -> Session:
        self.session = get_session()
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.session.rollback()
            logger.error(f"Database session rolled back due to exception: {exc_val}")
        else:
            self.session.commit()
        
        self.session.close()


def upsert_property(session: Session, property_data: Dict[str, Any]) -> 'Property':
    """
    Insert or update a property (upsert operation).
    
    This function checks if a property with the given URL already exists.
    If it exists, it updates the record; otherwise, it creates a new one.
    Related records (features, images, publisher) are also upserted.
    
    Args:
        session: SQLAlchemy Session
        property_data: Dict with property data including:
            - url (required): Unique URL of the property
            - portal_id: ID from the portal
            - titulo: Property title
            - precio: Price as integer
            - precio_moneda: Currency code
            - operacion: Operation type (venta, arriendo, etc.)
            - tipo: Property type (departamento, casa, etc.)
            - comuna: Commune name
            - region: Region name
            - direccion: Full address
            - publicado_en: Publication date
            - features: Dict of features (key -> value)
            - imagenes: List of image URLs
            - publisher: Dict with publisher info (nombre, telefono, email, tipo)
        
    Returns:
        Property instance (created or updated)
        
    Raises:
        ValueError: If required fields are missing
        SQLAlchemyError: If database operation fails
    """
    from models import Property, Feature, Image, Publisher
    
    # Validate required fields
    if not property_data.get('url'):
        raise ValueError("Property data must include 'url' field")
    
    url = property_data['url']
    
    try:
        # Try to find existing property by URL
        property = session.query(Property).filter(Property.url == url).first()
        
        if property:
            # Update existing property
            logger.info(f"Updating existing property: {url}")
            
            # Update basic fields
            if 'portal_id' in property_data:
                property.portal_id = property_data['portal_id']
            if 'titulo' in property_data:
                property.titulo = property_data['titulo']
            if 'precio' in property_data:
                property.precio = property_data['precio']
            if 'precio_moneda' in property_data:
                property.precio_moneda = property_data['precio_moneda']
            if 'operacion' in property_data:
                property.operacion = property_data['operacion']
            if 'tipo' in property_data:
                property.tipo = property_data['tipo']
            if 'comuna' in property_data:
                property.comuna = property_data['comuna']
            if 'region' in property_data:
                property.region = property_data['region']
            if 'direccion' in property_data:
                property.direccion = property_data['direccion']
            if 'publicado_en' in property_data:
                property.publicado_en = property_data['publicado_en']
            
            # Update actualizado_en timestamp
            property.actualizado_en = datetime.utcnow()
            
            # Delete existing related records (cascade will handle this)
            session.query(Feature).filter(Feature.property_id == property.id).delete()
            session.query(Image).filter(Image.property_id == property.id).delete()
            session.query(Publisher).filter(Publisher.property_id == property.id).delete()
            
        else:
            # Create new property
            logger.info(f"Creating new property: {url}")
            property = Property(
                url=url,
                portal_id=property_data.get('portal_id'),
                titulo=property_data.get('titulo'),
                precio=property_data.get('precio'),
                precio_moneda=property_data.get('precio_moneda'),
                operacion=property_data.get('operacion'),
                tipo=property_data.get('tipo'),
                comuna=property_data.get('comuna'),
                region=property_data.get('region'),
                direccion=property_data.get('direccion'),
                publicado_en=property_data.get('publicado_en'),
                scrapeado_en=datetime.utcnow()
            )
            session.add(property)
            session.flush()  # Get the ID
        
        # Upsert features
        if 'features' in property_data and isinstance(property_data['features'], dict):
            for key, value in property_data['features'].items():
                feature = Feature(
                    property_id=property.id,
                    key=str(key),
                    value=str(value) if value is not None else None
                )
                session.add(feature)
        
        # Upsert images
        if 'imagenes' in property_data and isinstance(property_data['imagenes'], list):
            for idx, img_url in enumerate(property_data['imagenes']):
                image = Image(
                    property_id=property.id,
                    url=str(img_url),
                    es_principal=(idx == 0)  # First image is principal
                )
                session.add(image)
        
        # Upsert publisher
        if 'publisher' in property_data and isinstance(property_data['publisher'], dict):
            publisher_data = property_data['publisher']
            publisher = Publisher(
                property_id=property.id,
                nombre=publisher_data.get('nombre'),
                telefono=publisher_data.get('telefono'),
                email=publisher_data.get('email'),
                tipo=publisher_data.get('tipo')
            )
            session.add(publisher)
        
        session.flush()
        logger.info(f"Property upserted successfully: {url} (ID: {property.id})")
        return property
        
    except IntegrityError as e:
        logger.error(f"Integrity error upserting property {url}: {e}")
        session.rollback()
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error upserting property {url}: {e}")
        session.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected error upserting property {url}: {e}")
        session.rollback()
        raise
