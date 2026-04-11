# SPEC-MVP-001: Implementación de Arquitectura MVP con Contenedor Único

**Estado:** 🚧 Pendiente  
**Prioridad:** Alta  
**Estimación:** 6 días  
**Asignado a:** AI Dev Engine  
**Fecha creación:** 2026-04-10  

---

## 📋 Resumen

Implementar la arquitectura MVP del Portal Inmobiliario Scraper con un solo contenedor Docker que incluya PostgreSQL, Python, Selenium, Flask, pandas y Ollama para analítica básica y detección de oportunidades de inversión.

---

## 🎯 Objetivos

1. Crear Dockerfile único que incluya PostgreSQL + Python + Chrome
2. Implementar módulo de analítica con pandas (`analytics.py`)
3. Crear tablas `opportunities` y `analytics_cache` en PostgreSQL
4. Desarrollar pipeline de detección de oportunidades
5. Actualizar dashboard con página de oportunidades
6. Integrar agente IA ligero (Ollama) para interpretación de insights

---

## 📐 Diseño Técnico

### 1. Dockerfile MVP (Contenedor Único)

**Archivo:** `Dockerfile.mvp`

```dockerfile
FROM python:3.11-slim

# Metadata
LABEL maintainer="ja-viers"
LABEL description="Portal Inmobiliario Scraper MVP - Single Container"

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    DISPLAY=:99 \
    PGDATA=/var/lib/postgresql/data

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    # PostgreSQL
    postgresql postgresql-contrib \
    # Chrome y Selenium
    wget gnupg ca-certificates apt-transport-https unzip curl xvfb \
    # Utilidades
    supervisor procps \
    && rm -rf /var/lib/apt/lists/*

# Instalar Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Instalar ChromeDriver
RUN CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d '.' -f 1) \
    && CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}") \
    && wget -q "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip" \
    && unzip chromedriver_linux64.zip \
    && mv chromedriver /usr/local/bin/ \
    && chmod +x /usr/local/bin/chromedriver \
    && rm chromedriver_linux64.zip

# Crear usuario para PostgreSQL y aplicación
RUN useradd -m -u 1000 scraper && \
    mkdir -p /app /app/output /var/lib/postgresql/data && \
    chown -R postgres:postgres /var/lib/postgresql && \
    chown -R scraper:scraper /app

# Configurar PostgreSQL
USER postgres
RUN /etc/init.d/postgresql start && \
    psql --command "CREATE USER scraper WITH SUPERUSER PASSWORD 'scraper123';" && \
    createdb -O scraper portalinmobiliario && \
    /etc/init.d/postgresql stop

# Cambiar a usuario scraper
USER scraper
WORKDIR /app

# Copiar requirements y instalar dependencias Python
COPY --chown=scraper:scraper requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY --chown=scraper:scraper . .

# Copiar configuración de Supervisor
USER root
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Exponer puerto Flask
EXPOSE 5000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Entrypoint con Supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
```

### 2. Configuración de Supervisor

**Archivo:** `supervisord.conf`

```ini
[supervisord]
nodaemon=true
user=root

[program:postgresql]
command=/usr/lib/postgresql/15/bin/postgres -D /var/lib/postgresql/data
user=postgres
autostart=true
autorestart=true
priority=1
stdout_logfile=/var/log/postgresql.log
stderr_logfile=/var/log/postgresql_err.log

[program:flask]
command=python /app/app.py
directory=/app
user=scraper
autostart=true
autorestart=true
priority=10
stdout_logfile=/var/log/flask.log
stderr_logfile=/var/log/flask_err.log
environment=DATABASE_URL="postgresql://scraper:scraper123@localhost:5432/portalinmobiliario"

[program:scheduler]
command=python /app/main.py --scheduler start
directory=/app
user=scraper
autostart=true
autorestart=true
priority=20
stdout_logfile=/var/log/scheduler.log
stderr_logfile=/var/log/scheduler_err.log
```

### 3. Módulo de Analítica

**Archivo:** `analytics.py`

