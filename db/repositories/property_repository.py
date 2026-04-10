"""
Property Repository with specific query methods.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_
from models import Property
from .base_repository import BaseRepository


class PropertyRepository(BaseRepository[Property]):
    """
    Repository for Property entity with specific query methods.
    
    Provides methods for querying properties by various criteria
    specific to real estate data.
    """
    
    def __init__(self, session: Session):
        """
        Initialize PropertyRepository.
        
        Args:
            session: SQLAlchemy session
        """
        super().__init__(session, Property)
    
    def find_by_url(self, url: str) -> Optional[Property]:
        """
        Find property by URL.
        
        Args:
            url: Property URL
            
        Returns:
            Property instance or None
        """
        return self._session.execute(
            select(Property).where(Property.url == url)
        ).scalar_one_or_none()
    
    def find_by_portal_id(self, portal_id: str) -> Optional[Property]:
        """
        Find property by portal ID.
        
        Args:
            portal_id: Portal property ID (e.g., "MLC-3705621748")
            
        Returns:
            Property instance or None
        """
        return self._session.execute(
            select(Property).where(Property.portal_id == portal_id)
        ).scalar_one_or_none()
    
    def find_by_location(
        self, 
        comuna: Optional[str] = None,
        region: Optional[str] = None
    ) -> List[Property]:
        """
        Find properties by location.
        
        Args:
            comuna: Commune name
            region: Region name
            
        Returns:
            List of matching properties
        """
        query = select(Property)
        
        conditions = []
        if comuna:
            conditions.append(Property.comuna == comuna)
        if region:
            conditions.append(Property.region == region)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        result = self._session.execute(query)
        return list(result.scalars().all())
    
    def find_by_price_range(
        self,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        currency: Optional[str] = None
    ) -> List[Property]:
        """
        Find properties by price range.
        
        Args:
            min_price: Minimum price
            max_price: Maximum price
            currency: Currency code (CLP, UF, USD)
            
        Returns:
            List of matching properties
        """
        query = select(Property)
        
        conditions = []
        if min_price is not None:
            conditions.append(Property.precio >= min_price)
        if max_price is not None:
            conditions.append(Property.precio <= max_price)
        if currency:
            conditions.append(Property.precio_moneda == currency)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        result = self._session.execute(query)
        return list(result.scalars().all())
    
    def find_by_operation_and_type(
        self,
        operacion: str,
        tipo: Optional[str] = None
    ) -> List[Property]:
        """
        Find properties by operation type and property type.
        
        Args:
            operacion: Operation (venta, arriendo, arriendo-de-temporada)
            tipo: Property type (departamento, casa, etc.)
            
        Returns:
            List of matching properties
        """
        query = select(Property).where(Property.operacion == operacion)
        
        if tipo:
            query = query.where(Property.tipo == tipo)
        
        result = self._session.execute(query)
        return list(result.scalars().all())
    
    def search(
        self,
        filters: dict,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        descending: bool = False
    ) -> List[Property]:
        """
        Search properties with multiple filters.
        
        Args:
            filters: Dictionary of field/value pairs
            skip: Number of records to skip
            limit: Maximum records to return
            order_by: Field to sort by
            descending: Sort direction
            
        Returns:
            List of matching properties
        """
        query = select(Property)
        
        conditions = []
        for key, value in filters.items():
            if hasattr(Property, key) and value is not None:
                column = getattr(Property, key)
                
                # Handle special cases
                if key == 'precio_min':
                    conditions.append(Property.precio >= value)
                elif key == 'precio_max':
                    conditions.append(Property.precio <= value)
                elif key == 'ubicacion':
                    conditions.append(Property.direccion.ilike(f'%{value}%'))
                elif key == 'titulo':
                    conditions.append(Property.titulo.ilike(f'%{value}%'))
                else:
                    conditions.append(column == value)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Apply ordering
        if order_by and hasattr(Property, order_by):
            column = getattr(Property, order_by)
            if descending:
                query = query.order_by(column.desc())
            else:
                query = query.order_by(column.asc())
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = self._session.execute(query)
        return list(result.scalars().all())
