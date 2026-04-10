"""
Integration tests for data migration.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database import setup_database, session_scope, Base, drop_tables, create_tables
from models.property import Property
from scripts.migrate_to_postgres import DataMigrator


@pytest.fixture
def test_database():
    """
    Fixture to create and teardown a test database.
    
    Uses SQLite for testing to avoid requiring PostgreSQL.
    """
    # Use in-memory SQLite for testing
    test_db_url = "sqlite:///:memory:"
    
    # Setup database
    engine = setup_database(test_db_url)
    create_tables(engine)
    
    yield test_db_url
    
    # Cleanup
    drop_tables(engine)


class TestMigrationIntegration:
    """Integration tests for data migration."""
    
    def test_migration_dry_run(self, test_database):
        """Test migration in dry-run mode."""
        # Create temporary file with test data
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write('{"id": "MLC-1", "titulo": "Prop 1", "precio": "UF 3.055", "ubicacion": "Santiago", "url": "https://example.com/1", "operacion": "venta", "tipo": "departamento"}\n')
            f.write('{"id": "MLC-2", "titulo": "Prop 2", "precio": "$ 500.000", "ubicacion": "Santiago", "url": "https://example.com/2", "operacion": "venta", "tipo": "casa"}\n')
            temp_path = f.name
        
        try:
            # Run migration in dry-run mode
            migrator = DataMigrator(
                database_url=test_database,
                dry_run=True
            )
            stats = migrator.migrate_from_file(temp_path)
            
            # Verify dry-run doesn't insert data
            with session_scope() as session:
                count = session.query(Property).count()
                assert count == 0
            
            # Verify stats
            assert stats['total_processed'] == 2
            assert stats['successful'] == 2
            assert stats['failed'] == 0
        finally:
            os.unlink(temp_path)
    
    def test_migration_with_duplicates(self, test_database):
        """Test migration with duplicate handling."""
        # Create temporary file with test data
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write('{"id": "MLC-1", "titulo": "Prop 1", "precio": "UF 3.055", "ubicacion": "Santiago", "url": "https://example.com/1", "operacion": "venta", "tipo": "departamento"}\n')
            temp_path = f.name
        
        try:
            # First migration
            migrator1 = DataMigrator(
                database_url=test_database,
                skip_duplicates=True
            )
            stats1 = migrator1.migrate_from_file(temp_path)
            
            # Verify first migration inserted data
            with session_scope() as session:
                count = session.query(Property).count()
                assert count == 1
            
            # Second migration (should skip duplicate)
            migrator2 = DataMigrator(
                database_url=test_database,
                skip_duplicates=True
            )
            stats2 = migrator2.migrate_from_file(temp_path)
            
            # Verify second migration skipped duplicate
            with session_scope() as session:
                count = session.query(Property).count()
                assert count == 1  # Still only 1 property
            
            assert stats2['duplicates'] == 1
        finally:
            os.unlink(temp_path)
    
    def test_migration_invalid_data(self, test_database):
        """Test migration with invalid data."""
        # Create temporary file with invalid data
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            # Valid property
            f.write('{"id": "MLC-1", "titulo": "Prop 1", "precio": "UF 3.055", "ubicacion": "Santiago", "url": "https://example.com/1", "operacion": "venta", "tipo": "departamento"}\n')
            # Invalid property (missing required fields)
            f.write('{"id": "MLC-2", "titulo": "Prop 2"}\n')
            temp_path = f.name
        
        try:
            migrator = DataMigrator(
                database_url=test_database,
                skip_duplicates=True
            )
            stats = migrator.migrate_from_file(temp_path)
            
            # Verify only valid property was inserted
            with session_scope() as session:
                count = session.query(Property).count()
                assert count == 1
            
            assert stats['successful'] == 1
            assert stats['failed'] == 1  # Invalid property failed
        finally:
            os.unlink(temp_path)
    
    def test_migration_json_format(self, test_database):
        """Test migration from JSON format."""
        data = {
            "metadata": {"operacion": "venta", "tipo": "departamento"},
            "propiedades": [
                {
                    "id": "MLC-1",
                    "titulo": "Prop 1",
                    "precio": "UF 3.055",
                    "ubicacion": "Santiago",
                    "url": "https://example.com/1",
                    "operacion": "venta",
                    "tipo": "departamento"
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(data, f)
            temp_path = f.name
        
        try:
            migrator = DataMigrator(
                database_url=test_database,
                skip_duplicates=True
            )
            stats = migrator.migrate_from_file(temp_path)
            
            # Verify property was inserted
            with session_scope() as session:
                count = session.query(Property).count()
                assert count == 1
            
            assert stats['successful'] == 1
        finally:
            os.unlink(temp_path)
    
    def test_migration_directory(self, test_database):
        """Test migration from directory with multiple files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create TXT file
            txt_path = os.path.join(temp_dir, 'data.txt')
            with open(txt_path, 'w') as f:
                f.write('{"id": "MLC-1", "titulo": "Prop 1", "precio": "UF 3.055", "ubicacion": "Santiago", "url": "https://example.com/1", "operacion": "venta", "tipo": "departamento"}\n')
            
            # Create JSON file
            json_path = os.path.join(temp_dir, 'data.json')
            with open(json_path, 'w') as f:
                json.dump({"propiedades": [{"id": "MLC-2", "titulo": "Prop 2", "precio": "$ 500.000", "ubicacion": "Santiago", "url": "https://example.com/2", "operacion": "venta", "tipo": "casa"}]}, f)
            
            migrator = DataMigrator(
                database_url=test_database,
                skip_duplicates=True
            )
            stats = migrator.migrate_from_directory(temp_dir)
            
            # Verify both properties were inserted
            with session_scope() as session:
                count = session.query(Property).count()
                assert count == 2
            
            assert stats['successful'] == 2
