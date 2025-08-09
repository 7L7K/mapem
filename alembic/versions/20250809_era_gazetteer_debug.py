"""add gazetteer_entries and geocode_attempts

Revision ID: era_gazetteer_debug
Revises: fbd8f01be3a5
Create Date: 2025-08-09
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'era_gazetteer_debug'
down_revision = 'fbd8f01be3a5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'gazetteer_entries',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('name_norm', sa.String(), nullable=False),
        sa.Column('admin_norm', sa.String(), nullable=True),
        sa.Column('era_bucket', sa.String(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('source_id', sa.String(), nullable=True),
        sa.Column('country_code', sa.String(), nullable=True),
        sa.Column('admin1', sa.String(), nullable=True),
        sa.Column('admin2', sa.String(), nullable=True),
        sa.Column('alt_names', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('meta', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_gazetteer_name_admin_era', 'gazetteer_entries', ['name_norm', 'admin_norm', 'era_bucket'])

    op.create_table(
        'geocode_attempts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('raw_place', sa.String(), nullable=False),
        sa.Column('name_norm', sa.String(), nullable=True),
        sa.Column('admin_norm', sa.String(), nullable=True),
        sa.Column('era_bucket', sa.String(), nullable=True),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('chosen', sa.String(), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('request_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('response_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('debug_scoring_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_geocode_attempts_raw_created', 'geocode_attempts', ['raw_place', 'created_at'])


def downgrade() -> None:
    op.drop_index('ix_geocode_attempts_raw_created', table_name='geocode_attempts')
    op.drop_table('geocode_attempts')
    op.drop_index('ix_gazetteer_name_admin_era', table_name='gazetteer_entries')
    op.drop_table('gazetteer_entries')


