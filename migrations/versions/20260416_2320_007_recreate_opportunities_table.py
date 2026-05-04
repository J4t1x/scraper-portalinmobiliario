"""Recreate opportunities table with correct schema

Revision ID: 007_recreate_opportunities
Revises: 006_expand_property_schema
Create Date: 2026-04-16 23:20:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007_recreate_opportunities'
down_revision = '006_expand_property_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop old opportunities table
    op.drop_table('opportunities')
    
    # Recreate opportunities table with correct schema
    op.create_table(
        'opportunities',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('property_id', sa.Integer(), nullable=False),
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


def downgrade() -> None:
    # Drop new opportunities table
    op.drop_index(op.f('idx_opportunities_score'), table_name='opportunities')
    op.drop_index('idx_opportunities_property', table_name='opportunities')
    op.drop_table('opportunities')
    
    # Recreate old opportunities table (if needed)
    op.create_table(
        'opportunities',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('property_id', sa.String(length=255), nullable=True),
        sa.Column('score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('detected_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('idx_opportunities_score'), 'opportunities', ['score'], unique=False, postgresql_ops={'score': 'DESC'})
