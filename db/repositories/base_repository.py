"""
Base Repository class implementing generic CRUD operations.

Provides a common interface for all repositories with standard CRUD methods.
"""

from typing import Generic, TypeVar, List, Optional, Type, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """
    Generic repository with standard CRUD operations.
    
    Provides a base implementation for all entity repositories
    with common database operations.
    """
    
    def __init__(self, session: Session, model: Type[T]):
        """
        Initialize repository with session and model.
        
        Args:
            session: SQLAlchemy session
            model: SQLAlchemy model class
        """
        self._session = session
        self._model = model
    
    def get_by_id(self, id: int) -> Optional[T]:
        """
        Get entity by primary key.
        
        Args:
            id: Primary key value
            
        Returns:
            Entity instance or None if not found
        """
        return self._session.get(self._model, id)
    
    def get(self, id: int) -> Optional[T]:
        """
        Alias for get_by_id() for convenience.
        
        Args:
            id: Primary key value
            
        Returns:
            Entity instance or None if not found
        """
        return self.get_by_id(id)
    
    def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        order_by: Optional[str] = None,
        descending: bool = False
    ) -> List[T]:
        """
        Get all entities with pagination and optional sorting.
        
        Args:
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return
            order_by: Field name to sort by
            descending: Sort in descending order
            
        Returns:
            List of entity instances
        """
        query = select(self._model)
        
        # Apply ordering if specified
        if order_by:
            column = getattr(self._model, order_by, None)
            if column:
                if descending:
                    query = query.order_by(column.desc())
                else:
                    query = query.order_by(column.asc())
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = self._session.execute(query)
        return list(result.scalars().all())
    
    def create(self, obj: T) -> T:
        """
        Create new entity.
        
        Args:
            obj: Entity instance to create
            
        Returns:
            Created entity instance
        """
        self._session.add(obj)
        self._session.flush()
        return obj
    
    def update(self, id: int, data: Dict[str, Any]) -> Optional[T]:
        """
        Update entity by ID.
        
        Args:
            id: Primary key of entity to update
            data: Dictionary of fields to update
            
        Returns:
            Updated entity instance or None if not found
        """
        obj = self.get_by_id(id)
        if obj is None:
            return None
        
        for key, value in data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        
        self._session.flush()
        return obj
    
    def delete(self, id: int) -> bool:
        """
        Delete entity by ID.
        
        Args:
            id: Primary key of entity to delete
            
        Returns:
            True if deleted, False if not found
        """
        obj = self.get_by_id(id)
        if obj is None:
            return False
        
        self._session.delete(obj)
        self._session.flush()
        return True
    
    def find_by(self, **kwargs) -> List[T]:
        """
        Find entities by field values.
        
        Args:
            **kwargs: Field name/value pairs to filter by
            
        Returns:
            List of matching entity instances
        """
        query = select(self._model)
        
        for key, value in kwargs.items():
            if hasattr(self._model, key):
                column = getattr(self._model, key)
                query = query.where(column == value)
        
        result = self._session.execute(query)
        return list(result.scalars().all())
    
    def count(self, **kwargs) -> int:
        """
        Count entities matching filters.
        
        Args:
            **kwargs: Field name/value pairs to filter by
            
        Returns:
            Count of matching entities
        """
        from sqlalchemy import func
        query = select(func.count()).select_from(self._model)
        
        for key, value in kwargs.items():
            if hasattr(self._model, key):
                column = getattr(self._model, key)
                query = query.where(column == value)
        
        result = self._session.execute(query)
        return result.scalar() or 0
