"""Initial schema for property scraper

Revision ID: 001
Revises: 
Create Date: 2026-04-09 01:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create properties table
    op.create_table(
        'properties',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('portal_id', sa.String(length=100), nullable=True),
        sa.Column('titulo', sa.String(length=500), nullable=True),
        sa.Column('precio', sa.Integer(), nullable=True),
        sa.Column('precio_moneda', sa.String(length=10), nullable=True),
        sa.Column('precio_original', sa.String(length=100), nullable=True),
        sa.Column('operacion', sa.String(length=50), nullable=True),
        sa.Column('tipo', sa.String(length=50), nullable=True),
        sa.Column('comuna', sa.String(length=100), nullable=True),
        sa.Column('region', sa.String(length=100), nullable=True),
        sa.Column('direccion', sa.String(length=500), nullable=True),
        sa.Column('headline', sa.String(length=500), nullable=True),
        sa.Column('atributos', sa.String(length=1000), nullable=True),
        sa.Column('descripcion', sa.String(length=5000), nullable=True),
        sa.Column('publicado_en', sa.DateTime(), nullable=True),
        sa.Column('scrapeado_en', sa.DateTime(), nullable=False),
        sa.Column('actualizado_en', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('url'),
        sa.Index('ix_properties_portal_id', 'portal_id'),
        sa.Index('ix_properties_operacion', 'operacion'),
        sa.Index('ix_properties_tipo', 'tipo'),
        sa.Index('ix_properties_comuna', 'comuna'),
        sa.Index('ix_properties_url', 'url')
    )
    
    # Create features table
    op.create_table(
        'features',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('property_id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_features_property_id', 'property_id')
    )
    
    # Create images table
    op.create_table(
        'images',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('property_id', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('es_principal', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_images_property_id', 'property_id')
    )
    
    # Create publishers table
    op.create_table(
        'publishers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('property_id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=200), nullable=True),
        sa.Column('telefono', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=200), nullable=True),
        sa.Column('tipo', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('property_id'),
        sa.Index('ix_publishers_property_id', 'property_id')
    )


def downgrade() -> None:
    op.drop_table('publishers')
    op.drop_table('images')
    op.drop_table('features')
    op.drop_table('properties')
