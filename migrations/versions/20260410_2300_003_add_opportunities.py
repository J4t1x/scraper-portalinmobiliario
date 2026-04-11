"""Add opportunities and analytics_cache tables

Revision ID: 003
Revises: 002
Create Date: 2026-04-10 23:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add analytics fields to properties table
    op.add_column('properties', sa.Column('superficie_util', sa.Integer(), nullable=True))
    op.add_column('properties', sa.Column('dormitorios', sa.Integer(), nullable=True))
    op.add_column('properties', sa.Column('banos', sa.Integer(), nullable=True))
    op.add_column('properties', sa.Column('precio_m2', sa.Integer(), nullable=True))
    
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
    op.create_index(op.f('idx_opportunities_score'), 'opportunities', ['score'], unique=False, postgresql_ops={'score': 'DESC'})
    
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


def downgrade() -> None:
    op.drop_table('analytics_cache')
    op.drop_index(op.f('idx_opportunities_score'), table_name='opportunities')
    op.drop_index('idx_opportunities_property', table_name='opportunities')
    op.drop_table('opportunities')
    op.drop_column('properties', 'precio_m2')
    op.drop_column('properties', 'banos')
    op.drop_column('properties', 'dormitorios')
    op.drop_column('properties', 'superficie_util')
