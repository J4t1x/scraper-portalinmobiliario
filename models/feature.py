"""
Feature model for property characteristics.
"""

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Feature(Base):
    """
    Model representing a property feature/characteristic.
    
    Stores individual features like dormitorios, baños, m², etc.
    as key-value pairs associated with a property.
    
    Attributes:
        id: Primary key
        property_id: Foreign key to properties table
        key: Feature name (e.g., "dormitorios", "baños", "m2_utiles")
        value: Feature value (e.g., "2", "1", "50")
        property: Relationship to Property model
    """
    
    __tablename__ = 'features'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    property_id = Column(
        Integer,
        ForeignKey('properties.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    key = Column(String(100), nullable=False)
    value = Column(String(500), nullable=True)
    
    # Relationship
    property = relationship("Property", back_populates="features")
    
    def __repr__(self) -> str:
        return f"<Feature(id={self.id}, key='{self.key}', value='{self.value}')>"
    
    def to_dict(self) -> dict:
        """
        Convert feature to dictionary representation.
        
        Returns:
            Dictionary with feature data
        """
        return {
            'id': self.id,
            'property_id': self.property_id,
            'key': self.key,
            'value': self.value,
        }
