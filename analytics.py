"""
Analytics module for property data processing and opportunity detection.

This module uses pandas for data analysis and PostgreSQL for storage.
"""

import logging
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import text
from database import get_session
from models import Property

logger = logging.getLogger(__name__)


class PropertyAnalytics:
    """Property analytics engine using pandas."""
    
    def __init__(self):
        self.session = get_session()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
    
    def calculate_price_per_m2(self) -> int:
        """
        Calculate price per m² for all properties.
        
        Returns:
            Number of properties updated
        """
        logger.info("Calculating price/m² for all properties...")
        
        query = text("""
            UPDATE properties
            SET precio_m2 = precio / superficie_util,
                updated_at = CURRENT_TIMESTAMP
            WHERE superficie_util > 0 
              AND precio > 0 
              AND (precio_m2 IS NULL OR updated_at < created_at)
        """)
        
        result = self.session.execute(query)
        self.session.commit()
        
        updated = result.rowcount
        logger.info(f"Updated {updated} properties with precio_m2")
        
        return updated
    
    def get_avg_by_comuna(self) -> List[Dict[str, Any]]:
        """
        Get average price/m² by comuna.
        
        Returns:
            List of dicts with comuna stats
        """
        logger.info("Calculating average price/m² by comuna...")
        
        df = pd.read_sql(
            """
            SELECT 
                comuna,
                COUNT(*) as total_propiedades,
                AVG(precio_m2) as avg_precio_m2,
                STDDEV(precio_m2) as std_precio_m2,
                MIN(precio_m2) as min_precio_m2,
                MAX(precio_m2) as max_precio_m2
            FROM properties
            WHERE precio_m2 IS NOT NULL
              AND comuna IS NOT NULL
            GROUP BY comuna
            ORDER BY avg_precio_m2 DESC
            """,
            self.session.bind
        )
        
        self._cache_metric('avg_by_comuna', df.to_dict('records'))
        
        return df.to_dict('records')
    
    def get_distribution_by_tipo(self) -> List[Dict[str, Any]]:
        """
        Get property distribution by type.
        
        Returns:
            List of dicts with type distribution
        """
        logger.info("Calculating distribution by property type...")
        
        df = pd.read_sql(
            """
            SELECT 
                tipo,
                COUNT(*) as total,
                AVG(precio) as avg_precio,
                AVG(precio_m2) as avg_precio_m2
            FROM properties
            WHERE tipo IS NOT NULL
            GROUP BY tipo
            ORDER BY total DESC
            """,
            self.session.bind
        )
        
        return df.to_dict('records')
    
    def detect_opportunities(self, threshold_std: float = 1.0) -> int:
        """
        Detect investment opportunities based on price/m² analysis.
        
        Args:
            threshold_std: Number of standard deviations below mean to consider opportunity
            
        Returns:
            Number of opportunities detected
        """
        logger.info(f"Detecting opportunities (threshold: {threshold_std} std)...")
        
        from models import Opportunity
        
        self.session.query(Opportunity).delete()
        
        df = pd.read_sql(
            """
            SELECT 
                id, titulo, precio, precio_m2, comuna, tipo, operacion,
                superficie_util, dormitorios, banos, url
            FROM properties
            WHERE precio_m2 IS NOT NULL
              AND comuna IS NOT NULL
            """,
            self.session.bind
        )
        
        if df.empty:
            logger.warning("No properties with precio_m2 found")
            return 0
        
        stats = df.groupby('comuna')['precio_m2'].agg(['mean', 'std', 'count']).reset_index()
        stats.columns = ['comuna', 'mean_precio_m2', 'std_precio_m2', 'count']
        
        stats = stats[stats['count'] >= 5]
        
        df_with_stats = df.merge(stats, on='comuna', how='inner')
        
        opportunities = []
        for _, row in df_with_stats.iterrows():
            threshold = row['mean_precio_m2'] - (threshold_std * row['std_precio_m2'])
            
            if row['precio_m2'] < threshold:
                diff_pct = ((row['mean_precio_m2'] - row['precio_m2']) / row['mean_precio_m2']) * 100
                
                score = min(100, diff_pct * 2)
                
                if diff_pct > 30:
                    tipo_oportunidad = 'excelente'
                elif diff_pct > 20:
                    tipo_oportunidad = 'muy_buena'
                elif diff_pct > 10:
                    tipo_oportunidad = 'buena'
                else:
                    tipo_oportunidad = 'moderada'
                
                from models import Opportunity
                opp = Opportunity(
                    property_id=row['id'],
                    tipo_oportunidad=tipo_oportunidad,
                    score=round(score, 2),
                    precio_m2_propiedad=round(row['precio_m2'], 2),
                    precio_m2_promedio_comuna=round(row['mean_precio_m2'], 2),
                    diferencia_porcentual=round(diff_pct, 2),
                    razon=f"Precio/m² {diff_pct:.1f}% bajo el promedio de {row['comuna']} ({row['tipo']})"
                )
                opportunities.append(opp)
        
        if opportunities:
            self.session.bulk_save_objects(opportunities)
            self.session.commit()
            logger.info(f"Detected and saved {len(opportunities)} opportunities")
        else:
            logger.info("No opportunities detected")
        
        return len(opportunities)
    
    def get_top_opportunities(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get top opportunities by score.
        
        Args:
            limit: Maximum number of opportunities to return
            
        Returns:
            List of opportunities with property details
        """
        df = pd.read_sql(
            f"""
            SELECT 
                o.id,
                o.tipo_oportunidad,
                o.score,
                o.precio_m2_propiedad,
                o.precio_m2_promedio_comuna,
                o.diferencia_porcentual,
                o.razon,
                p.id as property_id,
                p.titulo,
                p.precio,
                p.comuna,
                p.tipo,
                p.operacion,
                p.superficie_util,
                p.dormitorios,
                p.banos,
                p.url
            FROM opportunities o
            JOIN properties p ON o.property_id = p.id
            ORDER BY o.score DESC
            LIMIT {limit}
            """,
            self.session.bind
        )
        
        return df.to_dict('records')
    
    def _cache_metric(self, metric_name: str, metric_value: Any):
        """Cache a metric in the database."""
        from models import AnalyticsCache
        
        cache = self.session.query(AnalyticsCache).filter_by(metric_name=metric_name).first()
        
        if cache:
            cache.metric_value = metric_value
            cache.calculated_at = datetime.utcnow()
        else:
            cache = AnalyticsCache(
                metric_name=metric_name,
                metric_value=metric_value
            )
            self.session.add(cache)
        
        self.session.commit()
    
    def get_cached_metric(self, metric_name: str) -> Optional[Any]:
        """Get a cached metric from the database."""
        from models import AnalyticsCache
        
        cache = self.session.query(AnalyticsCache).filter_by(metric_name=metric_name).first()
        return cache.metric_value if cache else None


def run_analytics_pipeline():
    """Run the complete analytics pipeline."""
    logger.info("Starting analytics pipeline...")
    
    with PropertyAnalytics() as analytics:
        updated = analytics.calculate_price_per_m2()
        logger.info(f"Step 1: Updated {updated} properties with precio_m2")
        
        stats = analytics.get_avg_by_comuna()
        logger.info(f"Step 2: Calculated stats for {len(stats)} comunas")
        
        opportunities = analytics.detect_opportunities()
        logger.info(f"Step 3: Detected {opportunities} opportunities")
    
    logger.info("Analytics pipeline completed successfully")
    return {
        'properties_updated': updated,
        'comunas_analyzed': len(stats),
        'opportunities_detected': opportunities
    }


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    result = run_analytics_pipeline()
    print(f"Analytics pipeline result: {result}")
