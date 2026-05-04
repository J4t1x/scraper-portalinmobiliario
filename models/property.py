"""
Property model for scraped real estate data.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Numeric, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from database import Base


class Property(Base):
    """
    Main property model representing a real estate listing.
    
    Attributes:
        id: Primary key
        url: Unique URL of the property listing
        portal_id: ID from the portal (e.g., "MLC-3705621748")
        titulo: Property title
        precio: Price as integer (normalized)
        precio_moneda: Currency code (CLP, UF, USD)
        precio_original: Original price string from scraper
        operacion: Operation type (venta, arriendo, arriendo-de-temporada)
        tipo: Property type (departamento, casa, oficina, etc.)
        comuna: Commune name
        region: Region name
        direccion: Full address
        headline: Category headline
        atributos: Raw attributes string from scraper
        descripcion: Full description (from detail page)
        publicado_en: Date when property was published
        scrapeado_en: Timestamp when property was scraped
        actualizado_en: Timestamp of last update
        features: List of Feature objects (one-to-many)
        images: List of Image objects (one-to-many)
        publisher: Publisher object (one-to-one)
    """
    
    __tablename__ = 'properties'
    
    # Primary key and identifiers (mapped to actual DB columns)
    id = Column(Integer, primary_key=True, autoincrement=True)
    # Python attr `portal_id` -> DB column `property_id` (portal listing identifier, e.g. "MLC-3705621748")
    portal_id = Column('property_id', String(255), nullable=False)
    url = Column(Text, nullable=True)
    
    # Basic data (mapped to actual DB columns)
    titulo = Column('title', Text, nullable=True)  # DB: title
    headline = Column(Text, nullable=True)
    precio = Column(Numeric, nullable=True)
    precio_moneda = Column(String(10), nullable=True)  # CLP, UF, USD
    precio_original = Column(Text, nullable=True)  # Raw price string from scraper
    
    # Operation and type (mapped to actual DB columns)
    operacion = Column(String, nullable=True)
    tipo = Column('tipo_propiedad', String, nullable=True)  # DB: tipo_propiedad
    
    # Location (mapped to actual DB columns)
    direccion = Column('ubicacion', Text, nullable=True)  # DB: ubicacion
    comuna = Column(String, nullable=True)
    region = Column(String, nullable=True)
    
    # Detail / descriptive fields
    atributos = Column(Text, nullable=True)  # Raw attributes string from scraper
    descripcion = Column(Text, nullable=True)  # Full description (from detail page)
    publicado_en = Column(DateTime, nullable=True)  # Publication date
    
    # Analytics fields (mapped to actual DB columns)
    superficie_total = Column(Numeric, nullable=True)
    superficie_util = Column(Numeric, nullable=True)
    superficie_terraza = Column(Numeric, nullable=True)
    superficie_terreno = Column(Numeric, nullable=True)
    dormitorios = Column(Integer, nullable=True)
    banos = Column(Integer, nullable=True)
    medios_banos = Column(Integer, nullable=True)
    ambientes = Column(Integer, nullable=True)
    estacionamientos = Column(Integer, nullable=True)
    bodegas = Column(Integer, nullable=True)
    piso = Column(Integer, nullable=True)
    pisos_edificio = Column(Integer, nullable=True)

    # Pricing extras
    precio_anterior = Column(Numeric, nullable=True)
    gastos_comunes = Column(Integer, nullable=True)

    # Building / unit details
    ano_construccion = Column('ano_construccion', Integer, nullable=True)
    antiguedad = Column(Integer, nullable=True)
    orientacion = Column(String(50), nullable=True)
    vista = Column(String(100), nullable=True)
    condicion = Column(String(50), nullable=True)  # nuevo/usado

    # Location details
    barrio = Column(String(150), nullable=True)
    calle = Column(String(200), nullable=True)
    numero = Column(String(50), nullable=True)
    lat = Column(Numeric(10, 7), nullable=True)
    lng = Column(Numeric(10, 7), nullable=True)

    # Additional content
    descripcion_html = Column(Text, nullable=True)

    # Listing metrics / state
    num_fotos = Column(Integer, nullable=True)
    thumbnail_url = Column(Text, nullable=True)
    visitas = Column(Integer, nullable=True)
    estado_publicacion = Column(String(50), nullable=True)
    fecha_publicacion = Column(DateTime, nullable=True)
    fecha_actualizacion = Column(DateTime, nullable=True)

    # Flexible / raw data
    tags = Column(JSONB, nullable=True)
    breadcrumbs = Column(JSONB, nullable=True)
    raw_state = Column(JSONB, nullable=True)

    # Metadata (mapped to actual DB columns)
    scrapeado_en = Column('scraped_at', DateTime, nullable=True)  # DB: scraped_at
    created_at = Column(DateTime, nullable=True)
    actualizado_en = Column('updated_at', DateTime, nullable=True)  # DB: updated_at
    
    # Relationships
    features = relationship(
        "Feature",
        back_populates="property",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    images = relationship(
        "Image",
        back_populates="property",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    publisher = relationship(
        "Publisher",
        back_populates="property",
        uselist=False,
        cascade="all, delete-orphan"
    )
    opportunities = relationship(
        "Opportunity",
        back_populates="property",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    amenities = relationship(
        "Amenity",
        back_populates="property",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    services = relationship(
        "Service",
        back_populates="property",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    def __repr__(self) -> str:
        return f"<Property(id={self.id}, portal_id='{self.portal_id}', titulo='{self.titulo}', precio={self.precio})>"
    
    def to_dict(self) -> dict:
        """
        Convert property to dictionary representation.
        
        Returns:
            Dictionary with property data
        """
        return {
            'id': self.id,
            'url': self.url,
            'portal_id': self.portal_id,
            'titulo': self.titulo,
            'precio': self.precio,
            'precio_moneda': self.precio_moneda,
            'precio_original': self.precio_original,
            'operacion': self.operacion,
            'tipo': self.tipo,
            'comuna': self.comuna,
            'region': self.region,
            'direccion': self.direccion,
            'headline': self.headline,
            'atributos': self.atributos,
            'descripcion': self.descripcion,
            'publicado_en': self.publicado_en.isoformat() if self.publicado_en else None,
            'scrapeado_en': self.scrapeado_en.isoformat() if self.scrapeado_en else None,
            'actualizado_en': self.actualizado_en.isoformat() if self.actualizado_en else None,
        }
