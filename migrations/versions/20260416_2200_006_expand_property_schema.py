"""Expand property schema for maximum data capture

Adds many new columns to `properties`, new `amenities` and `services` tables,
and extends `publishers` and `images` with richer fields.

Revision ID: 006_expand_property_schema
Revises: 005_fix_opportunity_property_id
Create Date: 2026-04-16 22:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision = '006_expand_property_schema'
down_revision = '005_fix_opportunity_property_id'
branch_labels = None
depends_on = None


# New columns on properties
PROPERTY_NEW_COLS = [
    # Surface extras
    ('superficie_terraza', sa.Numeric(), True),
    ('superficie_terreno', sa.Numeric(), True),
    # Counts
    ('medios_banos', sa.Integer(), True),
    ('ambientes', sa.Integer(), True),
    ('estacionamientos', sa.Integer(), True),
    ('bodegas', sa.Integer(), True),
    ('piso', sa.Integer(), True),
    ('pisos_edificio', sa.Integer(), True),
    # Pricing
    ('precio_anterior', sa.Numeric(), True),
    ('gastos_comunes', sa.Integer(), True),
    # Building / unit
    ('ano_construccion', sa.Integer(), True),
    ('antiguedad', sa.Integer(), True),
    ('orientacion', sa.String(length=50), True),
    ('vista', sa.String(length=100), True),
    ('condicion', sa.String(length=50), True),
    # Location
    ('barrio', sa.String(length=150), True),
    ('calle', sa.String(length=200), True),
    ('numero', sa.String(length=50), True),
    ('lat', sa.Numeric(10, 7), True),
    ('lng', sa.Numeric(10, 7), True),
    # Content
    ('descripcion_html', sa.Text(), True),
    # Listing metrics / state
    ('num_fotos', sa.Integer(), True),
    ('thumbnail_url', sa.Text(), True),
    ('visitas', sa.Integer(), True),
    ('estado_publicacion', sa.String(length=50), True),
    ('fecha_publicacion', sa.DateTime(), True),
    ('fecha_actualizacion', sa.DateTime(), True),
    # JSON blobs
    ('tags', JSONB, True),
    ('breadcrumbs', JSONB, True),
    ('raw_state', JSONB, True),
]

PUBLISHER_NEW_COLS = [
    ('logo_url', sa.Text(), True),
    ('perfil_url', sa.Text(), True),
    ('reputacion', sa.String(length=50), True),
    ('publicaciones_activas', sa.Integer(), True),
    ('antiguedad_portal', sa.String(length=50), True),
]

IMAGE_NEW_COLS = [
    ('orden', sa.Integer(), True),
    ('alt', sa.Text(), True),
    ('resolucion', sa.String(length=20), True),
]


def _add_column_if_missing(table: str, column: sa.Column) -> None:
    """Add column only if it doesn't already exist (idempotent)."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing = {c['name'] for c in insp.get_columns(table)}
    if column.name not in existing:
        op.add_column(table, column)


def upgrade() -> None:
    # Expand properties
    for name, coltype, nullable in PROPERTY_NEW_COLS:
        _add_column_if_missing(
            'properties',
            sa.Column(name, coltype, nullable=nullable),
        )

    # Indices útiles
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing_idx = {i['name'] for i in insp.get_indexes('properties')}
    if 'ix_properties_barrio' not in existing_idx:
        op.create_index('ix_properties_barrio', 'properties', ['barrio'])
    if 'ix_properties_fecha_publicacion' not in existing_idx:
        op.create_index('ix_properties_fecha_publicacion', 'properties', ['fecha_publicacion'])
    if 'ix_properties_lat_lng' not in existing_idx:
        op.create_index('ix_properties_lat_lng', 'properties', ['lat', 'lng'])

    # Expand publishers
    for name, coltype, nullable in PUBLISHER_NEW_COLS:
        _add_column_if_missing(
            'publishers',
            sa.Column(name, coltype, nullable=nullable),
        )

    # Expand images
    for name, coltype, nullable in IMAGE_NEW_COLS:
        _add_column_if_missing(
            'images',
            sa.Column(name, coltype, nullable=nullable),
        )

    # New table: amenities
    if not insp.has_table('amenities'):
        op.create_table(
            'amenities',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('property_id', sa.Integer(), nullable=False),
            sa.Column('nombre', sa.String(length=200), nullable=False),
            sa.Column('categoria', sa.String(length=100), nullable=True),
            sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_amenities_property_id', 'amenities', ['property_id'])
        op.create_index('ix_amenities_property_nombre', 'amenities', ['property_id', 'nombre'])

    # New table: services
    insp = sa.inspect(bind)  # refresh
    if not insp.has_table('services'):
        op.create_table(
            'services',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('property_id', sa.Integer(), nullable=False),
            sa.Column('nombre', sa.String(length=200), nullable=False),
            sa.Column('incluido', sa.Boolean(), nullable=True),
            sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_services_property_id', 'services', ['property_id'])


def downgrade() -> None:
    # Drop new tables
    op.drop_index('ix_services_property_id', table_name='services')
    op.drop_table('services')
    op.drop_index('ix_amenities_property_nombre', table_name='amenities')
    op.drop_index('ix_amenities_property_id', table_name='amenities')
    op.drop_table('amenities')

    # Images
    for name, _, _ in IMAGE_NEW_COLS:
        op.drop_column('images', name)

    # Publishers
    for name, _, _ in PUBLISHER_NEW_COLS:
        op.drop_column('publishers', name)

    # Properties indices
    op.drop_index('ix_properties_lat_lng', table_name='properties')
    op.drop_index('ix_properties_fecha_publicacion', table_name='properties')
    op.drop_index('ix_properties_barrio', table_name='properties')

    # Properties columns
    for name, _, _ in PROPERTY_NEW_COLS:
        op.drop_column('properties', name)