```python
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
from models import Property, Opportunity, AnalyticsCache

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
        
        # Query properties without precio_m2
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
        
        # Cache results
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
        
        # Clear existing opportunities
        self.session.query(Opportunity).delete()
        
        # Read all properties with precio_m2
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
        
        # Calculate stats by comuna
        stats = df.groupby('comuna')['precio_m2'].agg(['mean', 'std', 'count']).reset_index()
        stats.columns = ['comuna', 'mean_precio_m2', 'std_precio_m2', 'count']
        
        # Filter comunas with enough data (at least 5 properties)
        stats = stats[stats['count'] >= 5]
        
        # Merge stats with properties
        df_with_stats = df.merge(stats, on='comuna', how='inner')
        
        # Detect opportunities
        opportunities = []
        for _, row in df_with_stats.iterrows():
            threshold = row['mean_precio_m2'] - (threshold_std * row['std_precio_m2'])
            
            if row['precio_m2'] < threshold:
                diff_pct = ((row['mean_precio_m2'] - row['precio_m2']) / row['mean_precio_m2']) * 100
                
                # Calculate score (0-100)
                score = min(100, diff_pct * 2)
                
                # Determine opportunity type
                if diff_pct > 30:
                    tipo_oportunidad = 'excelente'
                elif diff_pct > 20:
                    tipo_oportunidad = 'muy_buena'
                elif diff_pct > 10:
                    tipo_oportunidad = 'buena'
                else:
                    tipo_oportunidad = 'moderada'
                
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
        
        # Save opportunities
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
        cache = self.session.query(AnalyticsCache).filter_by(metric_name=metric_name).first()
        return cache.metric_value if cache else None


def run_analytics_pipeline():
    """Run the complete analytics pipeline."""
    logger.info("Starting analytics pipeline...")
    
    with PropertyAnalytics() as analytics:
        # Step 1: Calculate price/m²
        updated = analytics.calculate_price_per_m2()
        logger.info(f"Step 1: Updated {updated} properties with precio_m2")
        
        # Step 2: Calculate averages by comuna
        stats = analytics.get_avg_by_comuna()
        logger.info(f"Step 2: Calculated stats for {len(stats)} comunas")
        
        # Step 3: Detect opportunities
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
```

### 4. Modelos de Base de Datos

**Archivo:** `models/opportunity.py`

```python
"""
Opportunity model for investment opportunities.
"""

from sqlalchemy import Column, String, Integer, Numeric, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Opportunity(Base):
    """Investment opportunity detected by analytics."""
    
    __tablename__ = 'opportunities'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    property_id = Column(String(50), ForeignKey('properties.id'), nullable=False)
    tipo_oportunidad = Column(String(50), nullable=False)  # excelente, muy_buena, buena, moderada
    score = Column(Numeric(5, 2), nullable=False)  # 0-100
    precio_m2_propiedad = Column(Numeric(12, 2))
    precio_m2_promedio_comuna = Column(Numeric(12, 2))
    diferencia_porcentual = Column(Numeric(5, 2))
    razon = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    property = relationship("Property", back_populates="opportunities")
    
    def __repr__(self):
        return f"<Opportunity(id={self.id}, property_id={self.property_id}, score={self.score})>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'property_id': self.property_id,
            'tipo_oportunidad': self.tipo_oportunidad,
            'score': float(self.score) if self.score else None,
            'precio_m2_propiedad': float(self.precio_m2_propiedad) if self.precio_m2_propiedad else None,
            'precio_m2_promedio_comuna': float(self.precio_m2_promedio_comuna) if self.precio_m2_promedio_comuna else None,
            'diferencia_porcentual': float(self.diferencia_porcentual) if self.diferencia_porcentual else None,
            'razon': self.razon,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
```

**Archivo:** `models/analytics_cache.py`

```python
"""
Analytics cache model for storing computed metrics.
"""

from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from database import Base


class AnalyticsCache(Base):
    """Cache for analytics metrics."""
    
    __tablename__ = 'analytics_cache'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_name = Column(String(100), unique=True, nullable=False)
    metric_value = Column(JSONB, nullable=False)
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<AnalyticsCache(metric_name={self.metric_name})>"
```

### 5. Migración de Base de Datos

**Archivo:** `migrations/versions/003_add_opportunities.py`

