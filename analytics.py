"""
Analytics module for property data processing and opportunity detection.

This module uses pandas for data analysis and PostgreSQL for storage.
"""

import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import text
from database import get_session
from models import Property

logger = logging.getLogger(__name__)

SCORE_WEIGHTS = {
    'precio_m2':         0.40,
    'precio_dormitorio': 0.20,
    'liquidez_comuna':   0.15,
    'antiguedad':        0.15,
    'eficiencia_m2':     0.10,
}


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
    
    def detect_opportunities(self, threshold_std: float = 0.5) -> int:
        """
        Detect investment opportunities using a multi-criteria scoring model.

        Criteria and weights (defined in SCORE_WEIGHTS):
          - precio_m2 (40%):        How far below the commune average price/m²
          - precio_dormitorio (20%): Price per bedroom vs commune average
          - liquidez_comuna (15%):  Inverse of supply (fewer listings = scarcer = better)
          - antiguedad (15%):       Freshness of the listing (newer = better signal)
          - eficiencia_m2 (10%):    Ratio útil/total surface (efficiency of usable space)

        Returns:
            Number of opportunities detected and saved
        """
        logger.info("Detecting opportunities with multi-criteria scoring...")

        from models import Opportunity

        self.session.query(Opportunity).delete()
        self.session.commit()

        df = pd.read_sql(
            """
            SELECT
                property_id, titulo, precio, precio_m2, comuna, tipo, operacion,
                superficie_util, dormitorios, banos, url, scrapeado_en
            FROM properties
            WHERE precio_m2 IS NOT NULL
              AND comuna IS NOT NULL
              AND precio > 0
              AND superficie_util > 0
            """,
            self.session.bind
        )

        if df.empty:
            logger.warning("No properties with precio_m2 found")
            return 0

        now = datetime.utcnow()

        df['scrapeado_en'] = pd.to_datetime(df['scrapeado_en'], utc=True, errors='coerce')
        df['dias_publicado'] = df['scrapeado_en'].apply(
            lambda x: (now - x.replace(tzinfo=None)).days if pd.notna(x) else 90
        )

        df['dormitorios'] = pd.to_numeric(df['dormitorios'], errors='coerce').fillna(1).clip(lower=1)
        df['precio_por_dormitorio'] = df['precio'] / df['dormitorios']

        commune_stats = df.groupby('comuna').agg(
            mean_pm2=('precio_m2', 'mean'),
            std_pm2=('precio_m2', 'std'),
            count_pm2=('precio_m2', 'count'),
            mean_ppd=('precio_por_dormitorio', 'mean'),
        ).reset_index()
        commune_stats = commune_stats[commune_stats['count_pm2'] >= 3]
        commune_stats['std_pm2'] = commune_stats['std_pm2'].fillna(commune_stats['mean_pm2'] * 0.1)

        df = df.merge(commune_stats, on='comuna', how='inner')

        global_median_supply = commune_stats['count_pm2'].median() or 1

        opportunities = []
        for _, row in df.iterrows():
            threshold = row['mean_pm2'] - (threshold_std * row['std_pm2'])
            if row['precio_m2'] >= threshold:
                continue

            reasons = []
            scores_raw = {}

            diff_pct_m2 = ((row['mean_pm2'] - row['precio_m2']) / row['mean_pm2']) * 100
            s_pm2 = min(100.0, diff_pct_m2 * (100 / 30))
            scores_raw['precio_m2'] = s_pm2
            reasons.append(f"Precio/m² {diff_pct_m2:.1f}% bajo el promedio de {row['comuna']}")

            diff_pct_ppd = ((row['mean_ppd'] - row['precio_por_dormitorio']) / row['mean_ppd']) * 100
            s_ppd = min(100.0, max(0.0, diff_pct_ppd * (100 / 25)))
            scores_raw['precio_dormitorio'] = s_ppd
            if diff_pct_ppd > 5:
                reasons.append(f"Precio por dormitorio {diff_pct_ppd:.1f}% bajo el promedio comunal")

            supply_ratio = row['count_pm2'] / global_median_supply
            s_liq = min(100.0, max(0.0, (1 - (supply_ratio - 0.5)) * 100))
            scores_raw['liquidez_comuna'] = s_liq

            dias = row['dias_publicado']
            if dias <= 7:
                s_age = 100.0
            elif dias <= 30:
                s_age = 80.0
            elif dias <= 90:
                s_age = 50.0
            else:
                s_age = 20.0
            scores_raw['antiguedad'] = s_age
            if dias <= 7:
                reasons.append("Publicada hace menos de 7 días")

            if row['superficie_util'] and row['superficie_util'] > 0:
                s_eff = min(100.0, (row['superficie_util'] / row['superficie_util']) * 100)
            else:
                s_eff = 50.0
            scores_raw['eficiencia_m2'] = s_eff

            final_score = sum(scores_raw[k] * SCORE_WEIGHTS[k] for k in SCORE_WEIGHTS)
            final_score = round(min(100.0, final_score), 2)

            if diff_pct_m2 > 30:
                tipo_oportunidad = 'excelente'
            elif diff_pct_m2 > 20:
                tipo_oportunidad = 'muy_buena'
            elif diff_pct_m2 > 10:
                tipo_oportunidad = 'buena'
            else:
                tipo_oportunidad = 'moderada'

            razon = " | ".join(reasons) if reasons else f"Precio/m² bajo el promedio de {row['comuna']}"

            from models import Opportunity
            opp = Opportunity(
                property_id=row['property_id'],
                tipo_oportunidad=tipo_oportunidad,
                score=final_score,
                precio_m2_propiedad=round(float(row['precio_m2']), 2),
                precio_m2_promedio_comuna=round(float(row['mean_pm2']), 2),
                diferencia_porcentual=round(diff_pct_m2, 2),
                razon=razon,
            )
            opportunities.append(opp)

        if opportunities:
            self.session.bulk_save_objects(opportunities)
            self.session.commit()
            logger.info(f"Detected and saved {len(opportunities)} opportunities")
        else:
            logger.info("No opportunities detected")

        return len(opportunities)
    
    def get_daily_opportunities(self, limit: int = 20, tipo_filter: str = None, comuna_filter: str = None) -> Dict[str, Any]:
        """
        Get enriched daily opportunities for the dashboard module.

        Returns a dict with:
          - featured: top opportunity with score breakdown
          - top_list: top N opportunities with reasons
          - score_summary: count by tipo_oportunidad
          - market_stats: global and per-commune averages
          - communes: commune stats sorted by avg price/m²
          - alerts: dynamic alerts based on current data
          - meta: total opportunities found, last_updated
        """
        df = pd.read_sql(
            """
            SELECT
                o.id            AS opp_id,
                o.tipo_oportunidad,
                o.score,
                o.precio_m2_propiedad,
                o.precio_m2_promedio_comuna,
                o.diferencia_porcentual,
                o.razon,
                o.created_at    AS opp_created,
                p.id            AS property_db_id,
                p.property_id,
                p.title         AS titulo,
                p.precio,
                p.comuna,
                p.tipo_propiedad AS tipo,
                p.operacion,
                p.superficie_util,
                p.dormitorios,
                p.banos,
                p.url,
                p.scraped_at    AS scrapeado_en
            FROM opportunities o
            JOIN properties p ON o.property_id = p.id
            ORDER BY o.score DESC
            """,
            self.session.bind
        )

        if df.empty:
            return {
                'featured': None,
                'top_list': [],
                'score_summary': {},
                'market_stats': {'avg_price_m2': 0, 'total_properties': 0},
                'communes': [],
                'alerts': [{'type': 'warning', 'message': 'No hay oportunidades detectadas. Ejecuta el pipeline de analítica primero.'}],
                'meta': {'total': 0, 'last_updated': None}
            }

        if tipo_filter:
            df = df[df['tipo_oportunidad'] == tipo_filter]
        if comuna_filter:
            df = df[df['comuna'] == comuna_filter]

        def build_opp_dict(row):
            razon_parts = str(row.get('razon', '') or '').split(' | ')
            return {
                'id': int(row['opp_id']) if pd.notna(row['opp_id']) else None,
                'score': round(float(row['score']), 1),
                'tipo_oportunidad': row['tipo_oportunidad'],
                'diferencia_porcentual': round(float(row['diferencia_porcentual']), 1) if pd.notna(row['diferencia_porcentual']) else 0,
                'precio_m2': int(row['precio_m2_propiedad']) if pd.notna(row['precio_m2_propiedad']) else 0,
                'precio_m2_promedio_comuna': int(row['precio_m2_promedio_comuna']) if pd.notna(row['precio_m2_promedio_comuna']) else 0,
                'razones': razon_parts,
                'property': {
                    'id': int(row['property_db_id']) if pd.notna(row['property_db_id']) else None,
                    'property_id': row['property_id'],
                    'titulo': row['titulo'],
                    'precio': int(row['precio']) if pd.notna(row['precio']) else 0,
                    'comuna': row['comuna'],
                    'tipo': row['tipo'],
                    'operacion': row['operacion'],
                    'superficie_total': int(row['superficie_util']) if pd.notna(row['superficie_util']) else 0,
                    'dormitorios': int(row['dormitorios']) if pd.notna(row['dormitorios']) else 0,
                    'banos': int(row['banos']) if pd.notna(row['banos']) else 0,
                    'url': row['url'],
                    'imagenes': [],
                },
            }

        top_list = [build_opp_dict(r) for _, r in df.head(limit).iterrows()]
        featured = top_list[0] if top_list else None

        score_summary = df['tipo_oportunidad'].value_counts().to_dict()

        market_stats = {
            'avg_price_m2': int(df['precio_m2_promedio_comuna'].mean()) if not df.empty else 0,
            'total_properties': len(df),
        }

        commune_df = df.groupby('comuna').agg(
            count=('opp_id', 'count'),
            avg_score=('score', 'mean'),
            avg_price_m2=('precio_m2_propiedad', 'mean'),
            avg_diff_pct=('diferencia_porcentual', 'mean'),
        ).reset_index().sort_values('avg_score', ascending=False)

        communes = [
            {
                'name': r['comuna'],
                'count': int(r['count']),
                'avg_score': round(float(r['avg_score']), 1),
                'avg_price_m2': int(r['avg_price_m2']),
                'avg_diff_pct': round(float(r['avg_diff_pct']), 1),
            }
            for _, r in commune_df.head(10).iterrows()
        ]

        alerts = self._build_dynamic_alerts(df)

        last_updated = None
        if 'opp_created' in df.columns and not df['opp_created'].isnull().all():
            ts = pd.to_datetime(df['opp_created'], utc=True, errors='coerce').max()
            last_updated = ts.isoformat() if pd.notna(ts) else None

        return {
            'featured': featured,
            'top_list': top_list,
            'score_summary': score_summary,
            'market_stats': market_stats,
            'communes': communes,
            'alerts': alerts,
            'meta': {
                'total': len(df),
                'last_updated': last_updated,
                'filters': {
                    'tipo': tipo_filter,
                    'comuna': comuna_filter,
                }
            }
        }

    def _build_dynamic_alerts(self, df: 'pd.DataFrame') -> List[Dict[str, str]]:
        """Generate dynamic alerts from opportunity data."""
        alerts = []
        if df.empty:
            return alerts

        excelentes = len(df[df['tipo_oportunidad'] == 'excelente'])
        if excelentes > 0:
            alerts.append({
                'type': 'highlight',
                'message': f'{excelentes} propiedad{"es" if excelentes > 1 else ""} con descuento >30% sobre el promedio comunal'
            })

        recientes = df[df['score'] >= 60]
        if not recientes.empty and 'scrapeado_en' in df.columns:
            week_ago = pd.Timestamp.utcnow() - pd.Timedelta(days=7)
            df_ts = pd.to_datetime(df['scrapeado_en'], utc=True, errors='coerce')
            nuevas = int((df_ts >= week_ago).sum())
            if nuevas > 0:
                alerts.append({
                    'type': 'new',
                    'message': f'{nuevas} oportunidad{"es" if nuevas > 1 else ""} publicada{"s" if nuevas > 1 else ""} en los últimos 7 días'
                })

        top_comuna = df.groupby('comuna')['score'].mean().idxmax() if not df.empty else None
        if top_comuna:
            avg_diff = df[df['comuna'] == top_comuna]['diferencia_porcentual'].mean()
            alerts.append({
                'type': 'commune',
                'message': f'Mejor zona del día: {top_comuna} ({avg_diff:.1f}% promedio bajo mercado)'
            })

        muy_baratas = df[df['diferencia_porcentual'] >= 25]
        if not muy_baratas.empty:
            max_diff = df['diferencia_porcentual'].max()
            alerts.append({
                'type': 'price_drop',
                'message': f'Máxima diferencia detectada: {max_diff:.1f}% bajo el promedio comunal'
            })

        return alerts[:4]

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
                p.property_id,
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
            JOIN properties p ON o.property_id = p.property_id
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
