"""Add scraper executions and logs tables

Revision ID: 004_add_scraper_executions
Revises: 003_add_opportunities
Create Date: 2026-04-12 19:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_add_scraper_executions'
down_revision = '003_add_opportunities'
branch_labels = None
depends_on = None


def upgrade():
    # Create scraper_executions table
    op.create_table(
        'scraper_executions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('execution_id', sa.String(length=36), nullable=False),
        sa.Column('operacion', sa.String(length=50), nullable=False),
        sa.Column('tipo', sa.String(length=50), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('duration', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('properties_scraped', sa.Integer(), nullable=True, default=0),
        sa.Column('properties_new', sa.Integer(), nullable=True, default=0),
        sa.Column('properties_updated', sa.Integer(), nullable=True, default=0),
        sa.Column('pages_processed', sa.Integer(), nullable=True, default=0),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('parameters', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('triggered_by', sa.String(length=50), nullable=True),
        sa.Column('user_id', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for scraper_executions
    op.create_index('ix_scraper_executions_execution_id', 'scraper_executions', ['execution_id'], unique=True)
    op.create_index('ix_scraper_executions_operacion', 'scraper_executions', ['operacion'])
    op.create_index('ix_scraper_executions_tipo', 'scraper_executions', ['tipo'])
    op.create_index('ix_scraper_executions_start_time', 'scraper_executions', ['start_time'])
    op.create_index('ix_scraper_executions_status', 'scraper_executions', ['status'])
    
    # Create scraper_logs table
    op.create_table(
        'scraper_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('execution_id', sa.String(length=36), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('level', sa.String(length=20), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('log_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['execution_id'], ['scraper_executions.execution_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for scraper_logs
    op.create_index('ix_scraper_logs_execution_id', 'scraper_logs', ['execution_id'])
    op.create_index('ix_scraper_logs_timestamp', 'scraper_logs', ['timestamp'])
    op.create_index('ix_scraper_logs_level', 'scraper_logs', ['level'])


def downgrade():
    # Drop indexes first
    op.drop_index('ix_scraper_logs_level', table_name='scraper_logs')
    op.drop_index('ix_scraper_logs_timestamp', table_name='scraper_logs')
    op.drop_index('ix_scraper_logs_execution_id', table_name='scraper_logs')
    
    op.drop_index('ix_scraper_executions_status', table_name='scraper_executions')
    op.drop_index('ix_scraper_executions_start_time', table_name='scraper_executions')
    op.drop_index('ix_scraper_executions_tipo', table_name='scraper_executions')
    op.drop_index('ix_scraper_executions_operacion', table_name='scraper_executions')
    op.drop_index('ix_scraper_executions_execution_id', table_name='scraper_executions')
    
    # Drop tables
    op.drop_table('scraper_logs')
    op.drop_table('scraper_executions')
