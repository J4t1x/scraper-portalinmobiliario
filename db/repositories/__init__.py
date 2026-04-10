"""
Repository pattern implementation for database entities.
"""

from .base_repository import BaseRepository
from .property_repository import PropertyRepository

__all__ = [
    "BaseRepository",
    "PropertyRepository",
]
