"""
Migration script for importing scraped data into PostgreSQL.

Reads exported files (TXT/JSON/CSV) and migrates data to PostgreSQL database.
"""

import os
import sys
import json
import time
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import setup_database, session_scope, Base
from models.property import Property
from models.feature import Feature
from models.image import Image
from models.publisher import Publisher
from scripts.data_reader import DataReader
from scripts.data_validator import DataValidator


class DataMigrator:
    """
    Migrator for importing scraped data into PostgreSQL.
    """
    
    def __init__(
        self,
        database_url: Optional[str] = None,
        skip_duplicates: bool = True,
        batch_size: int = 100,
        dry_run: bool = False
    ):
        """
        Initialize migrator.
        
        Args:
            database_url: PostgreSQL connection URL
            skip_duplicates: Skip properties that already exist
            batch_size: Number of properties to insert per batch
            dry_run: Simulate migration without inserting data
        """
        self.database_url = database_url
        self.skip_duplicates = skip_duplicates
        self.batch_size = batch_size
        self.dry_run = dry_run
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'duplicates': 0,
            'errors': []
        }
    
    def migrate_from_file(self, file_path: str) -> Dict:
        """
        Migrate data from a single file.
        
        Args:
            file_path: Path to exported file
            
        Returns:
            Dictionary with migration statistics
        """
        print(f"\n📄 Reading file: {file_path}")
        
        # Read file
        try:
            properties = DataReader.read_file(file_path)
            print(f"✓ Read {len(properties)} properties from file")
        except Exception as e:
            error_msg = f"Failed to read file {file_path}: {e}"
            self.stats['errors'].append(error_msg)
            print(f"✗ {error_msg}")
            return self.stats
        
        # Migrate properties
        return self._migrate_properties(properties, file_path)
    
    def migrate_from_directory(self, directory_path: str) -> Dict:
        """
        Migrate data from all files in a directory.
        
        Args:
            directory_path: Path to directory with exported files
            
        Returns:
            Dictionary with migration statistics
        """
        print(f"\n📁 Reading directory: {directory_path}")
        
        # Read all files
        try:
            files_data = DataReader.read_directory(directory_path)
            print(f"✓ Found {len(files_data)} files")
            
            total_props = sum(len(props) for props in files_data.values())
            print(f"✓ Total properties: {total_props}")
        except Exception as e:
            error_msg = f"Failed to read directory {directory_path}: {e}"
            self.stats['errors'].append(error_msg)
            print(f"✗ {error_msg}")
            return self.stats
        
        # Migrate each file
        for filename, properties in files_data.items():
            print(f"\n{'='*60}")
            file_path = os.path.join(directory_path, filename)
            self._migrate_properties(properties, file_path)
        
        return self.stats
    
    def _migrate_properties(self, properties: List[Dict], source: str) -> Dict:
        """
        Migrate a list of properties.
        
        Args:
            properties: List of property dictionaries
            source: Source file path for logging
            
        Returns:
            Dictionary with migration statistics
        """
        if not properties:
            print(f"⚠ No properties to migrate from {source}")
            return self.stats
        
        # Validate batch
        print(f"\n🔍 Validating {len(properties)} properties...")
        valid_count, invalid_count, invalid_props = DataValidator.validate_batch(properties)
        
        if invalid_count > 0:
            print(f"⚠ Found {invalid_count} invalid properties")
            for inv in invalid_props[:5]:  # Show first 5 errors
                prop_id = inv['property'].get('id', 'unknown')
                errors = ', '.join(inv['errors'])
                print(f"  - Property {prop_id}: {errors}")
            if invalid_count > 5:
                print(f"  ... and {invalid_count - 5} more")
        
        print(f"✓ Valid: {valid_count}, Invalid: {invalid_count}")
        
        # Filter valid properties
        valid_properties = [
            prop for prop in properties
            if prop not in [inv['property'] for inv in invalid_props]
        ]
        
        if not valid_properties:
            print(f"✗ No valid properties to migrate")
            return self.stats
        
        # Setup database
        if not self.dry_run:
            try:
                setup_database(self.database_url)
                print("✓ Database connected")
            except Exception as e:
                error_msg = f"Failed to connect to database: {e}"
                self.stats['errors'].append(error_msg)
                print(f"✗ {error_msg}")
                return self.stats
        else:
            print("🔶 DRY RUN MODE - No data will be inserted")
        
        # Migrate in batches
        print(f"\n📊 Migrating {len(valid_properties)} properties...")
        start_time = time.time()
        
        for i in range(0, len(valid_properties), self.batch_size):
            batch = valid_properties[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            total_batches = (len(valid_properties) + self.batch_size - 1) // self.batch_size
            
            print(f"\n  Batch {batch_num}/{total_batches} ({len(batch)} properties)...")
            
            if not self.dry_run:
                self._insert_batch(batch)
            else:
                self.stats['successful'] += len(batch)
                self.stats['total_processed'] += len(batch)
        
        elapsed = time.time() - start_time
        print(f"\n✓ Migration completed in {elapsed:.2f} seconds")
        
        return self.stats
    
    def _insert_batch(self, properties: List[Dict]) -> None:
        """
        Insert a batch of properties into database.
        
        Args:
            properties: List of property dictionaries
        """
        with session_scope() as session:
            for prop_dict in properties:
                try:
                    self._insert_property(session, prop_dict)
                    self.stats['successful'] += 1
                except Exception as e:
                    self.stats['failed'] += 1
                    error_msg = f"Failed to insert property {prop_dict.get('id', 'unknown')}: {e}"
                    self.stats['errors'].append(error_msg)
                    print(f"    ✗ {error_msg}")
                
                self.stats['total_processed'] += 1
                
                # Progress indicator
                if self.stats['total_processed'] % 10 == 0:
                    print(f"    Processed: {self.stats['total_processed']}")
    
    def _insert_property(self, session, prop_dict: Dict) -> None:
        """
        Insert a single property and its related data.
        
        Args:
            session: SQLAlchemy session
            prop_dict: Property dictionary
        """
        # Check for duplicate by URL
        existing = session.query(Property).filter_by(url=prop_dict.get('url')).first()
        
        if existing and self.skip_duplicates:
            self.stats['duplicates'] += 1
            return
        
        # Parse location
        ubicacion = prop_dict.get('ubicacion', '')
        parts = ubicacion.split(',')
        direccion = ubicacion
        comuna = parts[-1].strip() if parts else None
        region = None
        
        # Create property
        property_obj = Property(
            url=prop_dict.get('url'),
            portal_id=prop_dict.get('id'),
            titulo=prop_dict.get('titulo'),
            precio_original=prop_dict.get('precio'),
            operacion=prop_dict.get('operacion'),
            tipo=prop_dict.get('tipo'),
            comuna=comuna,
            region=region,
            direccion=direccion,
            headline=prop_dict.get('headline'),
            atributos=prop_dict.get('atributos'),
            descripcion=prop_dict.get('descripcion'),
            scrapeado_en=datetime.utcnow()
        )
        
        # Handle features from atributos
        if prop_dict.get('atributos'):
            self._parse_and_insert_features(session, property_obj, prop_dict['atributos'])
        
        # Handle images
        if prop_dict.get('imagenes'):
            self._insert_images(session, property_obj, prop_dict['imagenes'])
        
        # Handle publisher
        if prop_dict.get('publicador'):
            self._insert_publisher(session, property_obj, prop_dict['publicador'])
        
        # Handle coordinates
        if prop_dict.get('coordenadas'):
            # Could be stored as JSON in a separate table or as features
            coords = prop_dict['coordenadas']
            if isinstance(coords, dict):
                if coords.get('lat'):
                    session.add(Feature(
                        property=property_obj,
                        key='latitud',
                        value=str(coords['lat'])
                    ))
                if coords.get('lng'):
                    session.add(Feature(
                        property=property_obj,
                        key='longitud',
                        value=str(coords['lng'])
                    ))
        
        session.add(property_obj)
    
    def _parse_and_insert_features(self, session, property_obj, atributos_str: str) -> None:
        """
        Parse attributes string and insert as features.
        
        Args:
            session: SQLAlchemy session
            property_obj: Property object
            atributos_str: Attributes string from scraper
        """
        import re
        
        # Parse common attributes
        patterns = {
            'dormitorios': r'(\d+)\s+dormitorio',
            'baños': r'(\d+)\s+baño',
            'm2_utiles': r'(\d+)\s+m²\s+útiles',
            'm2_totales': r'(\d+)\s+m²\s+totales',
            'estacionamientos': r'(\d+)\s+estacionamiento'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, atributos_str, re.IGNORECASE)
            if match:
                session.add(Feature(
                    property=property_obj,
                    key=key,
                    value=match.group(1)
                ))
    
    def _insert_images(self, session, property_obj, images: List[str]) -> None:
        """
        Insert image URLs.
        
        Args:
            session: SQLAlchemy session
            property_obj: Property object
            images: List of image URLs
        """
        for i, url in enumerate(images):
            session.add(Image(
                property=property_obj,
                url=url,
                es_principal=(i == 0)  # First image is principal
            ))
    
    def _insert_publisher(self, session, property_obj, publisher: Dict) -> None:
        """
        Insert publisher information.
        
        Args:
            session: SQLAlchemy session
            property_obj: Property object
            publisher: Publisher dictionary
        """
        session.add(Publisher(
            property=property_obj,
            nombre=publisher.get('nombre'),
            tipo=publisher.get('tipo')
        ))
    
    def generate_report(self, output_path: Optional[str] = None) -> None:
        """
        Generate migration report.
        
        Args:
            output_path: Optional path to save JSON report
        """
        print("\n" + "="*60)
        print("📊 MIGRATION REPORT")
        print("="*60)
        print(f"Total processed: {self.stats['total_processed']}")
        print(f"Successful: {self.stats['successful']}")
        print(f"Failed: {self.stats['failed']}")
        print(f"Duplicates skipped: {self.stats['duplicates']}")
        print(f"Errors: {len(self.stats['errors'])}")
        
        if self.stats['errors']:
            print("\n❌ Errors:")
            for error in self.stats['errors'][:10]:
                print(f"  - {error}")
            if len(self.stats['errors']) > 10:
                print(f"  ... and {len(self.stats['errors']) - 10} more")
        
        print("="*60)
        
        # Save JSON report if path provided
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=2, ensure_ascii=False)
            print(f"\n📄 Report saved to: {output_path}")


