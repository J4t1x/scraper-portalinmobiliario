"""
Property Service for high-level property operations.

Encapsulates business logic for property operations including
upsert, bulk operations, and search.
"""

from typing import List, Dict, Optional
from datetime import datetime
from db.unit_of_work import UnitOfWork
from db.repositories.property_repository import PropertyRepository
from scraper_db_integration import parse_price, parse_publication_date
from models import Property, Feature, Image, Publisher


class PropertyService:
    """
    Service for property business logic operations.
    
    Provides high-level operations for property management
    using repositories and unit of work pattern.
    """
    
    def __init__(self, uow: UnitOfWork):
        """
        Initialize PropertyService.
        
        Args:
            uow: UnitOfWork instance
        """
        self._uow = uow
        self._repo: PropertyRepository = uow.properties
    
    def upsert_property(self, property_data: Dict) -> Property:
        """
        Insert or update a property (upsert logic).
        
        Uses URL as unique identifier. Updates existing record if found,
        creates new one otherwise.
        
        Args:
            property_data: Dictionary with property data
            
        Returns:
            Property instance (created or updated)
        """
        url = property_data.get('url')
        
        if not url:
            raise ValueError("Property data must include 'url' field")
        
        # Try to find existing property by URL
        existing = self._repo.find_by_url(url)
        
        if existing:
            # Update existing property
            self._update_property(existing, property_data)
            return existing
        else:
            # Create new property
            return self._create_property(property_data)
    
    def _create_property(self, property_data: Dict) -> Property:
        """
        Create new property from data.
        
        Args:
            property_data: Property data dictionary
            
        Returns:
            Created Property instance
        """
        precio, moneda = parse_price(property_data.get('precio'))
        
        prop = Property(
            url=property_data.get('url'),
            portal_id=property_data.get('id'),
            titulo=property_data.get('titulo'),
            precio=precio,
            precio_moneda=moneda,
            precio_original=property_data.get('precio'),
            operacion=property_data.get('operacion'),
            tipo=property_data.get('tipo'),
            direccion=property_data.get('ubicacion'),
            headline=property_data.get('headline'),
            atributos=property_data.get('atributos'),
            descripcion=property_data.get('descripcion'),
            scrapeado_en=datetime.utcnow()
        )
        
        self._repo.create(prop)
        
        # Handle related entities
        self._handle_features(prop, property_data.get('caracteristicas', {}))
        self._handle_images(prop, property_data.get('imagenes', []))
        self._handle_publisher(prop, property_data.get('publicador', {}))
        
        return prop
    
    def _update_property(self, prop: Property, property_data: Dict) -> None:
        """
        Update existing property with new data.
        
        Args:
            prop: Existing Property instance
            property_data: New property data
        """
        # Update basic fields if provided
        if 'titulo' in property_data:
            prop.titulo = property_data['titulo']
        if 'headline' in property_data:
            prop.headline = property_data['headline']
        if 'precio' in property_data:
            prop.precio_original = property_data['precio']
            precio, moneda = parse_price(property_data['precio'])
            if precio:
                prop.precio = precio
            if moneda:
                prop.precio_moneda = moneda
        if 'ubicacion' in property_data:
            prop.direccion = property_data['ubicacion']
        if 'atributos' in property_data:
            prop.atributos = property_data['atributos']
        if 'operacion' in property_data:
            prop.operacion = property_data['operacion']
        if 'tipo' in property_data:
            prop.tipo = property_data['tipo']
        
        # Update detail fields if provided
        if 'descripcion' in property_data:
            prop.descripcion = property_data['descripcion']
        
        # Update timestamp
        prop.actualizado_en = datetime.utcnow()
        
        # Handle related entities
        self._handle_features(prop, property_data.get('caracteristicas', {}))
        self._handle_images(prop, property_data.get('imagenes', []))
        self._handle_publisher(prop, property_data.get('publicador', {}))
    
    def _handle_features(self, prop: Property, characteristics: Dict) -> None:
        """
        Handle features/characteristics for a property.
        
        Args:
            prop: Property instance
            characteristics: Dictionary of characteristics
        """
        # Delete existing features
        self._uow.session.query(Feature).filter(Feature.property_id == prop.id).delete()
        
        # Add new features
        for key, value in characteristics.items():
            if value:
                feature = Feature(
                    property_id=prop.id,
                    key=key,
                    value=str(value)
                )
                self._uow.session.add(feature)
    
    def _handle_images(self, prop: Property, images: List[str]) -> None:
        """
        Handle images for a property.
        
        Args:
            prop: Property instance
            images: List of image URLs
        """
        # Delete existing images
        self._uow.session.query(Image).filter(Image.property_id == prop.id).delete()
        
        # Add new images
        for i, img_url in enumerate(images):
            image = Image(
                property_id=prop.id,
                url=img_url,
                es_principal=(i == 0)
            )
            self._uow.session.add(image)
    
    def _handle_publisher(self, prop: Property, publisher_data: Dict) -> None:
        """
        Handle publisher for a property.
        
        Args:
            prop: Property instance
            publisher_data: Publisher data dictionary
        """
        # Delete existing publisher
        self._uow.session.query(Publisher).filter(Publisher.property_id == prop.id).delete()
        
        if publisher_data.get('nombre') or publisher_data.get('tipo'):
            publisher = Publisher(
                property_id=prop.id,
                nombre=publisher_data.get('nombre'),
                telefono=publisher_data.get('telefono'),
                email=publisher_data.get('email'),
                tipo=publisher_data.get('tipo')
            )
            self._uow.session.add(publisher)
    
    def bulk_insert(self, properties_data: List[Dict]) -> int:
        """
        Bulk insert multiple properties.
        
        Args:
            properties_data: List of property data dictionaries
            
        Returns:
            Number of properties inserted
        """
        count = 0
        for prop_data in properties_data:
            try:
                self.upsert_property(prop_data)
                count += 1
            except Exception as e:
                # Log error but continue with next property
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error inserting property {prop_data.get('url', 'unknown')}: {e}")
        
        return count
    
    def search_properties(
        self,
        filters: Dict,
        page: int = 1,
        per_page: int = 20
    ) -> Dict:
        """
        Search properties with filters and pagination.
        
        Args:
            filters: Dictionary of search filters
            page: Page number (1-indexed)
            per_page: Number of results per page
            
        Returns:
            Dictionary with results and pagination info
        """
        skip = (page - 1) * per_page
        
        # Get total count
        total = self._repo.count(**{k: v for k, v in filters.items() 
                                   if hasattr(Property, k) and k not in ['precio_min', 'precio_max']})
        
        # Get results
        results = self._repo.search(
            filters=filters,
            skip=skip,
            limit=per_page,
            order_by='scrapeado_en',
            descending=True
        )
        
        return {
            'results': [r.to_dict() for r in results],
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        }
    
    def get_property_by_url(self, url: str) -> Optional[Dict]:
        """
        Get property by URL.
        
        Args:
            url: Property URL
            
        Returns:
            Property data dictionary or None
        """
        prop = self._repo.find_by_url(url)
        return prop.to_dict() if prop else None
    
    def get_recent_properties(self, limit: int = 10) -> List[Dict]:
        """
        Get most recently scraped properties.
        
        Args:
            limit: Maximum number of properties to return
            
        Returns:
            List of property data dictionaries
        """
        props = self._repo.get_all(
            limit=limit,
            order_by='scrapeado_en',
            descending=True
        )
        return [p.to_dict() for p in props]
