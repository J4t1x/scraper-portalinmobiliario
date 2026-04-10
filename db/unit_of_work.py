"""
Unit of Work pattern implementation for transaction management.

Provides a context manager for database transactions with automatic
commit/rollback behavior.
"""

from typing import Optional
from sqlalchemy.orm import Session
from database import get_session
from db.repositories.property_repository import PropertyRepository


class UnitOfWork:
    """
    Unit of Work context manager for transaction management.
    
    Manages database transactions with automatic commit on success
    and rollback on exceptions. Provides access to repositories.
    """
    
    def __init__(self, session: Optional[Session] = None):
        """
        Initialize Unit of Work.
        
        Args:
            session: Optional SQLAlchemy session. If not provided,
                    creates a new session.
        """
        self._session = session
        self._property_repository: Optional[PropertyRepository] = None
        self._committed = False
    
    def __enter__(self) -> 'UnitOfWork':
        """
        Enter context manager.
        
        Returns:
            UnitOfWork instance
        """
        if self._session is None:
            self._session = get_session()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit context manager with automatic commit/rollback.
        
        Args:
            exc_type: Exception type if raised
            exc_val: Exception value if raised
            exc_tb: Exception traceback if raised
        """
        if exc_type is not None:
            # Exception occurred, rollback
            if self._session:
                self._session.rollback()
            return
        
        # No exception, commit if not already committed
        if not self._committed and self._session:
            self._session.commit()
        
        # Close session if we created it
        if self._session and self._session is not None:
            self._session.close()
    
    def commit(self) -> None:
        """
        Manually commit the transaction.
        
        Call this if you want to commit before exiting the context.
        """
        if self._session:
            self._session.commit()
            self._committed = True
    
    def rollback(self) -> None:
        """
        Manually rollback the transaction.
        """
        if self._session:
            self._session.rollback()
            self._committed = False
    
    @property
    def properties(self) -> PropertyRepository:
        """
        Get PropertyRepository instance.
        
        Returns:
            PropertyRepository
        """
        if self._property_repository is None:
            self._property_repository = PropertyRepository(self._session)
        return self._property_repository
    
    @property
    def session(self) -> Session:
        """
        Get the underlying SQLAlchemy session.
        
        Returns:
            SQLAlchemy Session
        """
        return self._session