def main():
    """CLI entry point for migration script."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Migrate scraped data to PostgreSQL'
    )
    parser.add_argument(
        'source',
        help='Path to file or directory to migrate'
    )
    parser.add_argument(
        '--database-url',
        help='PostgreSQL connection URL (default: from DATABASE_URL env var)'
    )
    parser.add_argument(
        '--skip-duplicates',
        action='store_true',
        default=True,
        help='Skip properties that already exist (default: True)'
    )
    parser.add_argument(
        '--include-duplicates',
        action='store_false',
        dest='skip_duplicates',
        help='Include duplicate properties'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Batch size for inserts (default: 100)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate migration without inserting data'
    )
    parser.add_argument(
        '--report',
        help='Path to save JSON report'
    )
    
    args = parser.parse_args()
    
    # Get database URL from env if not provided
    database_url = args.database_url or os.getenv('DATABASE_URL')
    
    # Create migrator
    migrator = DataMigrator(
        database_url=database_url,
        skip_duplicates=args.skip_duplicates,
        batch_size=args.batch_size,
        dry_run=args.dry_run
    )
    
    # Migrate
    source_path = args.source
    if os.path.isfile(source_path):
        migrator.migrate_from_file(source_path)
    elif os.path.isdir(source_path):
        migrator.migrate_from_directory(source_path)
    else:
        print(f"✗ Error: {source_path} is not a valid file or directory")
        sys.exit(1)
    
    # Generate report
    migrator.generate_report(args.report)


if __name__ == '__main__':
    main()
