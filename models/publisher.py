"""
Publisher model for property publishers/contact info.
"""

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Publisher(Base):
    """
    Model representing property publisher/contact information.
    
    Stores publisher details for a property (inmobiliaria or particular).
    
    Attributes:
        id: Primary key
        property_id: Foreign key to properties table
        nombre: Publisher name
        telefono: Contact phone number
        email: Contact email
        tipo: Publisher type (inmobiliaria, particular)
        property: Relationship to Property model
    """
    
    __tablename__ = 'publishers'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    property_id = Column(
        Integer,
        ForeignKey('properties.id', ondelete='CASCADE'),
        nullable=False,
        unique=True,
        index=True
    )
    nombre = Column(String(200), nullable=True)
    telefono = Column(String(50), nullable=True)
    email = Column(String(200), nullable=True)
    tipo = Column(String(50), nullable=True)  # inmobiliaria, particular
    
    # Relationship
    property = relationship("Property", back_populates="publisher")
    
    def __repr__(self) -> str:
        return f"<Publisher(id={self.id}, nombre='{self.nombre}', tipo='{self.tipo}')>"
    
    def to_dict(self) -> dict:
        """
        Convert publisher to dictionary representation.
        
        Returns:
            Dictionary with publisher data
        """
        return {
            'id': self.id,
            'property_id': self.property_id,
            'nombre': self.nombre,
            'telefono': self.telefono,
            'email': self.email,
            'tipo': self.tipo,
        }
