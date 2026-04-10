"""
Image model for property images.
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Image(Base):
    """
    Model representing a property image.
    
    Stores image URLs associated with a property.
    
    Attributes:
        id: Primary key
        property_id: Foreign key to properties table
        url: Image URL
        es_principal: Whether this is the main/featured image
        property: Relationship to Property model
    """
    
    __tablename__ = 'images'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    property_id = Column(
        Integer,
        ForeignKey('properties.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    url = Column(String(500), nullable=False)
    es_principal = Column(Boolean, default=False, nullable=False)
    
    # Relationship
    property = relationship("Property", back_populates="images")
    
    def __repr__(self) -> str:
        return f"<Image(id={self.id}, url='{self.url}', principal={self.es_principal})>"
    
    def to_dict(self) -> dict:
        """
        Convert image to dictionary representation.
        
        Returns:
            Dictionary with image data
        """
        return {
            'id': self.id,
            'property_id': self.property_id,
            'url': self.url,
            'es_principal': self.es_principal,
        }
