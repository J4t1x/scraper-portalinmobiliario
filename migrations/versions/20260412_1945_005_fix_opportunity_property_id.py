"""Fix opportunity property_id type

Revision ID: 005_fix_opportunity_property_id
Revises: 004_add_scraper_executions
Create Date: 2026-04-12 19:45:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '005_fix_opportunity_property_id'
down_revision = '004_add_scraper_executions'
branch_labels = None
depends_on = None


def upgrade():
    # Drop existing foreign key constraint
    op.drop_constraint('opportunities_property_id_fkey', 'opportunities', type_='foreignkey')
    
    # Change column type from VARCHAR to INTEGER
    op.alter_column('opportunities', 'property_id',
                    existing_type=sa.String(length=255),
                    type_=sa.Integer(),
                    existing_nullable=False,
                    postgresql_using='property_id::integer')
    
    # Recreate foreign key constraint
    op.create_foreign_key(
        'opportunities_property_id_fkey',
        'opportunities', 'properties',
        ['property_id'], ['id']
    )


def downgrade():
    # Drop foreign key constraint
    op.drop_constraint('opportunities_property_id_fkey', 'opportunities', type_='foreignkey')
    
    # Change column type back to VARCHAR
    op.alter_column('opportunities', 'property_id',
                    existing_type=sa.Integer(),
                    type_=sa.String(length=255),
                    existing_nullable=False)
    
    # Recreate old foreign key constraint (pointing to non-existent column)
    op.create_foreign_key(
        'opportunities_property_id_fkey',
        'opportunities', 'properties',
        ['property_id'], ['property_id']
    )
