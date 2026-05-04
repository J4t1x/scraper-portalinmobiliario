#!/usr/bin/env python3
"""
Initialize database tables.

This script creates all tables defined in SQLAlchemy models.
Run this after deploying to Railway or when setting up a new database.

Usage:
    python init_db.py
"""

import sys
from database import setup_database, test_connection, Base
from logger_config import get_logger
# Import all models to register them with Base
import models

logger = get_logger(__name__)


def init_database():
    """Initialize database and create all tables."""
    try:
        logger.info("Starting database initialization...")
        
        # Test connection first
        logger.info("Testing database connection...")
        if not test_connection():
            logger.error("Database connection failed. Please check your DATABASE_URL.")
            return False
        
        logger.info("Database connection successful!")
        
        # Get engine
        engine = setup_database()
        
        # Create all tables
        logger.info("Creating tables...")
        Base.metadata.create_all(bind=engine)
        
        logger.info("✅ All tables created successfully!")
        logger.info("Tables created:")
        for table in Base.metadata.sorted_tables:
            logger.info(f"  - {table.name}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False


if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
