"""
Property model for scraped real estate data.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, DateTime, Boolean
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
    
    # Primary key and identifiers
    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(500), unique=True, nullable=False, index=True)
    portal_id = Column(String(100), index=True, nullable=True)
    
    # Basic data
    titulo = Column(String(500), nullable=True)
    precio = Column(Integer, nullable=True)
    precio_moneda = Column(String(10), nullable=True)
    precio_original = Column(String(100), nullable=True)
    operacion = Column(String(50), nullable=True, index=True)
    tipo = Column(String(50), nullable=True, index=True)
    
    # Location
    comuna = Column(String(100), nullable=True, index=True)
    region = Column(String(100), nullable=True)
    direccion = Column(String(500), nullable=True)
    
    # Additional data from listing
    headline = Column(String(500), nullable=True)
    atributos = Column(String(1000), nullable=True)
    
    # Additional data from detail page
    descripcion = Column(String(5000), nullable=True)
    
    # Metadata
    publicado_en = Column(DateTime, nullable=True)
    scrapeado_en = Column(DateTime, default=datetime.utcnow, nullable=False)
    actualizado_en = Column(DateTime, onupdate=datetime.utcnow, nullable=True)
    
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
