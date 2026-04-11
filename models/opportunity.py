"""
Opportunity model for investment opportunities.
"""

from sqlalchemy import Column, String, Integer, Numeric, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Opportunity(Base):
    """Investment opportunity detected by analytics."""
    
    __tablename__ = 'opportunities'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    property_id = Column(String(50), ForeignKey('properties.id'), nullable=False)
    tipo_oportunidad = Column(String(50), nullable=False)
    score = Column(Numeric(5, 2), nullable=False)
    precio_m2_propiedad = Column(Numeric(12, 2))
    precio_m2_promedio_comuna = Column(Numeric(12, 2))
    diferencia_porcentual = Column(Numeric(5, 2))
    razon = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    property = relationship("Property", back_populates="opportunities")
    
    def __repr__(self):
        return f"<Opportunity(id={self.id}, property_id={self.property_id}, score={self.score})>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'property_id': self.property_id,
            'tipo_oportunidad': self.tipo_oportunidad,
            'score': float(self.score) if self.score else None,
            'precio_m2_propiedad': float(self.precio_m2_propiedad) if self.precio_m2_propiedad else None,
            'precio_m2_promedio_comuna': float(self.precio_m2_promedio_comuna) if self.precio_m2_promedio_comuna else None,
            'diferencia_porcentual': float(self.diferencia_porcentual) if self.diferencia_porcentual else None,
            'razon': self.razon,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
