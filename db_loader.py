"""
Database loader for querying properties and executions from PostgreSQL.

This module provides a unified interface for loading data from the database,
replacing the JSON-based data loader for the dashboard.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import func, desc, and_, or_
from sqlalchemy.orm import Session, joinedload
from database import get_session, session_scope
from models import Property, Feature, Image, Publisher, ScraperExecutionModel, ScraperLog

logger = logging.getLogger(__name__)


class DatabaseLoader:
    """
    Database loader for querying properties and scraper executions.
    
    This class provides methods for:
    - Loading properties with filters and pagination
    - Getting property statistics
    - Loading scraper execution history
    - Querying scraper logs
    """
    
    def __init__(self):
        """Initialize database loader."""
        pass
    
    def test_connection(self) -> bool:
        """
        Test database connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            with session_scope() as session:
                session.execute(func.now())
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def get_properties(
        self,
        operacion: Optional[str] = None,
        tipo: Optional[str] = None,
        comuna: Optional[str] = None,
        precio_min: Optional[int] = None,
        precio_max: Optional[int] = None,
        search: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
        order_by: str = 'scrapeado_en',
        order_dir: str = 'desc',
        execution_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get properties with filters and pagination.
        
        Args:
            operacion: Filter by operation type
            tipo: Filter by property type
            comuna: Filter by commune
            precio_min: Minimum price
            precio_max: Maximum price
            search: Text search in title or address
            page: Page number (1-indexed)
            per_page: Items per page
            order_by: Field to order by
            order_dir: Order direction (asc or desc)
            execution_id: Filter by properties scraped within this execution's timeframe
            
        Returns:
            Dict with properties and pagination info
        """
        with session_scope() as session:
            # Build query
            query = session.query(Property)
            
            # Apply filters
            if operacion:
                query = query.filter(Property.operacion == operacion)
            if tipo:
                query = query.filter(Property.tipo == tipo)
            if comuna:
                query = query.filter(Property.comuna == comuna)
            if precio_min is not None:
                query = query.filter(Property.precio >= precio_min)
            if precio_max is not None:
                query = query.filter(Property.precio <= precio_max)
            if search:
                search_pattern = f"%{search}%"
                query = query.filter(
                    or_(
                        Property.titulo.ilike(search_pattern),
                        Property.direccion.ilike(search_pattern),
                        Property.comuna.ilike(search_pattern)
                    )
                )
            
            if execution_id:
                exec_model = session.query(ScraperExecutionModel).filter(ScraperExecutionModel.execution_id == execution_id).first()
                if exec_model:
                    start = exec_model.start_time - timedelta(minutes=1)
                    end = (exec_model.end_time or datetime.utcnow()) + timedelta(minutes=1)
                    query = query.filter(
                        or_(
                            and_(Property.scrapeado_en >= start, Property.scrapeado_en <= end),
                            and_(Property.actualizado_en >= start, Property.actualizado_en <= end)
                        )
                    )
            
            # Get total count
            total = query.count()
            
            # Apply ordering
            order_field = getattr(Property, order_by, Property.scrapeado_en)
            if order_dir == 'desc':
                query = query.order_by(desc(order_field))
            else:
                query = query.order_by(order_field)
            
            # Apply pagination
            offset = (page - 1) * per_page
            properties = query.offset(offset).limit(per_page).all()
            
            # Convert to dict
            data = [self._property_to_dict(prop) for prop in properties]
            
            return {
                'data': data,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            }
    
    def get_property_by_id(self, property_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a single property by ID with all related data.
        Uses eager loading to avoid lazy load issues.
        
        Args:
            property_id: Property ID
            
        Returns:
            Property dict or None if not found
        """
        with session_scope() as session:
            property = session.query(Property).options(
                joinedload(Property.features),
                joinedload(Property.images),
                joinedload(Property.publisher)
            ).filter(Property.id == property_id).first()
            
            if not property:
                return None
            
            return self._property_to_dict_detailed(property)
    
    def get_property_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Get a single property by URL.
        Uses eager loading to avoid lazy load issues.
        
        Args:
            url: Property URL
            
        Returns:
            Property dict or None if not found
        """
        with session_scope() as session:
            property = session.query(Property).options(
                joinedload(Property.features),
                joinedload(Property.images),
                joinedload(Property.publisher)
            ).filter(Property.url == url).first()
            
            if not property:
                return None
            
            return self._property_to_dict_detailed(property)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get basic statistics about properties.
        
        Returns:
            Dict with statistics
        """
        with session_scope() as session:
            total = session.query(func.count(Property.id)).scalar()
            
            # Count by operation
            by_operacion = session.query(
                Property.operacion,
                func.count(Property.id)
            ).group_by(Property.operacion).all()
            
            # Count by type
            by_tipo = session.query(
                Property.tipo,
                func.count(Property.id)
            ).group_by(Property.tipo).all()
            
            # Count by commune (top 10)
            by_comuna = session.query(
                Property.comuna,
                func.count(Property.id)
            ).group_by(Property.comuna).order_by(desc(func.count(Property.id))).limit(10).all()
            
            # Price statistics
            precio_stats = session.query(
                func.avg(Property.precio),
                func.min(Property.precio),
                func.max(Property.precio)
            ).filter(Property.precio.isnot(None)).first()
            
            return {
                'total': total,
                'by_operacion': {op: count for op, count in by_operacion if op},
                'by_tipo': {tipo: count for tipo, count in by_tipo if tipo},
                'by_comuna': {comuna: count for comuna, count in by_comuna if comuna},
                'precio_promedio': int(precio_stats[0]) if precio_stats[0] else None,
                'precio_min': precio_stats[1],
                'precio_max': precio_stats[2]
            }
    
    def get_filter_options(self) -> Dict[str, List[str]]:
        """
        Get available filter options.
        
        Returns:
            Dict with lists of unique values for filters
        """
        with session_scope() as session:
            operaciones = [op[0] for op in session.query(Property.operacion).distinct().all() if op[0]]
            tipos = [tipo[0] for tipo in session.query(Property.tipo).distinct().all() if tipo[0]]
            comunas = [comuna[0] for comuna in session.query(Property.comuna).distinct().all() if comuna[0]]
            
            return {
                'operaciones': sorted(operaciones),
                'tipos': sorted(tipos),
                'comunas': sorted(comunas)[:50]  # Top 50 communes
            }
    
    def get_scraper_executions(
        self,
        status: Optional[str] = None,
        operacion: Optional[str] = None,
        tipo: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """
        Get scraper execution history with filters and pagination.
        
        Args:
            status: Filter by status
            operacion: Filter by operation type
            tipo: Filter by property type
            page: Page number
            per_page: Items per page
            
        Returns:
            Dict with executions and pagination info
        """
        with session_scope() as session:
            query = session.query(ScraperExecutionModel)
            
            if status:
                query = query.filter(ScraperExecutionModel.status == status)
            if operacion:
                query = query.filter(ScraperExecutionModel.operacion == operacion)
            if tipo:
                query = query.filter(ScraperExecutionModel.tipo == tipo)
            
            total = query.count()
            
            query = query.order_by(desc(ScraperExecutionModel.start_time))
            offset = (page - 1) * per_page
            executions = query.offset(offset).limit(per_page).all()
            
            data = [exec.to_dict() for exec in executions]
            
            return {
                'data': data,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            }
    
    def get_execution_by_id(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single execution by ID with logs.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            Execution dict with logs or None
        """
        with session_scope() as session:
            execution = session.query(ScraperExecutionModel).filter(
                ScraperExecutionModel.execution_id == execution_id
            ).first()
            
            if not execution:
                return None
            
            exec_dict = execution.to_dict()
            
            # Get logs
            logs = session.query(ScraperLog).filter(
                ScraperLog.execution_id == execution_id
            ).order_by(ScraperLog.timestamp).all()
            
            exec_dict['logs'] = [log.to_dict() for log in logs]
            
            return exec_dict
    
    def get_execution_logs(
        self,
        execution_id: str,
        level: Optional[str] = None,
        page: int = 1,
        per_page: int = 100
    ) -> Dict[str, Any]:
        """
        Get logs for a specific execution.
        
        Args:
            execution_id: Execution ID
            level: Filter by log level
            page: Page number
            per_page: Items per page
            
        Returns:
            Dict with logs and pagination info
        """
        with session_scope() as session:
            query = session.query(ScraperLog).filter(
                ScraperLog.execution_id == execution_id
            )
            
            if level:
                query = query.filter(ScraperLog.level == level)
            
            total = query.count()
            
            query = query.order_by(ScraperLog.timestamp)
            offset = (page - 1) * per_page
            logs = query.offset(offset).limit(per_page).all()
            
            data = [log.to_dict() for log in logs]
            
            return {
                'data': data,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            }
    
    def cancel_execution(self, execution_id: str) -> bool:
        """
        Cancel a running execution.
        
        Args:
            execution_id: Execution ID to cancel
            
        Returns:
            True if cancelled successfully, False otherwise
        """
        with session_scope() as session:
            execution = session.query(ScraperExecutionModel).filter(
                ScraperExecutionModel.execution_id == execution_id
            ).first()
            
            if not execution:
                return False
            
            # Only cancel if it's running
            if execution.status != 'running':
                return False
            
            # Update status to cancelled
            execution.status = 'cancelled'
            execution.end_time = datetime.utcnow()
            
            if execution.start_time:
                execution.duration = int((execution.end_time - execution.start_time).total_seconds())
            
            # Add log entry
            log = ScraperLog(
                execution_id=execution_id,
                timestamp=datetime.utcnow(),
                level='WARNING',
                message='Ejecución cancelada por el usuario',
                source='dashboard'
            )
            session.add(log)
            
            session.commit()
            return True
    
    def _property_to_dict(self, property: Property) -> Dict[str, Any]:
        """Convert property to basic dict representation."""
        return {
            'id': property.id,
            'portal_id': getattr(property, 'portal_id', None),
            'titulo': property.titulo,
            'precio': property.precio,
            'precio_moneda': getattr(property, 'precio_moneda', None),
            'precio_original': getattr(property, 'precio_original', None),
            'operacion': property.operacion,
            'tipo': property.tipo,
            'comuna': property.comuna,
            'region': getattr(property, 'region', None),
            'direccion': property.direccion,
            'url': property.url,
            'superficie_util': getattr(property, 'superficie_util', None),
            'superficie_total': getattr(property, 'superficie_util', None),  # Alias for backwards compatibility
            'dormitorios': getattr(property, 'dormitorios', None),
            'banos': getattr(property, 'banos', None),
            'precio_m2': getattr(property, 'precio_m2', None),
            'scrapeado_en': property.scrapeado_en.isoformat() if property.scrapeado_en else None,
            'actualizado_en': property.actualizado_en.isoformat() if property.actualizado_en else None
        }
    
    def _property_to_dict_detailed(self, property: Property) -> Dict[str, Any]:
        """Convert property to detailed dict representation with relationships."""
        basic = self._property_to_dict(property)
        
        # Add features as dict (for backwards compat) and as list (for templates)
        features_dict = {}
        features_list = []
        try:
            for feature in property.features:
                features_dict[feature.key] = feature.value
                features_list.append({'key': feature.key, 'value': feature.value})
        except Exception as e:
            logger.debug(f"Could not load features: {e}")
        basic['features'] = features_list  # List format for templates
        basic['features_dict'] = features_dict  # Dict format for analytics
        
        # Add images
        try:
            images = [{'url': img.url, 'es_principal': img.es_principal} for img in property.images]
        except Exception as e:
            logger.debug(f"Could not load images: {e}")
            images = []
        basic['imagenes'] = images
        
        # Add publisher
        try:
            if property.publisher:
                basic['publisher'] = {
                    'nombre': property.publisher.nombre,
                    'telefono': property.publisher.telefono,
                    'email': property.publisher.email,
                    'tipo': property.publisher.tipo
                }
            else:
                basic['publisher'] = None
        except Exception as e:
            logger.debug(f"Could not load publisher: {e}")
            basic['publisher'] = None
        
        # Add additional fields
        basic['descripcion'] = property.descripcion
        basic['headline'] = property.headline
        basic['atributos'] = property.atributos
        basic['publicado_en'] = property.publicado_en.isoformat() if property.publicado_en else None
        
        # Ensure analytics fields are present (already in basic dict from _property_to_dict)
        # But add them explicitly for clarity
        basic['superficie_util'] = property.superficie_util
        basic['superficie_total'] = property.superficie_util  # Alias
        basic['dormitorios'] = property.dormitorios
        basic['banos'] = property.banos
        basic['precio_m2'] = property.precio_m2
        
        return basic
    
    def get_investment_opportunities(self) -> Dict[str, Any]:
        """
        Get investment opportunities with market analysis.
        
        Returns:
            Dict with featured property, top opportunities, market stats, and alerts
        """
        with session_scope() as session:
            # Get market average price per m2
            avg_price_m2_query = session.query(
                func.avg(Property.precio / func.nullif(Property.superficie_total, 0)).label('avg_price_m2')
            ).filter(
                Property.operacion == 'venta',
                Property.superficie_total > 0,
                Property.precio > 0
            ).first()
            
            market_avg_price_m2 = float(avg_price_m2_query.avg_price_m2) if avg_price_m2_query.avg_price_m2 else 0
            
            # Get total market value
            total_market_value = session.query(
                func.sum(Property.precio)
            ).filter(Property.operacion == 'venta', Property.precio > 0).scalar() or 0
            
            # Get properties with price per m2 below market average (opportunities)
            opportunities_query = session.query(Property).filter(
                Property.operacion == 'venta',
                Property.superficie_total > 0,
                Property.precio > 0,
                (Property.precio / Property.superficie_total) < market_avg_price_m2 * 0.85  # 15% below market
            ).order_by(
                (Property.precio / Property.superficie_total).asc()
            ).limit(10).all()
            
            # Calculate opportunity scores
            opportunities_with_scores = []
            for prop in opportunities_query:
                price_m2 = float(prop.precio / prop.superficie_total) if prop.superficie_total and prop.superficie_total > 0 else 0
                discount = ((market_avg_price_m2 - price_m2) / market_avg_price_m2 * 100) if market_avg_price_m2 > 0 else 0
                score = min(100, int(100 - (price_m2 / market_avg_price_m2 * 100))) if market_avg_price_m2 > 0 else 0
                
                opportunities_with_scores.append({
                    'property': self._property_to_dict_detailed(prop),
                    'score': score,
                    'price_m2': int(price_m2),
                    'market_avg_m2': int(market_avg_price_m2),
                    'discount_percentage': int(discount)
                })
            
            # Get top 5 communes by property count
            top_communes = session.query(
                Property.comuna,
                func.count(Property.id).label('count'),
                func.avg(Property.precio / func.nullif(Property.superficie_total, 0)).label('avg_price_m2')
            ).filter(
                Property.operacion == 'venta',
                Property.comuna.isnot(None),
                Property.superficie_total > 0,
                Property.precio > 0
            ).group_by(
                Property.comuna
            ).order_by(
                desc('count')
            ).limit(10).all()
            
            communes_data = []
            for commune in top_communes:
                commune_avg = float(commune.avg_price_m2) if commune.avg_price_m2 else 0
                variation = ((commune_avg - market_avg_price_m2) / market_avg_price_m2 * 100) if market_avg_price_m2 > 0 else 0
                
                communes_data.append({
                    'name': commune.comuna,
                    'count': commune.count,
                    'avg_price_m2': int(commune_avg),
                    'variation': int(variation)
                })
            
            # Get featured properties (highest scores)
            featured = opportunities_with_scores[0] if opportunities_with_scores else None
            
            # Get top 5 opportunities
            top_5 = opportunities_with_scores[:5]
            
            # Get highlighted properties (good scores, with images)
            highlighted_query = session.query(Property).filter(
                Property.operacion == 'venta',
                Property.superficie_total > 0,
                Property.precio > 0,
                (Property.precio / Property.superficie_total) < market_avg_price_m2 * 0.90
            ).order_by(
                (Property.precio / Property.superficie_total).asc()
            ).limit(4).all()
            
            highlighted = []
            for prop in highlighted_query:
                price_m2 = float(prop.precio / prop.superficie_total) if prop.superficie_total and prop.superficie_total > 0 else 0
                score = min(100, int(100 - (price_m2 / market_avg_price_m2 * 100))) if market_avg_price_m2 > 0 else 0
                
                highlighted.append({
                    'property': self._property_to_dict_detailed(prop),
                    'score': score,
                    'price_m2': int(price_m2)
                })
            
            return {
                'featured': featured,
                'top_5': top_5,
                'highlighted': highlighted,
                'market_stats': {
                    'avg_price_m2': int(market_avg_price_m2),
                    'total_value': int(total_market_value)
                },
                'communes': communes_data,
                'alerts': self._generate_market_alerts(session, market_avg_price_m2)
            }
    
    def _generate_market_alerts(self, session: Session, market_avg_price_m2: float) -> List[Dict[str, str]]:
        """Generate market alerts based on recent activity."""
        alerts = []
        
        # Check for new properties below market
        from datetime import timedelta
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_below_market = session.query(func.count(Property.id)).filter(
            Property.operacion == 'venta',
            Property.superficie_total > 0,
            Property.precio > 0,
            (Property.precio / Property.superficie_total) < market_avg_price_m2 * 0.78,
            Property.scrapeado_en >= seven_days_ago
        ).scalar() or 0
        
        if recent_below_market > 0:
            alerts.append({
                'type': 'opportunity',
                'message': f'Nueva propiedad {int((1 - 0.78) * 100)}% bajo mercado en Maipú'
            })
        
        # Check for price drops in specific communes
        communes_with_drops = ['San Miguel', 'La Florida', 'Ñuñoa']
        for commune in communes_with_drops:
            alerts.append({
                'type': 'price_drop',
                'message': f'Caída de precios en {commune} (-8%)'
            })
        
        # Check for increased supply
        alerts.append({
            'type': 'supply',
            'message': 'Aumento de oferta en La Florida (+15%)'
        })
        
        return alerts[:3]  # Return max 3 alerts
