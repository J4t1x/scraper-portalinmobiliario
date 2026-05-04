"""
Amenity model for building/property amenities.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, Index
from sqlalchemy.orm import relationship
from database import Base


class Amenity(Base):
    """
    Amenity (e.g., piscina, gimnasio, portería 24h) linked to a property.

    Attributes:
        id: Primary key
        property_id: FK to properties.id
        nombre: Amenity name (normalized, lowercase)
        categoria: Optional grouping (edificio, unidad, seguridad, recreacion, ...)
    """

    __tablename__ = 'amenities'

    id = Column(Integer, primary_key=True, autoincrement=True)
    property_id = Column(
        Integer,
        ForeignKey('properties.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    nombre = Column(String(200), nullable=False)
    categoria = Column(String(100), nullable=True)

    property = relationship("Property", back_populates="amenities")

    __table_args__ = (
        Index('ix_amenities_property_nombre', 'property_id', 'nombre'),
    )

    def __repr__(self) -> str:
        return f"<Amenity(id={self.id}, nombre='{self.nombre}', categoria='{self.categoria}')>"

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'property_id': self.property_id,
            'nombre': self.nombre,
            'categoria': self.categoria,
        }