```python
"""Add opportunities and analytics_cache tables

Revision ID: 003
Revises: 002
Create Date: 2026-04-10
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # Create opportunities table
    op.create_table(
        'opportunities',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('property_id', sa.String(length=50), nullable=False),
        sa.Column('tipo_oportunidad', sa.String(length=50), nullable=False),
        sa.Column('score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('precio_m2_propiedad', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('precio_m2_promedio_comuna', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('diferencia_porcentual', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('razon', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_opportunities_property', 'opportunities', ['property_id'])
    op.create_index('idx_opportunities_score', 'opportunities', ['score'], unique=False, postgresql_ops={'score': 'DESC'})
    
    # Create analytics_cache table
    op.create_table(
        'analytics_cache',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('metric_value', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('calculated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('metric_name')
    )


def downgrade():
    op.drop_table('analytics_cache')
    op.drop_index('idx_opportunities_score', table_name='opportunities')
    op.drop_index('idx_opportunities_property', table_name='opportunities')
    op.drop_table('opportunities')
```

### 6. API Endpoints para Oportunidades

**Archivo:** `api/opportunities.py`

```python
"""
API endpoints for opportunities.
"""

from flask import Blueprint, jsonify, request
from analytics import PropertyAnalytics

bp = Blueprint('opportunities', __name__, url_prefix='/api/opportunities')


@bp.route('/', methods=['GET'])
def get_opportunities():
    """Get top opportunities."""
    limit = request.args.get('limit', 20, type=int)
    tipo = request.args.get('tipo', None, type=str)
    comuna = request.args.get('comuna', None, type=str)
    
    with PropertyAnalytics() as analytics:
        opportunities = analytics.get_top_opportunities(limit=limit)
    
    # Filter by tipo if provided
    if tipo:
        opportunities = [o for o in opportunities if o['tipo'] == tipo]
    
    # Filter by comuna if provided
    if comuna:
        opportunities = [o for o in opportunities if o['comuna'] == comuna]
    
    return jsonify({
        'total': len(opportunities),
        'opportunities': opportunities
    })


@bp.route('/stats', methods=['GET'])
def get_stats():
    """Get opportunity statistics."""
    with PropertyAnalytics() as analytics:
        stats = analytics.session.execute("""
            SELECT 
                tipo_oportunidad,
                COUNT(*) as total,
                AVG(score) as avg_score,
                AVG(diferencia_porcentual) as avg_diff_pct
            FROM opportunities
            GROUP BY tipo_oportunidad
            ORDER BY avg_score DESC
        """).fetchall()
    
    return jsonify({
        'stats': [
            {
                'tipo': row[0],
                'total': row[1],
                'avg_score': float(row[2]) if row[2] else 0,
                'avg_diff_pct': float(row[3]) if row[3] else 0
            }
            for row in stats
        ]
    })


@bp.route('/run-analytics', methods=['POST'])
def run_analytics():
    """Run analytics pipeline manually."""
    from analytics import run_analytics_pipeline
    
    result = run_analytics_pipeline()
    
    return jsonify({
        'success': True,
        'result': result
    })
```

### 7. Integración con Ollama

**Archivo:** `ai/agent.py`

