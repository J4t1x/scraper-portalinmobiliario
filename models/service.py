"""
Service model for included/excluded services of a property.
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Service(Base):
    """
    Service linked to a property (e.g., agua caliente, gas, internet, cable).

    Attributes:
        id: Primary key
        property_id: FK to properties.id
        nombre: Service name (normalized lowercase)
        incluido: True if included in price, False if not, None if unknown
    """

    __tablename__ = 'services'

    id = Column(Integer, primary_key=True, autoincrement=True)
    property_id = Column(
        Integer,
        ForeignKey('properties.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    nombre = Column(String(200), nullable=False)
    incluido = Column(Boolean, nullable=True)

    property = relationship("Property", back_populates="services")

    def __repr__(self) -> str:
        return f"<Service(id={self.id}, nombre='{self.nombre}', incluido={self.incluido})>"

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'property_id': self.property_id,
            'nombre': self.nombre,
            'incluido': self.incluido,
        }