```python
"""
AI agent for interpreting analytics insights using Ollama.
"""

import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5-coder:1.5b"


class AnalyticsAgent:
    """AI agent for analytics interpretation."""
    
    def __init__(self, model: str = MODEL, ollama_url: str = OLLAMA_URL):
        self.model = model
        self.ollama_url = ollama_url
    
    def ask(self, question: str, context: Dict[str, Any]) -> str:
        """
        Ask the agent a question with analytics context.
        
        Args:
            question: User's question
            context: Analytics insights (opportunities, stats, etc.)
            
        Returns:
            Agent's response
        """
        prompt = self._build_prompt(question, context)
        
        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "max_tokens": 500
                    }
                },
                timeout=30
            )
            response.raise_for_status()
            
            return response.json()["response"]
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Ollama: {e}")
            return "Lo siento, no pude procesar tu pregunta en este momento."
    
    def _build_prompt(self, question: str, context: Dict[str, Any]) -> str:
        """Build prompt for the agent."""
        return f"""Eres un asistente de analítica inmobiliaria experto.

Tu tarea es responder preguntas sobre oportunidades de inversión en propiedades.

CONTEXTO (insights ya calculados):
{self._format_context(context)}

PREGUNTA DEL USUARIO:
{question}

INSTRUCCIONES:
- Responde de forma concisa y clara
- Usa los datos del contexto, NO inventes números
- Si no tienes suficiente información, dilo
- Menciona las mejores oportunidades si es relevante
- Usa formato markdown para listas y énfasis

RESPUESTA:"""
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context for the prompt."""
        formatted = []
        
        if 'opportunities' in context:
            formatted.append(f"Total de oportunidades: {len(context['opportunities'])}")
            
            if context['opportunities']:
                formatted.append("\nTop 5 oportunidades:")
                for i, opp in enumerate(context['opportunities'][:5], 1):
                    formatted.append(
                        f"{i}. {opp['titulo']} - {opp['comuna']} "
                        f"(Score: {opp['score']:.1f}, "
                        f"Precio/m²: ${opp['precio_m2_propiedad']:,.0f}, "
                        f"Ahorro: {opp['diferencia_porcentual']:.1f}%)"
                    )
        
        if 'stats_by_comuna' in context:
            formatted.append("\n\nEstadísticas por comuna:")
            for stat in context['stats_by_comuna'][:5]:
                formatted.append(
                    f"- {stat['comuna']}: "
                    f"Promedio ${stat['avg_precio_m2']:,.0f}/m² "
                    f"({stat['total_propiedades']} propiedades)"
                )
        
        return "\n".join(formatted) if formatted else "No hay datos disponibles"


# API endpoint
from flask import Blueprint, request, jsonify

bp = Blueprint('agent', __name__, url_prefix='/api/agent')

@bp.route('/chat', methods=['POST'])
def chat():
    """Chat with the AI agent."""
    data = request.get_json()
    question = data.get('question', '')
    
    if not question:
        return jsonify({'error': 'Question is required'}), 400
    
    # Get context from analytics
    from analytics import PropertyAnalytics
    
    with PropertyAnalytics() as analytics:
        opportunities = analytics.get_top_opportunities(limit=10)
        stats_by_comuna = analytics.get_avg_by_comuna()
    
    context = {
        'opportunities': opportunities,
        'stats_by_comuna': stats_by_comuna
    }
    
    # Ask agent
    agent = AnalyticsAgent()
    response = agent.ask(question, context)
    
    return jsonify({
        'question': question,
        'response': response
    })
```

---

## 📝 Tareas de Implementación

### Fase 1: Docker Único (1 día)
- [ ] Crear `Dockerfile.mvp` con PostgreSQL + Python + Chrome
- [ ] Crear `supervisord.conf` para gestionar procesos
- [ ] Crear script de inicialización de PostgreSQL
- [ ] Probar build y ejecución del contenedor
- [ ] Validar que PostgreSQL y Flask arrancan correctamente

### Fase 2: Módulo de Analítica (1 día)
- [ ] Crear `analytics.py` con clase `PropertyAnalytics`
- [ ] Implementar `calculate_price_per_m2()`
- [ ] Implementar `get_avg_by_comuna()`
- [ ] Implementar `get_distribution_by_tipo()`
- [ ] Implementar `detect_opportunities()`
- [ ] Crear tests unitarios para analítica

### Fase 3: Modelos y Migraciones (0.5 días)
- [ ] Crear modelo `Opportunity`
- [ ] Crear modelo `AnalyticsCache`
- [ ] Crear migración `003_add_opportunities.py`
- [ ] Ejecutar migración en contenedor
- [ ] Validar estructura de tablas

### Fase 4: API de Oportunidades (0.5 días)
- [ ] Crear `api/opportunities.py`
- [ ] Implementar endpoint `GET /api/opportunities/`
- [ ] Implementar endpoint `GET /api/opportunities/stats`
- [ ] Implementar endpoint `POST /api/opportunities/run-analytics`
- [ ] Probar endpoints con Postman/curl

### Fase 5: Dashboard de Oportunidades (1 día)
- [ ] Crear template `templates/oportunidades.html`
- [ ] Implementar tabla de oportunidades con DataTables
- [ ] Agregar filtros (comuna, tipo, score mínimo)
- [ ] Agregar gráficos con Chart.js
- [ ] Integrar con API de oportunidades

### Fase 6: Agente IA (1 día)
- [ ] Crear `ai/agent.py` con clase `AnalyticsAgent`
- [ ] Implementar método `ask()` con llamada a Ollama
- [ ] Crear endpoint `/api/agent/chat`
- [ ] Crear interfaz de chat en dashboard
- [ ] Probar con preguntas de ejemplo

### Fase 7: Testing y Documentación (1 día)
- [ ] Escribir tests de integración
- [ ] Probar flujo completo (scraping → analítica → dashboard)
- [ ] Actualizar README.md con instrucciones MVP
- [ ] Crear guía de uso del agente IA
- [ ] Documentar métricas y KPIs

---

## ✅ Criterios de Aceptación

1. **Contenedor único funcional:**
   - Build exitoso en < 5 minutos
   - PostgreSQL inicia automáticamente
   - Flask accesible en puerto 5000
   - Uso de RAM < 2GB

2. **Analítica funcional:**
   - Calcula precio/m² correctamente
   - Detecta al menos 10 oportunidades en dataset de prueba
   - Pipeline completo ejecuta en < 10 segundos para 1000 propiedades

3. **Dashboard actualizado:**
   - Página de oportunidades muestra top 20
   - Filtros funcionan correctamente
   - Gráficos se renderizan sin errores

4. **Agente IA operativo:**
   - Responde en < 5 segundos
   - Usa contexto de oportunidades
   - No inventa datos

5. **Tests pasando:**
   - Coverage > 70%
   - Tests de integración pasan
   - No errores en logs

---

## 🧪 Plan de Testing

### Tests Unitarios

```python
# tests/test_analytics.py
def test_calculate_price_per_m2():
    """Test price/m² calculation."""
    # Setup: Insert test properties
    # Execute: Run calculate_price_per_m2()
    # Assert: precio_m2 is calculated correctly

def test_detect_opportunities():
    """Test opportunity detection."""
    # Setup: Insert properties with known prices
    # Execute: Run detect_opportunities()
    # Assert: Correct opportunities are detected

def test_get_avg_by_comuna():
    """Test comuna averages."""
    # Setup: Insert properties in different comunas
    # Execute: Run get_avg_by_comuna()
    # Assert: Averages are correct
```

### Tests de Integración

```bash
# Test completo del pipeline
docker exec scraper-mvp python -c "
from analytics import run_analytics_pipeline
result = run_analytics_pipeline()
assert result['opportunities_detected'] > 0
print('✅ Analytics pipeline OK')
"

# Test de API
curl http://localhost:5000/api/opportunities/ | jq '.total'

# Test de agente IA
curl -X POST http://localhost:5000/api/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Cuáles son las mejores oportunidades?"}' \
  | jq '.response'
```

---

## 📊 Métricas de Éxito

| Métrica | Objetivo | Medición |
|---------|----------|----------|
| Build time | < 5 min | `time docker build` |
| RAM usage | < 2GB | `docker stats` |
| CPU usage (idle) | < 50% | `docker stats` |
| Scraping time | < 2 min/50 props | Logs |
| Analytics time | < 10 seg/1000 props | Logs |
| Dashboard response | < 1 seg | Browser DevTools |
| Agent response | < 5 seg | Browser DevTools |
| Test coverage | > 70% | `pytest --cov` |

---

## 🚀 Deployment

### Build y Run

```bash
# Build
docker build -f Dockerfile.mvp -t portalinmobiliario:mvp .

# Run
docker run -d \
  --name scraper-mvp \
  -p 5000:5000 \
  -v $(pwd)/output:/app/output \
  -e OLLAMA_URL=http://host.docker.internal:11434/api/generate \
  portalinmobiliario:mvp

# Logs
docker logs -f scraper-mvp

# Health check
curl http://localhost:5000/health
```

### Comandos Útiles

```bash
# Ejecutar scraping
docker exec scraper-mvp python main.py --operacion venta --tipo departamento --max-pages 2

# Ejecutar analítica
docker exec scraper-mvp python -c "from analytics import run_analytics_pipeline; run_analytics_pipeline()"

# Conectar a PostgreSQL
docker exec -it scraper-mvp psql -U scraper -d portalinmobiliario

# Ver oportunidades
docker exec scraper-mvp python -c "from analytics import PropertyAnalytics; print(PropertyAnalytics().get_top_opportunities())"
```

---

## 📚 Referencias

- [docs/MVP-ARCHITECTURE.md](../MVP-ARCHITECTURE.md) - Arquitectura completa
- [docs/ARCHITECTURE.md](../ARCHITECTURE.md) - Arquitectura actual
- [README.md](../../README.md) - Documentación general
- [Ollama Documentation](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [Supervisor Documentation](http://supervisord.org/)

---

**Próximos pasos:** Ejecutar `/cascade-dev SPEC-MVP-001` para implementación automatizada.
